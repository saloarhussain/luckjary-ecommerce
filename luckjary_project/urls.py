from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize Django Admin Header & Title
admin.site.site_header = "Luckjary Haute Joaillerie Administration"
admin.site.site_title = "Luckjary Atelier Portal"
admin.site.index_title = "Atelier & Order Operations"

# Inject live atelier metrics into Admin Dashboard Index
original_admin_index = admin.site.index

def atelier_admin_index(request, extra_context=None):
    extra = extra_context or {}
    try:
        from orders.models import Order
        from catalog.models import Product
        from django.db.models import Sum
        
        rev = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        extra['total_revenue'] = f"{rev:,.2f}"
        extra['total_orders'] = Order.objects.count()
        extra['pending_count'] = Order.objects.filter(status='PENDING').count()
        extra['processing_count'] = Order.objects.filter(status='PROCESSING').count()
        extra['shipped_count'] = Order.objects.filter(status='SHIPPED').count()
        extra['delivered_count'] = Order.objects.filter(status='DELIVERED').count()
        extra['total_products'] = Product.objects.count()
    except Exception:
        pass
    return original_admin_index(request, extra_context=extra)

admin.site.index = atelier_admin_index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('catalog.urls')),
    path('', include('orders.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
