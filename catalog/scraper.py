"""
Luckjary Atelier - E-Commerce Product Scraper Engine
Extracts product titles, descriptions, pricing, SKUs, variants, and high-res images
from Shopify stores, WooCommerce, Schema.org JSON-LD, OpenGraph metadata, and custom HTML.
"""

import json
import re
import urllib.parse
from html.parser import HTMLParser
import requests

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
}

class FastMetaHTMLParser(HTMLParser):
    """
    Lightweight HTML parser to extract:
    - <title> and <h1>
    - <meta> tags (og:*, twitter:*, product:*, description)
    - <script type="application/ld+json"> blocks
    - <img> tags with src, data-src, srcset
    """
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.in_h1 = False
        self.h1 = ""
        self.meta_tags = {}
        self.json_ld_scripts = []
        self.in_json_ld = False
        self.current_json_ld = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}

        if tag == 'title' and not self.title:
            self.in_title = True
        elif tag == 'h1' and not self.h1:
            self.in_h1 = True
        elif tag == 'meta':
            # Property or name
            prop = attr_dict.get('property', '').lower() or attr_dict.get('name', '').lower()
            content = attr_dict.get('content', '')
            if prop and content:
                # Save multiple or single
                if prop not in self.meta_tags:
                    self.meta_tags[prop] = content
                elif isinstance(self.meta_tags[prop], list):
                    self.meta_tags[prop].append(content)
                else:
                    self.meta_tags[prop] = [self.meta_tags[prop], content]
        elif tag == 'script':
            script_type = attr_dict.get('type', '').lower().strip()
            if script_type == 'application/ld+json':
                self.in_json_ld = True
                self.current_json_ld = []
        elif tag == 'img':
            src = attr_dict.get('data-zoom-image') or attr_dict.get('data-highres') or attr_dict.get('data-large-image') or attr_dict.get('data-src') or attr_dict.get('src')
            srcset = attr_dict.get('srcset')
            alt = attr_dict.get('alt', '')
            if srcset:
                # Pick largest image from srcset
                candidates = [s.strip().split() for s in srcset.split(',') if s.strip()]
                if candidates:
                    src = candidates[-1][0]
            if src and not src.startswith('data:') and not src.endswith('.svg') and not src.endswith('.gif'):
                self.images.append({'src': src, 'alt': alt})

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag == 'h1':
            self.in_h1 = False
        elif tag == 'script' and self.in_json_ld:
            self.in_json_ld = False
            raw = "".join(self.current_json_ld).strip()
            if raw:
                self.json_ld_scripts.append(raw)

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_h1:
            self.h1 += data
        elif self.in_json_ld:
            self.current_json_ld.append(data)


def clean_price(val):
    """Parses numeric price from various string formats (e.g. '$1,299.00', '₹ 95,000')"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    match = re.search(r'[\d,]+(?:\.\d+)?', val_str)
    if match:
        num_str = match.group(0).replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            return None
    return None


def clean_html_text(html_text):
    """Strips HTML tags and normalizes whitespace."""
    if not html_text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def absolute_url(base_url, link):
    """Resolves relative URLs against base URL."""
    if not link:
        return ""
    if link.startswith('//'):
        return 'https:' + link
    if link.startswith(('http://', 'https://')):
        return link
    if base_url:
        return urllib.parse.urljoin(base_url, link)
    return link


def try_shopify_json_endpoint(product_url):
    """
    Attempts to fetch directly from Shopify's standard public product JSON API.
    e.g. https://store.com/products/ring-name -> https://store.com/products/ring-name.json
    """
    try:
        parsed = urllib.parse.urlparse(product_url)
        path = parsed.path
        if '/products/' in path:
            json_path = re.sub(r'(\.json)?$', '.json', path)
            shopify_json_url = urllib.parse.urlunparse((
                parsed.scheme or 'https',
                parsed.netloc,
                json_path,
                '', '', ''
            ))
            resp = requests.get(shopify_json_url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if 'product' in data:
                    prod = data['product']
                    return parse_shopify_product_dict(prod, product_url)
    except Exception:
        pass
    return None


def parse_shopify_product_dict(prod, source_url):
    """Formats Shopify JSON dictionary into standardized Luckjary scraper output."""
    title = prod.get('title', '')
    body_html = prod.get('body_html', '') or ''
    description = clean_html_text(body_html)
    vendor = prod.get('vendor', '')
    product_type = prod.get('product_type', '')
    tags = prod.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    # Variants
    variants = []
    min_price = None
    compare_at_price = None

    for v in prod.get('variants', []):
        v_price = clean_price(v.get('price'))
        v_comp = clean_price(v.get('compare_at_price'))
        v_sku = v.get('sku') or ''
        v_title = v.get('title') or ''
        v_avail = v.get('available', True)

        if min_price is None or (v_price is not None and v_price < min_price):
            min_price = v_price
        if compare_at_price is None and v_comp:
            compare_at_price = v_comp

        variants.append({
            'title': v_title,
            'sku': v_sku,
            'price': v_price,
            'compare_at_price': v_comp,
            'available': v_avail,
            'option1': v.get('option1'),
            'option2': v.get('option2'),
            'option3': v.get('option3'),
        })

    # Images
    images = []
    for img in prod.get('images', []):
        src = img.get('src') or ''
        if src:
            images.append({
                'src': absolute_url(source_url, src),
                'alt': img.get('alt') or title,
                'width': img.get('width'),
                'height': img.get('height')
            })

    # Options (e.g. Size, Color, Metal)
    options = []
    for opt in prod.get('options', []):
        options.append({
            'name': opt.get('name', ''),
            'values': opt.get('values', [])
        })

    # Determine primary SKU
    first_sku = variants[0]['sku'] if variants and variants[0]['sku'] else ''
    if not first_sku:
        slug_part = prod.get('handle') or re.sub(r'[^A-Za-z0-9]', '', title)[:8].upper()
        first_sku = f"LCK-SCR-{slug_part.upper()[:12]}"

    return {
        'source_type': 'Shopify Product API',
        'source_url': source_url,
        'title': title,
        'subtitle': f"Curated from {vendor}" if vendor else "Haute Atelier Import",
        'description': description or f"Exquisite handcrafted {title} featuring master gemstone setting and premium fine finishes.",
        'sku': first_sku,
        'price': min_price or 0.0,
        'compare_at_price': compare_at_price,
        'currency': 'USD',
        'brand': vendor,
        'product_type': product_type,
        'tags': tags,
        'options': options,
        'variants': variants,
        'images': images,
        'available': any(v.get('available') for v in variants) if variants else True,
        'success': True,
    }


def parse_json_ld_scripts(scripts_list, source_url):
    """Finds Schema.org Product objects in JSON-LD script blocks."""
    product_obj = None

    for raw in scripts_list:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') in ('Product', 'IndividualProduct'):
                        product_obj = item
                        break
            elif isinstance(data, dict):
                if data.get('@type') in ('Product', 'IndividualProduct'):
                    product_obj = data
                    break
                elif '@graph' in data and isinstance(data['@graph'], list):
                    for item in data['@graph']:
                        if isinstance(item, dict) and item.get('@type') in ('Product', 'IndividualProduct'):
                            product_obj = item
                            break
            if product_obj:
                break
        except Exception:
            continue

    if not product_obj:
        return None

    title = product_obj.get('name') or product_obj.get('headline') or ''
    description = clean_html_text(product_obj.get('description') or '')
    sku = product_obj.get('sku') or product_obj.get('mpn') or product_obj.get('gtin13') or product_obj.get('gtin14') or ''
    brand_val = product_obj.get('brand')
    brand = brand_val.get('name') if isinstance(brand_val, dict) else (brand_val if isinstance(brand_val, str) else '')

    # Images
    images = []
    raw_images = product_obj.get('image', [])
    if isinstance(raw_images, str):
        raw_images = [raw_images]
    elif isinstance(raw_images, dict):
        raw_images = [raw_images.get('url') or raw_images.get('contentUrl') or '']

    for img in raw_images:
        img_url = ""
        alt = title
        if isinstance(img, str):
            img_url = img
        elif isinstance(img, dict):
            img_url = img.get('url') or img.get('contentUrl') or ''
            alt = img.get('caption') or alt
        if img_url:
            images.append({
                'src': absolute_url(source_url, img_url),
                'alt': alt
            })

    # Offers and variants
    offers = product_obj.get('offers', [])
    if isinstance(offers, dict):
        offers = [offers]

    variants = []
    min_price = None
    currency = 'USD'
    compare_at_price = None

    for off in offers:
        p = clean_price(off.get('price'))
        c = off.get('priceCurrency') or currency
        curr_sku = off.get('sku') or sku
        avail = 'InStock' in str(off.get('availability', ''))
        v_name = off.get('name') or (f"Variant {len(variants) + 1}" if len(offers) > 1 else 'Standard')

        if p is not None:
            if min_price is None or p < min_price:
                min_price = p
                currency = c

        variants.append({
            'title': v_name,
            'sku': curr_sku,
            'price': p,
            'compare_at_price': None,
            'available': avail,
            'option1': v_name,
        })

    # Fallback SKU
    if not sku:
        sku = variants[0]['sku'] if variants and variants[0]['sku'] else f"LCK-SCR-{re.sub(r'[^A-Za-z0-9]', '', title)[:8].upper()}"

    return {
        'source_type': 'Schema.org JSON-LD',
        'source_url': source_url,
        'title': title,
        'subtitle': f"Curated from {brand}" if brand else "Haute Joaillerie Import",
        'description': description or f"Handcrafted {title} with precision metalwork and luxury stones.",
        'sku': sku,
        'price': min_price or 0.0,
        'compare_at_price': compare_at_price,
        'currency': currency,
        'brand': brand,
        'variants': variants,
        'images': images,
        'available': any(v.get('available') for v in variants) if variants else True,
        'success': True,
    }


def parse_opengraph_fallback(meta_tags, images_found, title_found, source_url):
    """Extracts OpenGraph, Twitter, and microdata from page meta tags."""
    title = meta_tags.get('og:title') or meta_tags.get('twitter:title') or title_found or ""
    # Clean common title suffixes like " - Tiffany & Co." or " | Mejuri"
    title = re.sub(r'\s+[\|\-–—]\s+.*$', '', title).strip()

    description = meta_tags.get('og:description') or meta_tags.get('twitter:description') or meta_tags.get('description') or ""
    description = clean_html_text(description)

    brand = meta_tags.get('og:site_name') or meta_tags.get('product:brand') or ""
    price_val = meta_tags.get('product:price:amount') or meta_tags.get('og:price:amount')
    currency = meta_tags.get('product:price:currency') or meta_tags.get('og:price:currency') or 'USD'
    price = clean_price(price_val)

    # Images from meta
    images = []
    og_images = meta_tags.get('og:image')
    if og_images:
        if isinstance(og_images, str):
            og_images = [og_images]
        for im in og_images:
            images.append({'src': absolute_url(source_url, im), 'alt': title})

    tw_image = meta_tags.get('twitter:image')
    if tw_image and isinstance(tw_image, str):
        tw_url = absolute_url(source_url, tw_image)
        if not any(i['src'] == tw_url for i in images):
            images.append({'src': tw_url, 'alt': title})

    # Additional images from parser if less than 6
    for im in images_found:
        im_url = absolute_url(source_url, im['src'])
        if not any(i['src'] == im_url for i in images) and len(images) < 12:
            images.append({'src': im_url, 'alt': im.get('alt') or title})

    sku_gen = f"LCK-SCR-{re.sub(r'[^A-Za-z0-9]', '', title)[:8].upper()}"

    variants = [{
        'title': 'Standard Luxury Specification',
        'sku': sku_gen,
        'price': price,
        'compare_at_price': None,
        'available': True,
        'option1': '925 Sterling Silver',
    }]

    return {
        'source_type': 'OpenGraph & Meta Tags',
        'source_url': source_url,
        'title': title,
        'subtitle': f"Curated from {brand}" if brand else "Atelier Import",
        'description': description or f"Fine handcrafted {title} finished with signature Luckjary hallmark.",
        'sku': sku_gen,
        'price': price or 0.0,
        'compare_at_price': None,
        'currency': currency,
        'brand': brand,
        'variants': variants,
        'images': images,
        'available': True,
        'success': bool(title),
    }


def scrape_ecommerce_product(url=None, raw_html=None, raw_json=None):
    """
    Main entry point for scraping an e-commerce product.
    Accepts:
    - url: Live website product URL
    - raw_html: User-pasted HTML source
    - raw_json: User-pasted JSON (e.g. Shopify .json format or Schema.org)
    """
    url = (url or '').strip()

    # 1. If raw JSON is provided directly
    if raw_json and raw_json.strip():
        try:
            data = json.loads(raw_json)
            if 'product' in data:
                return parse_shopify_product_dict(data['product'], url or 'pasted-shopify.json')
            if isinstance(data, dict) and data.get('@type') in ('Product', 'IndividualProduct'):
                return parse_json_ld_scripts([raw_json], url or 'pasted-schema.json')
        except Exception as e:
            return {'success': False, 'error': f"Failed to parse pasted JSON: {str(e)}"}

    # 2. If URL is provided, try direct Shopify JSON endpoint first if applicable
    if url and not raw_html:
        shopify_res = try_shopify_json_endpoint(url)
        if shopify_res and shopify_res.get('title'):
            return shopify_res

    # 3. Fetch HTML if URL provided, or use raw_html
    html = raw_html or ""
    if url and not html:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            html = resp.text
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network connection failed: {str(e)}. Try pasting the raw HTML in the Advanced tab if the store blocks automated web scrapers."
            }

    if not html.strip():
        return {'success': False, 'error': 'No HTML or URL provided for scraping.'}

    # 4. Parse HTML using FastMetaHTMLParser
    parser = FastMetaHTMLParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    # 5. Check JSON-LD in HTML
    if parser.json_ld_scripts:
        json_ld_res = parse_json_ld_scripts(parser.json_ld_scripts, url)
        if json_ld_res and json_ld_res.get('title'):
            # If JSON-LD didn't catch images, complement with parser images
            if not json_ld_res.get('images') and parser.images:
                json_ld_res['images'] = [
                    {'src': absolute_url(url, im['src']), 'alt': json_ld_res['title']}
                    for im in parser.images[:10]
                ]
            return json_ld_res

    # 6. Check OpenGraph / Meta tags
    og_res = parse_opengraph_fallback(
        parser.meta_tags,
        parser.images,
        parser.h1 or parser.title,
        url
    )
    if og_res and og_res.get('title'):
        return og_res

    # 7. Fallback basic extraction if page title was found
    if parser.title or parser.h1:
        clean_name = clean_html_text(parser.h1 or parser.title)
        clean_name = re.sub(r'\s+[\|\-–—]\s+.*$', '', clean_name).strip()
        sku_cand = f"LCK-SCR-{re.sub(r'[^A-Za-z0-9]', '', clean_name)[:8].upper()}"
        return {
            'source_type': 'Standard HTML Parser',
            'source_url': url,
            'title': clean_name,
            'subtitle': 'Atelier Curated Piece',
            'description': f"Handcrafted {clean_name} fashioned in premium 925 Solid Sterling Silver with luxury finish.",
            'sku': sku_cand,
            'price': 149.0,
            'compare_at_price': 199.0,
            'currency': 'USD',
            'brand': 'Curated',
            'variants': [{
                'title': 'Default Size & Specification',
                'sku': sku_cand,
                'price': 149.0,
                'available': True,
                'option1': '925 Sterling Silver',
            }],
            'images': [{'src': absolute_url(url, im['src']), 'alt': clean_name} for im in parser.images[:8]],
            'available': True,
            'success': True,
        }

    return {
        'success': False,
        'error': 'Could not automatically detect product information. Please verify the URL or paste the product page HTML directly.'
    }
