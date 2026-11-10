from django.contrib import admin
from .models import Order, OrderItem, OrderStatusUpdate, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'unit_price', 'quantity', 'line_total')

class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 1

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'discount_amount', 'is_percent', 'active', 'min_spend')
    list_filter = ('active', 'is_percent')
    search_fields = ('code',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'email', 'status', 'payment_status', 'total_amount', 'carrier', 'tracking_number', 'created_at')
    list_filter = ('status', 'payment_status', 'carrier', 'gift_wrapping', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'tracking_number', 'shipping_street', 'shipping_city')
    readonly_fields = ('order_number', 'subtotal', 'shipping_cost', 'discount_amount', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderStatusUpdateInline]
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']

    @admin.action(description='Mark selected orders as PROCESSING')
    def mark_as_processing(self, request, queryset):
        queryset.update(status='PROCESSING')
        for order in queryset:
            OrderStatusUpdate.objects.create(
                order=order,
                status='PROCESSING',
                title='Moved to Processing & Quality Control',
                description='Order transferred to master jeweler team for inspection and preparation.',
                location='Luckjary New York Atelier'
            )

    @admin.action(description='Mark selected orders as SHIPPED')
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='SHIPPED')
        for order in queryset:
            OrderStatusUpdate.objects.create(
                order=order,
                status='SHIPPED',
                title='Package Dispatched with Courier',
                description='Dispatched via luxury insured courier. Tracking updated.',
                location='New York Logistics Hub'
            )

    @admin.action(description='Mark selected orders as DELIVERED')
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='DELIVERED')
        for order in queryset:
            OrderStatusUpdate.objects.create(
                order=order,
                status='DELIVERED',
                title='Delivered to Client',
                description='Shipment successfully delivered and signed.',
                location=f"{order.shipping_city}, {order.shipping_state}"
            )
