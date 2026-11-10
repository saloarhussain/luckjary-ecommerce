from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Category, Product
from accounts.models import CustomUser
from .models import Order, OrderItem, Coupon, OrderStatusUpdate

class OrderManagementSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Necklaces', slug='necklaces')
        self.product = Product.objects.create(
            title='Lumière Teardrop Diamond Solitaire Pendant',
            slug='lumiere-teardrop-diamond-solitaire-pendant',
            sku='LCK-NCK-001',
            category=self.category,
            price=1650.00,
            inventory=20
        )
        self.coupon = Coupon.objects.create(code='LUCKJARY10', discount_percent=10, is_percent=True)
        self.staff_user = CustomUser.objects.create_user(
            username='staff_manager',
            email='manager@luckjary.com',
            password='StaffPassword123!',
            is_staff=True
        )

    def test_cart_workflow_and_coupon(self):
        # Add to cart
        add_resp = self.client.post(reverse('orders:add_to_cart', kwargs={'product_id': self.product.id}), {
            'quantity': 1,
            'size': '18" Chain'
        })
        self.assertEqual(add_resp.status_code, 302)

        # Check cart page
        cart_resp = self.client.get(reverse('orders:cart'))
        self.assertEqual(cart_resp.status_code, 200)
        self.assertContains(cart_resp, 'Lumière Teardrop Diamond Solitaire Pendant')
        self.assertContains(cart_resp, '$1650.00')

        # Apply coupon
        coupon_resp = self.client.post(reverse('orders:apply_coupon'), {'coupon_code': 'LUCKJARY10'})
        self.assertEqual(coupon_resp.status_code, 302)

        cart_resp_after = self.client.get(reverse('orders:cart'))
        self.assertContains(cart_resp_after, 'LUCKJARY10 applied')
        self.assertContains(cart_resp_after, '-$165.00')

    def test_real_time_customer_tracking_portal(self):
        order = Order.objects.create(
            order_number='LCK-202611-TESTTRACK',
            email='patron@luxury.com',
            full_name='Marcus Sterling',
            shipping_street='10 Central Park West',
            shipping_city='New York',
            shipping_state='NY',
            shipping_zip='10023',
            status='SHIPPED',
            carrier='FedEx Luxury Priority Overnight',
            tracking_number='FDX-123456789-USA',
            subtotal=1650.00,
            total_amount=1650.00
        )
        OrderStatusUpdate.objects.create(
            order=order,
            status='SHIPPED',
            title='In Armored Transit',
            description='Dispatched via secure overnight flight.',
            location='Newark Logistics Center'
        )

        # Track order lookup
        track_resp = self.client.post(reverse('orders:order_tracking'), {
            'order_number': 'LCK-202611-TESTTRACK',
            'email': 'patron@luxury.com'
        })
        self.assertEqual(track_resp.status_code, 200)
        self.assertContains(track_resp, 'LCK-202611-TESTTRACK')
        self.assertContains(track_resp, 'In Armored Transit')
        self.assertContains(track_resp, 'FDX-123456789-USA')
        self.assertContains(track_resp, 'FedEx Luxury Priority Overnight')

    def test_staff_oms_dashboard_and_status_update(self):
        order = Order.objects.create(
            order_number='LCK-202611-OMSTEST',
            email='client@luxury.com',
            full_name='Elena Rostova',
            shipping_street='5th Ave',
            shipping_city='New York',
            shipping_state='NY',
            shipping_zip='10021',
            status='PENDING',
            subtotal=2450.00,
            total_amount=2450.00
        )

        # Anonymous cannot access OMS
        anon_resp = self.client.get(reverse('orders:oms_dashboard'))
        self.assertEqual(anon_resp.status_code, 302)

        # Staff can access OMS
        self.client.force_login(self.staff_user)
        staff_resp = self.client.get(reverse('orders:oms_dashboard'))
        self.assertEqual(staff_resp.status_code, 200)
        self.assertContains(staff_resp, 'Atelier OMS Console')
        self.assertContains(staff_resp, 'LCK-202611-OMSTEST')

        # Update order status via OMS
        update_resp = self.client.post(reverse('orders:oms_dashboard'), {
            'update_order_status': '1',
            'order_number': 'LCK-202611-OMSTEST',
            'new_status': 'PROCESSING',
            'carrier': 'Ferrari Armored Logistics',
            'tracking_number': 'FAR-998877',
            'estimated_delivery': '2026-11-15',
            'log_note': 'Diamond setting completed in New York atelier.',
            'log_location': 'Luckjary Main Atelier'
        })
        self.assertEqual(update_resp.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, 'PROCESSING')
        self.assertEqual(order.carrier, 'Ferrari Armored Logistics')
        self.assertEqual(order.tracking_number, 'FAR-998877')
        self.assertEqual(order.status_updates.count(), 1)
