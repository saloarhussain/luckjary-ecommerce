from .models import Category, Material, Collection

def catalog_context(request):
    wishlist = request.session.get('wishlist', [])
    
    # Active jewellery collection switcher: 'silver', 'fashion' (default 'silver')
    metal_param = request.GET.get('metal')
    if metal_param and metal_param.lower() in ['silver', 'fashion']:
        active_metal = metal_param.lower()
        request.session['active_metal'] = active_metal
    else:
        active_metal = request.session.get('active_metal')
        if active_metal not in ['silver', 'fashion']:
            active_metal = 'silver'
            request.session['active_metal'] = active_metal

    return {
        'nav_categories': Category.objects.all(),
        'nav_materials': Material.objects.all()[:6],
        'nav_collections': Collection.objects.filter(is_active=True)[:4],
        'wishlist_count': len(wishlist),
        'site_name': 'Luckjary',
        'site_tagline': 'Fine Silver & Luxury Fashion Jewelry',
        'active_metal': active_metal,
    }
