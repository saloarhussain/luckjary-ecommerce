import json
from unittest.mock import patch
from django.test import TestCase, SimpleTestCase, Client, RequestFactory
from django.urls import reverse
from .models import Category, Material, Collection, Product, ProductImage

class CatalogAndSEOTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Rings', slug='rings')
        self.material = Material.objects.create(name='18K Solid Yellow Gold', slug='18k-solid-yellow-gold')
        self.product = Product.objects.create(
            title='The Celestia Solitaire Diamond Ring',
            slug='the-celestia-solitaire-diamond-ring',
            sku='LCK-RNG-001',
            category=self.category,
            price=2450.00,
            compare_at_price=2850.00,
            inventory=15,
            karat_metal='18K Solid Yellow Gold',
            gemstone='1.80 ctw Oval Cut Lab Diamond',
            description='Handcrafted in New York.'
        )
        self.product.materials.add(self.material)
        ProductImage.objects.create(
            product=self.product,
            image_url='https://images.unsplash.com/photo-1605100804763-247f67b3557e',
            is_primary=True
        )

    def test_catalog_filtering_by_category_and_material(self):
        resp = self.client.get(reverse('catalog:product_list') + '?category=rings')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'The Celestia Solitaire Diamond Ring')

        resp_mat = self.client.get(reverse('catalog:product_list') + '?material=18k-solid-yellow-gold')
        self.assertEqual(resp_mat.status_code, 200)
        self.assertContains(resp_mat, 'The Celestia Solitaire Diamond Ring')

    def test_product_detail_page_and_json_ld_schema(self):
        url = reverse('catalog:product_detail', kwargs={'slug': self.product.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        # Test SEO semantic elements
        self.assertContains(resp, '<meta property="og:title"')
        self.assertContains(resp, 'application/ld+json')
        self.assertContains(resp, '"@type": "Product"')
        self.assertContains(resp, '"name": "The Celestia Solitaire Diamond Ring"')
        self.assertContains(resp, '"price": "2450.00"')

    def test_sitemap_and_robots_txt(self):
        sitemap_resp = self.client.get(reverse('core:sitemap_xml'))
        self.assertEqual(sitemap_resp.status_code, 200)
        self.assertEqual(sitemap_resp['Content-Type'], 'application/xml')
        self.assertContains(sitemap_resp, '<urlset')
        self.assertContains(sitemap_resp, self.product.get_absolute_url())

        robots_resp = self.client.get(reverse('core:robots_txt'))
        self.assertEqual(robots_resp.status_code, 200)
        self.assertContains(robots_resp, 'User-agent: *')
        self.assertContains(robots_resp, 'Disallow: /admin/')


def _make_shopify_products(start_id, count):
    return [
        {
            'id': start_id + i,
            'handle': f'piece-{start_id + i}',
            'title': f'Atelier Piece {start_id + i}',
            'vendor': 'Luckjary',
            'variants': [{'title': 'Default', 'sku': f'SKU-{start_id + i}', 'price': '100.00', 'available': True}],
            'images': [],
            'options': [],
        }
        for i in range(count)
    ]


class ScraperPaginationTests(SimpleTestCase):
    def test_paginated_collection_fetches_all_pages_via_page_param(self):
        from .scraper import scrape_ecommerce_product

        def fake_http_get(url, timeout=12):
            if 'page=1' in url:
                return json.dumps({'products': _make_shopify_products(1, 250)}), 200
            if 'page=2' in url:
                return json.dumps({'products': _make_shopify_products(251, 250)}), 200
            if 'page=3' in url:
                return json.dumps({'products': _make_shopify_products(501, 40)}), 200
            return json.dumps({'products': []}), 200

        with patch('catalog.scraper.http_get', side_effect=fake_http_get):
            p1 = scrape_ecommerce_product(url='https://example-store.com/collections/rings', page=1)
            self.assertTrue(p1['success'])
            self.assertTrue(p1['is_collection'])
            self.assertEqual(len(p1['collection_products']), 250)
            self.assertTrue(p1['has_more'])
            self.assertEqual(p1['next_page'], 2)

            p2 = scrape_ecommerce_product(url='https://example-store.com/collections/rings', page=2)
            self.assertTrue(p2['has_more'])
            self.assertEqual(p2['next_page'], 3)
            self.assertEqual(len(p2['collection_products']), 250)

            p3 = scrape_ecommerce_product(url='https://example-store.com/collections/rings', page=3)
            self.assertFalse(p3['has_more'])
            self.assertIsNone(p3['next_page'])
            self.assertEqual(len(p3['collection_products']), 40)

    def test_exact_250_multiple_stops_cleanly_on_empty_next_page(self):
        from .scraper import scrape_ecommerce_product

        def fake_http_get(url, timeout=12):
            if 'page=1' in url:
                return json.dumps({'products': _make_shopify_products(1, 250)}), 200
            if 'page=2' in url:
                return json.dumps({'products': []}), 200
            return '<html><title>Fallback</title></html>', 200

        with patch('catalog.scraper.http_get', side_effect=fake_http_get):
            p1 = scrape_ecommerce_product(url='https://example-store.com/products.json?limit=250', page=1)
            self.assertTrue(p1['has_more'])
            self.assertEqual(len(p1['collection_products']), 250)

            p2 = scrape_ecommerce_product(url='https://example-store.com/products.json?limit=250', page=2)
            self.assertTrue(p2['success'])
            self.assertTrue(p2['is_collection'])
            self.assertEqual(len(p2['collection_products']), 0)
            self.assertFalse(p2['has_more'])

    def test_unpaged_call_fetches_beyond_1000_products(self):
        from .scraper import scrape_ecommerce_product

        def fake_http_get(url, timeout=12):
            for pg in range(1, 7):
                if f'page={pg}' in url:
                    cnt = 250 if pg < 6 else 50
                    return json.dumps({'products': _make_shopify_products((pg - 1) * 250 + 1, cnt)}), 200
            return json.dumps({'products': []}), 200

        with patch('catalog.scraper.http_get', side_effect=fake_http_get):
            res = scrape_ecommerce_product(url='https://example-store.com/')
            self.assertTrue(res['success'])
            self.assertTrue(res['is_collection'])
            self.assertEqual(len(res['collection_products']), 1300)
            self.assertFalse(res['has_more'])

    def test_api_scrape_view_passes_page_param(self):
        from django.contrib.admin import site
        from catalog.models import Product
        from catalog.admin import ProductAdmin

        prod_admin = ProductAdmin(Product, site)
        rf = RequestFactory()
        req = rf.post(
            '/admin/catalog/product/api/scrape/',
            data=json.dumps({'url': 'https://example-store.com/products', 'page': 2}),
            content_type='application/json',
        )

        def fake_http_get(url, timeout=12):
            if 'products.json' in url and 'page=2' in url:
                return json.dumps({'products': _make_shopify_products(251, 15)}), 200
            return '', 404

        with patch('catalog.scraper.http_get', side_effect=fake_http_get), \
             patch('catalog.admin.Category.objects') as mock_cat_mgr:
            mock_cat_mgr.filter.return_value.first.return_value = None
            mock_cat_mgr.exists.return_value = False
            resp = prod_admin.api_scrape_view(req)
            self.assertEqual(resp.status_code, 200, resp.content.decode('utf-8'))
            payload = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(payload['status'], 'ok')
            self.assertTrue(payload['product']['is_collection'])
            self.assertEqual(len(payload['product']['collection_products']), 15)
            self.assertFalse(payload['product']['has_more'])
            self.assertEqual(payload['product']['page'], 2)

    def test_admin_context_and_zero_counts_render_zero_not_hardcoded_defaults(self):
        from django.template import Context, Template
        from catalog.context_processors import catalog_context

        rf = RequestFactory()
        req = rf.get('/admin/catalog/product/')
        with patch('catalog.models.Product.objects.count', return_value=0), \
             patch('orders.models.Order.objects.count', return_value=0):
            ctx = catalog_context(req)

        self.assertEqual(ctx['total_products'], 0)
        self.assertEqual(ctx['total_orders'], 0)

        rendered = Template('{{ total_products|default_if_none:0 }}|{{ total_orders|default_if_none:0 }}').render(Context(ctx))
        self.assertEqual(rendered, '0|0')
