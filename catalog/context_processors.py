from .models import Category, Material, Collection

def catalog_context(request):
    wishlist = request.session.get('wishlist', [])

    return {
        'nav_categories': Category.objects.all(),
        'nav_materials': Material.objects.all()[:6],
        'nav_collections': Collection.objects.filter(is_active=True)[:4],
        'wishlist_count': len(wishlist),
        'site_name': 'Luckjary',
        'site_tagline': 'Pure 925 Sterling Silver Jewellery',
        'active_metal': 'silver',
    }
