"""
Luckjary Atelier - E-Commerce Product & Collection Scraper Engine
Extracts product titles, descriptions, pricing, SKUs, variants, and high-res images
from Shopify stores, collections, WooCommerce, Schema.org JSON-LD, OpenGraph metadata, and custom HTML.
Zero mandatory external dependencies - uses standard library urllib with requests fallback.
"""

import json
import re
import urllib.parse
from html.parser import HTMLParser

# Safe import of requests (optional enhancement; standard library works independently)
try:
    import requests
except ImportError:
    requests = None

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
}


def http_get(url, timeout=12):
    """
    Robust HTTP GET with automatic fallback to Python standard library urllib.
    Ensures zero dependency crashes on Vercel / Serverless environments.
    """
    if requests is not None:
        try:
            session = requests.Session()
            resp = session.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                resp.encoding = resp.apparent_encoding or 'utf-8'
                return resp.text, 200
            elif resp.status_code in (403, 404, 429):
                # Try urllib fallback before giving up
                pass
        except Exception:
            pass

    # Standard library fallback (zero external dependencies)
    import urllib.request
    import ssl
    import gzip
    import io

    req = urllib.request.Request(url, headers=HEADERS)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            code = r.status
            raw = r.read()
            if r.headers.get('Content-Encoding') == 'gzip':
                try:
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                except Exception:
                    pass
            charset = r.headers.get_content_charset() or 'utf-8'
            try:
                text = raw.decode(charset)
            except Exception:
                text = raw.decode('utf-8', errors='ignore')
            return text, code
    except Exception as e:
        return "", getattr(e, 'code', 500)


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
            prop = attr_dict.get('property', '').lower() or attr_dict.get('name', '').lower()
            content = attr_dict.get('content', '')
            if prop and content:
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


def try_shopify_endpoints(target_url):
    """
    Detects and extracts from Shopify store endpoints:
    1. Product URLs (/products/{handle}) -> {domain}/products/{handle}.json
    2. Collection URLs (/collections/{handle}) -> {domain}/collections/{handle}/products.json
    """
    try:
        parsed = urllib.parse.urlparse(target_url)
        netloc = parsed.netloc
        scheme = parsed.scheme or 'https'
        path = parsed.path

        # Case 1: Collection URL (e.g. /collections/samsung-repair)
        col_match = re.search(r'/collections/([^/?#]+)', path)
        if col_match:
            col_handle = col_match.group(1)
            all_products = []
            page = 1
            while page <= 4:
                col_json_url = f"{scheme}://{netloc}/collections/{col_handle}/products.json?limit=250&page={page}"
                body, code = http_get(col_json_url)
                if code == 200 and body:
                    data = json.loads(body)
                    prods = data.get('products', [])
                    if not prods:
                        break
                    all_products.extend(prods)
                    if len(prods) < 250:
                        break
                    page += 1
                else:
                    break
            if all_products:
                return parse_shopify_collection(all_products, col_handle, target_url, netloc)

        # Case 2: Product URL (e.g. /products/ring-name)
        prod_match = re.search(r'/products/([^/?#]+)', path)
        if prod_match:
            prod_handle = prod_match.group(1).replace('.json', '')
            prod_json_url = f"{scheme}://{netloc}/products/{prod_handle}.json"
            body, code = http_get(prod_json_url)
            if code == 200 and body:
                data = json.loads(body)
                if 'product' in data:
                    return parse_shopify_product_dict(data['product'], target_url)

        # Case 3: Direct JSON URL
        if path.endswith('.json'):
            body, code = http_get(target_url)
            if code == 200 and body:
                data = json.loads(body)
                if 'product' in data:
                    return parse_shopify_product_dict(data['product'], target_url)
                elif 'products' in data and data['products']:
                    return parse_shopify_collection(data['products'], 'collection', target_url, netloc)

        # Case 4: Shopify Admin URL (e.g. admin.shopify.com/store/repairindi/... or repairindi.myshopify.com/admin/...)
        admin_match = re.search(r'admin\.shopify\.com/store/([^/?#]+)', target_url) or re.search(r'([^/?#]+)\.myshopify\.com/admin', target_url)
        if admin_match:
            store_handle = admin_match.group(1)
            # Attempt to resolve via public myshopify endpoint
            public_candidates = [
                f"https://{store_handle}.myshopify.com/collections/all/products.json?limit=250",
                f"https://{store_handle}.myshopify.com/products.json?limit=250",
            ]
            for cand_url in public_candidates:
                body, code = http_get(cand_url)
                if code == 200 and body:
                    try:
                        data = json.loads(body)
                        prods = data.get('products', [])
                        if prods:
                            return parse_shopify_collection(prods, 'all', target_url, f"{store_handle}.myshopify.com")
                    except Exception:
                        pass
            
            # If public endpoint could not be reached, return an explicit helpful error
            return {
                'success': False,
                'error': f"The URL entered is a private Shopify Admin URL ('admin.shopify.com/store/{store_handle}'). External scrapers cannot access password-protected merchant dashboards. Please use the public storefront URL (e.g. https://{store_handle}.myshopify.com/products or your public storefront domain), or click 'Advanced: Paste HTML / JSON Source'."
            }
    except Exception:
        pass
    return None


def parse_shopify_collection(products_list, col_handle, source_url, domain):
    """
    Parses a Shopify collection into:
    - Complete list of all collection products with variants, SKUs, and images
    - Primary product for studio view
    - Aggregate metrics (total items, total variants)
    """
    formatted_products = []
    total_variants_count = 0
    for p in products_list:
        parsed = parse_shopify_product_dict(p, f"https://{domain}/products/{p.get('handle', '')}")
        formatted_products.append(parsed)
        total_variants_count += len(parsed.get('variants', []))

    primary = dict(formatted_products[0]) if formatted_products else {}
    col_name = col_handle.replace('-', ' ').title()

    primary['is_collection'] = True
    primary['collection_title'] = col_name
    primary['collection_handle'] = col_handle
    primary['collection_total'] = len(formatted_products)
    primary['total_variants_count'] = total_variants_count
    primary['collection_products'] = formatted_products
    primary['source_type'] = f"Shopify Collection ({len(formatted_products)} items, {total_variants_count} variants)"
    return primary


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
    max_price = None
    compare_at_price = None

    slug_part = prod.get('handle') or re.sub(r'[^A-Za-z0-9]', '', title)[:8].upper()
    atelier_sku = f"LCK-SCR-{slug_part.upper().replace('_', '-')[:14]}"

    for i, v in enumerate(prod.get('variants', [])):
        v_price = clean_price(v.get('price'))
        v_comp = clean_price(v.get('compare_at_price'))
        # Extract raw Shopify variant SKU accurately (preserving model numbers, warehouse codes, slashes, etc.)
        v_sku = str(v.get('sku') or '').strip()
        v_title = v.get('title') or ''
        v_avail = v.get('available', True)

        if v_price is not None:
            if min_price is None or v_price < min_price:
                min_price = v_price
            if max_price is None or v_price > max_price:
                max_price = v_price

        if compare_at_price is None and v_comp:
            compare_at_price = v_comp

        variants.append({
            'title': v_title,
            'sku': v_sku if v_sku else f"{atelier_sku}-V{i+1}",
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

    # Options (e.g. Size, Color, Metal, Item)
    options = []
    for opt in prod.get('options', []):
        options.append({
            'name': opt.get('name', ''),
            'values': opt.get('values', [])
        })

    # Primary SKU: Use raw variant SKU from Shopify if available; otherwise use atelier SKU
    first_sku = ''
    for v in variants:
        if v.get('sku') and not v['sku'].startswith(atelier_sku):
            first_sku = v['sku']
            break
    if not first_sku and variants and variants[0].get('sku'):
        first_sku = variants[0]['sku']
    if not first_sku:
        first_sku = atelier_sku

    # Featured primary price: match the live store's featured variant price (e.g. Display)
    first_var_price = variants[0]['price'] if (variants and variants[0].get('price') is not None) else None
    primary_price = first_var_price if first_var_price is not None else (min_price or 0.0)

    is_inr = ('.in' in source_url or 'sparelelo' in source_url or 'india' in source_url)
    currency = 'INR' if is_inr else 'USD'

    return {
        'source_type': 'Shopify Product API',
        'source_url': source_url,
        'id': prod.get('id'),
        'handle': prod.get('handle'),
        'title': title,
        'subtitle': f"Curated from {vendor}" if vendor else "Haute Atelier Import",
        'description': description or f"Exquisite handcrafted {title} featuring master gemstone setting and premium fine finishes.",
        'sku': first_sku,
        'price': primary_price,
        'min_price': min_price if min_price is not None else primary_price,
        'max_price': max_price if max_price is not None else primary_price,
        'compare_at_price': compare_at_price,
        'currency': currency,
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
    max_price = None
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
            if max_price is None or p > max_price:
                max_price = p

        variants.append({
            'title': v_name,
            'sku': curr_sku or f"SKU-{len(variants)+1}",
            'price': p,
            'compare_at_price': None,
            'available': avail,
            'option1': v_name,
        })

    # Fallback SKU
    if not sku:
        sku = variants[0]['sku'] if variants and variants[0]['sku'] else f"LCK-SCR-{re.sub(r'[^A-Za-z0-9]', '', title)[:8].upper()}"

    first_var_price = variants[0]['price'] if (variants and variants[0].get('price') is not None) else None
    primary_price = first_var_price if first_var_price is not None else (min_price or 0.0)

    return {
        'source_type': 'Schema.org JSON-LD',
        'source_url': source_url,
        'title': title,
        'subtitle': f"Curated from {brand}" if brand else "Haute Joaillerie Import",
        'description': description or f"Handcrafted {title} with precision metalwork and luxury stones.",
        'sku': sku,
        'price': primary_price,
        'min_price': min_price if min_price is not None else primary_price,
        'max_price': max_price if max_price is not None else primary_price,
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

    # Additional images from parser if needed
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


def parse_shopify_csv(csv_text, source_name='Shopify Export CSV'):
    """
    Parses a standard Shopify Products export CSV into a full Luckjary collection
    with all products, options, high-resolution images, and EXACT raw SKUs.
    """
    import csv, io
    reader = csv.DictReader(io.StringIO(csv_text))
    products_map = {}
    ordered_handles = []

    for row in reader:
        handle = (row.get('Handle') or '').strip()
        if not handle:
            continue
        
        title = (row.get('Title') or '').strip()
        body_html = (row.get('Body (HTML)') or '').strip()
        vendor = (row.get('Vendor') or '').strip()
        img_src = (row.get('Image Src') or '').strip()
        v_sku = str(row.get('Variant SKU') or '').strip()
        v_price = clean_price(row.get('Variant Price'))
        v_comp = clean_price(row.get('Variant Compare At Price'))
        
        opt1_val = (row.get('Option1 Value') or '').strip()
        opt2_val = (row.get('Option2 Value') or '').strip()
        opt3_val = (row.get('Option3 Value') or '').strip()
        opt_parts = [p for p in (opt1_val, opt2_val, opt3_val) if p and p.lower() != 'default title']
        v_title = " / ".join(opt_parts) if opt_parts else (opt1_val or 'Default Option')

        if handle not in products_map:
            ordered_handles.append(handle)
            products_map[handle] = {
                'title': title or handle.replace('-', ' ').title(),
                'handle': handle,
                'vendor': vendor,
                'description': clean_html_text(body_html),
                'variants': [],
                'images': []
            }
        
        # If row has variant data
        if v_sku or v_price is not None or opt1_val:
            products_map[handle]['variants'].append({
                'title': v_title,
                'sku': v_sku,
                'price': v_price if v_price is not None else 0.0,
                'compare_at_price': v_comp,
                'available': True,
                'option1': opt1_val,
                'option2': opt2_val,
                'option3': opt3_val
            })
        
        # If row has image
        if img_src and not any(im['src'] == img_src for im in products_map[handle]['images']):
            products_map[handle]['images'].append({
                'src': img_src,
                'alt': row.get('Image Alt Text') or products_map[handle]['title']
            })

    if not products_map:
        return {'success': False, 'error': 'No products could be parsed from the provided CSV.'}

    # Convert to Shopify product dict format and use parse_shopify_collection
    raw_prods = []
    for h in ordered_handles:
        p = products_map[h]
        raw_prods.append({
            'title': p['title'],
            'handle': p['handle'],
            'body_html': p['description'],
            'vendor': p['vendor'],
            'variants': p['variants'] or [{'title': 'Default', 'sku': '', 'price': 0.0}],
            'images': p['images']
        })

    return parse_shopify_collection(raw_prods, 'shopify-csv-export', source_name, 'Shopify Admin Export')


def scrape_ecommerce_product(url=None, raw_html=None, raw_json=None, raw_csv=None):
    """
    Main entry point for scraping an e-commerce product or collection.
    Accepts:
    - url: Live website product/collection URL
    - raw_html: User-pasted HTML source
    - raw_json: User-pasted JSON (e.g. Shopify .json format or Schema.org)
    - raw_csv: User-pasted or uploaded Shopify products export CSV
    """
    url = (url or '').strip()

    # 0. Check for CSV input (explicit or embedded in raw_html/raw_json)
    candidate_text = raw_csv or raw_html or raw_json or ""
    if candidate_text and ('Variant SKU' in candidate_text or ('Handle,' in candidate_text and 'Title,' in candidate_text)):
        return parse_shopify_csv(candidate_text, url or 'Shopify Export CSV')

    # 1. If raw JSON is provided directly
    if raw_json and raw_json.strip():
        try:
            data = json.loads(raw_json)
            if 'product' in data:
                return parse_shopify_product_dict(data['product'], url or 'pasted-shopify.json')
            if 'products' in data and data['products']:
                return parse_shopify_collection(data['products'], 'pasted-collection', url or 'pasted-collection.json', 'pasted')
            if isinstance(data, dict) and data.get('@type') in ('Product', 'IndividualProduct'):
                return parse_json_ld_scripts([raw_json], url or 'pasted-schema.json')
        except Exception as e:
            return {'success': False, 'error': f"Failed to parse pasted JSON: {str(e)}"}

    # 2. If URL is provided, try direct Shopify endpoints (Product or Collection)
    if url and not raw_html:
        shopify_res = try_shopify_endpoints(url)
        if shopify_res:
            if shopify_res.get('title'):
                return shopify_res
            if not shopify_res.get('success', True) and shopify_res.get('error'):
                return shopify_res

    # 3. Fetch HTML if URL provided, or use raw_html
    html = raw_html or ""
    if url and not html:
        fetched_text, code = http_get(url)
        if code == 200 and fetched_text:
            html = fetched_text
        else:
            return {
                'success': False,
                'error': f"Target server returned HTTP {code}. The store may require manual copy-paste: open the page in your browser, right-click 'View Page Source' (Ctrl+U), copy the source, and paste it into the 'Advanced: Paste Source' tab."
            }

    if not html.strip():
        return {'success': False, 'error': 'No content could be retrieved from the provided URL.'}

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
