from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect
from core.views import set_currency

# Customize Django Admin Header & Title
admin.site.site_header = "Luckjary Haute Joaillerie Administration"
admin.site.site_title = "Luckjary Atelier Portal"
admin.site.index_title = "Atelier & Order Operations"

# Inject live high-performance metrics into Admin Dashboard Index
original_admin_index = admin.site.index

def atelier_admin_index(request, extra_context=None):
    extra = extra_context or {}
    try:
        from orders.models import Order
        from catalog.models import Product
        from accounts.models import CustomUser
        from django.db.models import Sum, Count, Q

        order_stats = Order.objects.aggregate(
            rev=Sum('total_amount'),
            total_orders=Count('id'),
            pending=Count('id', filter=Q(status='PENDING')),
            processing=Count('id', filter=Q(status='PROCESSING')),
            shipped=Count('id', filter=Q(status='SHIPPED')),
            delivered=Count('id', filter=Q(status='DELIVERED'))
        )
        total_products = Product.objects.count()
        total_customers = CustomUser.objects.count()

        rev = order_stats['rev'] or 0
        total_orders = order_stats['total_orders'] or 0
        pending = order_stats['pending'] or 0
        processing = order_stats['processing'] or 0
        shipped = order_stats['shipped'] or 0
        delivered = order_stats['delivered'] or 0

        avg_aov = (rev / total_orders) if total_orders > 0 else 0
        rev_inr = int(float(rev) * 83.1527)
        avg_aov_inr = int(float(avg_aov) * 83.1527)

        extra.update({
            'total_revenue': f"{rev:,.2f}",
            'total_revenue_inr': f"{rev_inr:,}",
            'total_orders': total_orders,
            'pending_count': pending,
            'processing_count': processing,
            'unfulfilled_count': pending + processing,
            'shipped_count': shipped,
            'delivered_count': delivered,
            'avg_aov': f"{avg_aov:,.2f}",
            'avg_aov_inr': f"{avg_aov_inr:,}",
            'total_products': total_products,
            'total_customers': total_customers,
        })
        extra['recent_orders'] = Order.objects.select_related('user').order_by('-created_at')[:6]
        extra['active_nav'] = 'home'
        extra['is_dashboard'] = True
    except Exception:
        pass
    return original_admin_index(request, extra_context=extra)

admin.site.index = atelier_admin_index

urlpatterns = [
    path('admin/scrape/', lambda request: HttpResponseRedirect('/admin/catalog/product/scrape/'), name='admin_scrape'),
    path('admin/settings/', lambda request: HttpResponseRedirect('/admin/orders/order/#settings'), name='admin_settings'),
    path('admin/set-currency/', set_currency, name='admin_set_currency'),
    path('set-currency/', set_currency, name='set_currency'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('catalog.urls')),
    path('', include('orders.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
