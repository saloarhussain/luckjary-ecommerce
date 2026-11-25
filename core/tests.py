from django.test import TestCase
from orders.models import Order
from core.telemetry import get_atelier_live_telemetry


class TelemetryMetricsTests(TestCase):
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
