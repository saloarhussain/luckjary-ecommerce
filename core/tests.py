from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from orders.models import Order, OrderItem
from core.telemetry import get_atelier_live_telemetry


class TelemetryMetricsTests(TestCase):
    def test_order_change_form_handles_deleted_product(self):
        superuser = CustomUser.objects.create_superuser(
            username='admin_check',
            email='admin_check@luckjary.com',
            password='AdminPassword123!',
        )
        order = Order.objects.create(
            order_number='LCK-DELPROD-1',
            email='patron@example.com',
            full_name='Julian Stewart',
            shipping_street='1 St',
            shipping_city='NY',
            shipping_state='NY',
            shipping_zip='10001',
            status='CANCELLED',
            payment_status='PAID',
            subtotal=3450.00,
            total_amount=3450.00,
        )
        OrderItem.objects.create(
            order=order,
            product=None,
            product_name='Archived Bracelet',
            product_sku='LCK-ARCH-1',
            product_image='https://example.com/img.jpg',
            unit_price=3450.00,
            quantity=1,
        )
        self.client.force_login(superuser)
        resp = self.client.get(reverse('admin:orders_order_change', args=[order.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Archived Bracelet')
        self.assertContains(resp, 'LCK-ARCH-1')

    def test_telemetry_excludes_cancelled_and_unpaid_orders(self):
        Order.objects.create(
            order_number='LCK-T1',
            email='a@example.com',
            full_name='A Patron',
            shipping_street='1 St',
            shipping_city='NY',
            shipping_state='NY',
            shipping_zip='10001',
            status='DELIVERED',
            payment_status='PAID',
            subtotal=1000.00,
            total_amount=1000.00,
        )
        Order.objects.create(
            order_number='LCK-T2',
            email='b@example.com',
            full_name='B Patron',
            shipping_street='2 St',
            shipping_city='NY',
            shipping_state='NY',
            shipping_zip='10001',
            status='PROCESSING',
            payment_status='PAID',
            subtotal=2000.00,
            total_amount=2000.00,
        )
        # Paid but cancelled -> must NOT count toward revenue or AOV
        Order.objects.create(
            order_number='LCK-T3',
            email='c@example.com',
            full_name='C Patron',
            shipping_street='3 St',
            shipping_city='NY',
            shipping_state='NY',
            shipping_zip='10001',
            status='CANCELLED',
            payment_status='PAID',
            subtotal=3450.00,
            total_amount=3450.00,
        )
        # Unpaid pending -> must NOT count toward revenue or AOV, MUST count in unfulfilled_count
        Order.objects.create(
            order_number='LCK-T4',
            email='d@example.com',
            full_name='D Patron',
            shipping_street='4 St',
            shipping_city='NY',
            shipping_state='NY',
            shipping_zip='10001',
            status='PENDING',
            payment_status='PENDING',
            subtotal=500.00,
            total_amount=500.00,
        )

        data = get_atelier_live_telemetry(summary_only=False)
        self.assertEqual(data['total_orders'], 4)
        self.assertEqual(data['total_revenue'], '3,000.00')
        self.assertEqual(data['avg_aov'], '1,500.00')
        self.assertEqual(data['pending_count'], 1)
        self.assertEqual(data['processing_count'], 1)
        self.assertEqual(data['unfulfilled_count'], 2)
