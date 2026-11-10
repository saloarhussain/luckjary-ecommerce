from django.db import models
from django.conf import settings
from catalog.models import Product
import uuid
import datetime

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(default=10, help_text="Discount in percent (e.g. 15 for 15%)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_percent = models.BooleanField(default=True)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    active = models.BooleanField(default=True)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.is_percent:
            return f"{self.code} ({self.discount_percent}% OFF)"
        return f"{self.code} (${self.discount_amount} OFF)"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('PROCESSING', 'Processing & Handcrafting'),
        ('SHIPPED', 'Shipped & In Transit'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Payment Captured'),
        ('PENDING', 'Payment Pending'),
        ('REFUNDED', 'Refunded'),
    ]

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Guest and contact information
    email = models.EmailField(verbose_name="Contact / Notification Email")
    full_name = models.CharField(max_length=150, verbose_name="Customer Name")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Phone Number")

    # Shipping Details
    shipping_street = models.CharField(max_length=255)
    shipping_apartment = models.CharField(max_length=100, blank=True, null=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_zip = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='United States')

    # OMS & Logistics
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PAID')
    payment_method = models.CharField(max_length=80, default='Secure Card Payment (Stripe Luxury)')

    # Fulfillment & Tracking
    carrier = models.CharField(max_length=100, default='FedEx Luxury Priority Overnight')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(max_length=500, blank=True, null=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    
    # Financial breakdown
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    # Luxury touches
    gift_wrapping = models.BooleanField(default=True, verbose_name="Complimentary Signature Gold Gift Box")
    gift_message = models.TextField(blank=True, null=True, verbose_name="Handwritten Gift Card Message")
    customer_notes = models.TextField(blank=True, null=True)
    internal_admin_notes = models.TextField(blank=True, null=True, help_text="Notes for atelier and fulfillment team")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            now = datetime.datetime.now()
            rand_code = uuid.uuid4().hex[:6].upper()
            self.order_number = f"LCK-{now.strftime('%Y%m')}-{rand_code}"
        if not self.estimated_delivery and self.status in ['PENDING', 'PROCESSING', 'SHIPPED']:
            self.estimated_delivery = datetime.date.today() + datetime.timedelta(days=3)
        super().save(*args, **kwargs)

    @property
    def status_step_index(self):
        steps = {
            'PENDING': 1,
            'PROCESSING': 2,
            'SHIPPED': 3,
            'DELIVERED': 4,
            'CANCELLED': 0,
        }
        return steps.get(self.status, 1)

    @property
    def formatted_shipping_address(self):
        parts = [self.shipping_street]
        if self.shipping_apartment:
            parts.append(self.shipping_apartment)
        parts.append(f"{self.shipping_city}, {self.shipping_state} {self.shipping_zip}")
        parts.append(self.shipping_country)
        return ", ".join(parts)

    def __str__(self):
        return f"{self.order_number} - {self.full_name} (${self.total_amount})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=220)
    product_sku = models.CharField(max_length=60, blank=True)
    product_image = models.URLField(max_length=600, blank=True)
    selected_size = models.CharField(max_length=60, default='Standard / US 7')
    selected_material = models.CharField(max_length=100, default='18K Solid Yellow Gold')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in {self.order.order_number}"


class OrderStatusUpdate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=120, default='Luckjary Vault & Ateliers, New York, NY')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.order.order_number}: {self.title}"
