from django.test import TestCase, Client
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
