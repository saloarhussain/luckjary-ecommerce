from .models import Category, Material, Collection

SUPPORTED_CURRENCIES = {
    'INR': {
        'code': 'INR',
        'symbol': '₹',
        'name': 'Indian Rupee (INR)',
        'flag': '🇮🇳',
    },
    'USD': {
        'code': 'USD',
        'symbol': '$',
        'name': 'US Dollar (USD)',
        'flag': '🇺🇸',
    },
    'EUR': {
        'code': 'EUR',
        'symbol': '€',
        'name': 'Euro (EUR)',
        'flag': '🇪🇺',
    },
    'GBP': {
        'code': 'GBP',
        'symbol': '£',
        'name': 'British Pound (GBP)',
        'flag': '🇬🇧',
    },
    'AED': {
        'code': 'AED',
        'symbol': 'AED ',
        'name': 'UAE Dirham (AED)',
        'flag': '🇦🇪',
    },
}

def catalog_context(request):
    wishlist = []
    currency_code = None

    if hasattr(request, 'session') and request.session is not None:
        wishlist = request.session.get('wishlist', [])
        currency_code = request.session.get('currency')

    if not currency_code and hasattr(request, 'COOKIES') and request.COOKIES is not None:
        currency_code = request.COOKIES.get('admin_currency')

    if not currency_code or currency_code not in SUPPORTED_CURRENCIES:
        currency_code = 'INR'

    active_currency = SUPPORTED_CURRENCIES[currency_code]

    # For admin requests, skip storefront categories/materials/collections; provide live sidebar counts for HTML pages
    if hasattr(request, 'path') and request.path.startswith('/admin/'):
        is_api = '/api/' in request.path or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        total_products = 0
        total_orders = 0
        if not is_api:
            try:
                from .models import Product
                total_products = Product.objects.count()
            except Exception:
                total_products = 0
            try:
                from orders.models import Order
                total_orders = Order.objects.count()
            except Exception:
                total_orders = 0

        return {
            'wishlist_count': 0,
            'site_name': 'Luckjary',
            'site_tagline': 'Pure 925 Sterling Silver Jewellery',
            'active_metal': 'silver',
            'currency_code': currency_code,
            'currency_symbol': active_currency['symbol'],
            'active_currency': active_currency,
            'supported_currencies': SUPPORTED_CURRENCIES,
            'total_products': total_products,
            'total_orders': total_orders,
        }

    return {
        'nav_categories': Category.objects.all(),
        'nav_materials': Material.objects.all()[:6],
        'nav_collections': Collection.objects.filter(is_active=True)[:4],
        'wishlist_count': len(wishlist),
        'site_name': 'Luckjary',
        'site_tagline': 'Pure 925 Sterling Silver Jewellery',
        'active_metal': 'silver',
        'currency_code': currency_code,
        'currency_symbol': active_currency['symbol'],
        'active_currency': active_currency,
        'supported_currencies': SUPPORTED_CURRENCIES,
    }
