from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect, JsonResponse
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
        from core.telemetry import get_atelier_live_telemetry
        extra.update(get_atelier_live_telemetry(summary_only=False))
        extra['active_nav'] = 'home'
        extra['is_dashboard'] = True
    except Exception:
        pass
    return original_admin_index(request, extra_context=extra)

def admin_live_telemetry_api(request):
    try:
        from core.telemetry import get_atelier_live_telemetry
        summary_only = request.GET.get('summary') == '1'
        payload = get_atelier_live_telemetry(summary_only=summary_only)
        return JsonResponse({'status': 'ok', **payload})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

admin.site.index = atelier_admin_index

urlpatterns = [
    path('admin/api/live-telemetry/', admin.site.admin_view(admin_live_telemetry_api), name='admin_live_telemetry'),
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
