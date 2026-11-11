from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
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
    list_display = ('code', 'discount_display', 'is_percent', 'active', 'min_spend')
    list_filter = ('active', 'is_percent')
    search_fields = ('code',)

    @admin.display(description='Discount Value')
    def discount_display(self, obj):
        if obj.is_percent:
            return format_html('<span class="badge-luxury badge-delivered">{}% OFF</span>', obj.discount_percent)
        return format_html('<span class="badge-luxury badge-delivered">${} OFF</span>', obj.discount_amount)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_badge', 
        'customer_badge', 
        'status_pill', 
        'payment_pill', 
        'amount_gold', 
        'logistics_pill', 
        'gift_pill', 
        'created_display'
    )
    list_filter = ('status', 'payment_status', 'carrier', 'gift_wrapping', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'tracking_number', 'shipping_street', 'shipping_city')
    readonly_fields = ('order_number', 'subtotal', 'shipping_cost', 'discount_amount', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderStatusUpdateInline]
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']

    @admin.display(description='Order Ref', ordering='order_number')
    def order_badge(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="text-decoration:none;"><span class="order-pill">{}</span></a>',
            url,
            obj.order_number
        )

    @admin.display(description='Customer & Contact', ordering='full_name')
    def customer_badge(self, obj):
        if obj.phone:
            return format_html(
                '<div style="line-height:1.35;">'
                '<div style="font-weight:600; color:#FFFFFF;">{}</div>'
                '<div style="color:#DFBE76; font-size:0.72rem;">{}</div>'
                '<div style="color:#78788C; font-size:0.68rem;">📞 {}</div>'
                '</div>',
                obj.full_name,
                obj.email,
                obj.phone
            )
        return format_html(
            '<div style="line-height:1.35;">'
            '<div style="font-weight:600; color:#FFFFFF;">{}</div>'
            '<div style="color:#DFBE76; font-size:0.72rem;">{}</div>'
            '</div>',
            obj.full_name,
            obj.email
        )

    @admin.display(description='Fulfillment Stage', ordering='status')
    def status_pill(self, obj):
        badges = {
            'PENDING': ('badge-pending', '⏳ Intake Queue'),
            'PROCESSING': ('badge-processing', '◆ In Atelier QC'),
            'SHIPPED': ('badge-shipped', '✈ In Armored Transit'),
            'DELIVERED': ('badge-delivered', '✓ Delivered'),
            'CANCELLED': ('badge-cancelled', '✕ Cancelled'),
        }
        cls, label = badges.get(obj.status, ('badge-pending', obj.get_status_display()))
        return format_html('<span class="badge-luxury {}">{}</span>', cls, label)

    @admin.display(description='Payment', ordering='payment_status')
    def payment_pill(self, obj):
        if obj.payment_status == 'PAID':
            return mark_safe('<span class="badge-luxury badge-paid">🔒 Captured</span>')
        elif obj.payment_status == 'PENDING':
            return mark_safe('<span class="badge-luxury badge-pending">⏳ Pending</span>')
        return mark_safe('<span class="badge-luxury badge-cancelled">Refunded</span>')

    @admin.display(description='Total Amount', ordering='total_amount')
    def amount_gold(self, obj):
        return format_html('<span class="price-gold">${}</span>', f"{obj.total_amount:,.2f}")

    @admin.display(description='Logistics Telemetry', ordering='carrier')
    def logistics_pill(self, obj):
        carrier_short = obj.carrier.replace('Luxury Priority Overnight', 'Priority').replace('Armored Logistics / White Glove', 'Armored')
        if obj.tracking_number:
            track_url = f"/track/{obj.order_number}/"
            return format_html(
                '<div style="font-size:0.75rem;">'
                '<div style="color:#C6C6D6; font-weight:500;">{}</div>'
                '<div style="margin-top:2px;"><a href="{}" target="_blank" class="tracking-link">{}</a></div>'
                '</div>',
                carrier_short,
                track_url,
                obj.tracking_number
            )
        return format_html(
            '<div style="font-size:0.75rem;">'
            '<div style="color:#C6C6D6; font-weight:500;">{}</div>'
            '<div style="color:#666675; font-size:0.68rem;">Pending Dispatch</div>'
            '</div>',
            carrier_short
        )

    @admin.display(description='Signature Gift Box')
    def gift_pill(self, obj):
        if obj.gift_wrapping:
            return mark_safe('<span class="badge-luxury" style="background:rgba(197,160,89,0.15); color:#DFBE76; border:1px solid rgba(197,160,89,0.3);">🎁 Signature Gold</span>')
        return mark_safe('<span style="color:#666675;">Standard</span>')

    @admin.display(description='Date Placed', ordering='created_at')
    def created_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y • %H:%M')

    @admin.action(description='Mark selected orders as PROCESSING (In Atelier)')
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

    @admin.action(description='Mark selected orders as SHIPPED (In Armored Transit)')
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
