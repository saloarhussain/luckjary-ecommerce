from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import Order, OrderItem, OrderStatusUpdate, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ('item_preview', 'product_name', 'product_sku', 'selected_material', 'selected_size', 'unit_price', 'quantity', 'line_total')
    fields = ('item_preview', 'product_name', 'product_sku', 'selected_material', 'selected_size', 'unit_price', 'quantity', 'line_total')

    @admin.display(description='Piece Preview')
    def item_preview(self, obj):
        if obj and obj.product_image:
            return format_html(
                '<div class="order-item-inline-preview">'
                '<img src="{}" alt="{}" style="width:42px; height:42px; object-fit:cover; border-radius:6px; border:1px solid rgba(197,160,89,0.35); flex-shrink:0;" />'
                '</div>',
                obj.product_image,
                obj.product_name
            )
        return mark_safe('<span class="order-item-inline-empty" style="font-size:1.4rem;">💎</span>')

    @admin.display(description='Line Total')
    def line_total(self, obj):
        if obj and obj.unit_price is not None:
            return f"${(obj.unit_price * (obj.quantity or 1)):,.2f}"
        return "$0.00"

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 1
    fields = ('status', 'title', 'location', 'description', 'timestamp_display')
    readonly_fields = ('timestamp_display',)

    @admin.display(description='Logged At')
    def timestamp_display(self, obj):
        if obj and obj.timestamp:
            return obj.timestamp.strftime('%b %d, %Y • %H:%M')
        return "Automatic on Save"


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
    inlines = [OrderItemInline, OrderStatusUpdateInline]
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']

    def get_fieldsets(self, request, obj=None):
        if obj:
            return (
                ('Order Telemetry & Stage', {
                    'fields': (
                        'order_banner_card',
                        ('status', 'payment_status'),
                        ('carrier', 'tracking_number'),
                        ('tracking_url', 'estimated_delivery'),
                    ),
                    'classes': ('lux-fieldset', 'lux-logistics-card'),
                }),
                ('Patron & Client Identification (Protected)', {
                    'description': 'Customer identity and contact credentials are non-editable to preserve transaction integrity, legal audit compliance, and prevent accidental modifications.',
                    'fields': (
                        'customer_profile_card',
                    ),
                    'classes': ('lux-fieldset', 'lux-patron-card'),
                }),
                ('Delivery & Shipping Destination', {
                    'description': 'Shipping address may be amended by fulfillment staff prior to dispatch upon verified patron request.',
                    'fields': (
                        ('shipping_street', 'shipping_apartment'),
                        ('shipping_city', 'shipping_state'),
                        ('shipping_zip', 'shipping_country'),
                    ),
                    'classes': ('lux-fieldset', 'lux-shipping-card'),
                }),
                ('Financial Summary & Settlement', {
                    'fields': (
                        ('subtotal', 'shipping_cost'),
                        ('discount_amount', 'coupon'),
                        'total_amount',
                        'payment_method',
                    ),
                    'classes': ('lux-fieldset', 'lux-financial-card'),
                }),
                ('Atelier Presentation & Directives', {
                    'fields': (
                        'gift_wrapping',
                        'gift_message',
                        'customer_notes',
                        'internal_admin_notes',
                    ),
                    'classes': ('lux-fieldset', 'lux-notes-card'),
                }),
            )
        return (
            ('New Order Setup', {
                'fields': (
                    ('status', 'payment_status'),
                    ('user', 'full_name'),
                    ('email', 'phone'),
                    ('shipping_street', 'shipping_apartment'),
                    ('shipping_city', 'shipping_state'),
                    ('shipping_zip', 'shipping_country'),
                    ('carrier', 'payment_method'),
                    'gift_wrapping',
                    'internal_admin_notes',
                ),
                'classes': ('lux-fieldset',),
            }),
        )

    def get_readonly_fields(self, request, obj=None):
        base_readonly = [
            'order_number',
            'order_banner_card',
            'customer_profile_card',
            'subtotal',
            'shipping_cost',
            'discount_amount',
            'total_amount',
            'created_at',
            'updated_at',
        ]
        if obj:
            return base_readonly + ['user', 'full_name', 'email', 'phone']
        return base_readonly

    @admin.display(description='Order Status Telemetry')
    def order_banner_card(self, obj):
        if not obj or not obj.id:
            return "Order telemetry will be initialized upon saving."
            
        status_badges = {
            'PENDING': ('badge-pending', '⏳ Intake Queue'),
            'PROCESSING': ('badge-processing', '◆ In Atelier QC'),
            'SHIPPED': ('badge-shipped', '✈ In Armored Transit'),
            'DELIVERED': ('badge-delivered', '✓ Delivered'),
            'CANCELLED': ('badge-cancelled', '✕ Cancelled'),
        }
        badge_cls, status_label = status_badges.get(obj.status, ('badge-pending', obj.get_status_display()))
        
        pay_html = '<span class="badge-luxury badge-paid">🔒 Payment Captured</span>' if obj.payment_status == 'PAID' else f'<span class="badge-luxury badge-pending">{obj.get_payment_status_display()}</span>'
        
        tracking_html = ""
        if obj.tracking_number:
            tracking_html = format_html(
                '<a href="/track/{}/" target="_blank" class="lux-track-live-btn">'
                '<span>Courier Telemetry</span> <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>'
                '</a>',
                obj.order_number
            )

        return format_html(
            '<div class="lux-order-banner-widget">'
                '<div class="lux-banner-top">'
                    '<div class="lux-banner-ref-wrap">'
                        '<span class="lux-banner-tag">HAUTE JOAILLERIE ORDER</span>'
                        '<div class="lux-banner-ordernum">{}</div>'
                    '</div>'
                    '<div class="lux-banner-amount-wrap">'
                        '<span class="lux-banner-tag">SETTLED AMOUNT</span>'
                        '<div class="lux-banner-amount">${:,.2f}</div>'
                    '</div>'
                '</div>'
                '<div class="lux-banner-meta">'
                    '<div class="lux-banner-pills">'
                        '<span class="badge-luxury {}">{}</span>'
                        '{}'
                    '</div>'
                    '<div class="lux-banner-date">📅 Placed {}</div>'
                '</div>'
                '{}'
            '</div>',
            obj.order_number,
            obj.total_amount,
            badge_cls,
            status_label,
            mark_safe(pay_html),
            obj.created_at.strftime('%b %d, %Y • %H:%M') if obj.created_at else 'Just now',
            mark_safe(tracking_html)
        )

    @admin.display(description='Patron & Client Verification')
    def customer_profile_card(self, obj):
        if not obj or not obj.id:
            return "Customer details recorded at checkout."
            
        if obj.user:
            user_url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
            user_markup = f'<a href="{user_url}" class="lux-client-user-tag" target="_blank">VIP Patron #{obj.user.id} &bull; @{obj.user.username} &rarr;</a>'
        else:
            user_markup = '<span class="lux-client-guest-tag">Verified Guest Patron</span>'
            
        initials = (obj.full_name[:2] if obj.full_name else "VP").upper()
        email_val = obj.email or "No email on record"
        phone_val = obj.phone or "No phone on record"
        phone_markup = f'<a href="tel:{obj.phone}" class="lux-client-link">📞 {obj.phone}</a>' if obj.phone else '<span class="lux-client-dim">📞 No phone registered</span>'

        return format_html(
            '<div class="lux-patron-summary-card">'
                '<div class="lux-patron-main-row">'
                    '<div class="lux-patron-badge-avatar">{}</div>'
                    '<div class="lux-patron-info-col">'
                        '<div class="lux-patron-fullname">{}</div>'
                        '<div class="lux-patron-status-tag">{}</div>'
                    '</div>'
                '</div>'
                '<div class="lux-patron-contact-grid">'
                    '<div class="lux-contact-cell">'
                        '<span class="lux-cell-label">Email Notification</span>'
                        '<a href="mailto:{}" class="lux-client-link" title="Send direct email to patron">✉ {}</a>'
                    '</div>'
                    '<div class="lux-contact-cell">'
                        '<span class="lux-cell-label">Contact Telephone</span>'
                        '{}'
                    '</div>'
                '</div>'
                '<div class="lux-patron-security-notice">'
                    '<span class="lux-security-icon">🔒</span>'
                    '<span class="lux-security-text"><strong>Protected Patron Record:</strong> Client identity and credentials are non-editable to preserve transaction integrity, legal audit compliance, and prevent accidental modifications.</span>'
                '</div>'
            '</div>',
            initials,
            obj.full_name or "Anonymous Client",
            mark_safe(user_markup),
            email_val,
            email_val,
            mark_safe(phone_markup)
        )

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
