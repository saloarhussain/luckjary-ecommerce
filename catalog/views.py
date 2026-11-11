from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Product, Category, Material, Collection, ProductReview
import json

def product_list(request):
    products = Product.objects.filter(is_available=True)

    # 0. Metal Switcher Filter (Gold, Silver, Demifine)
    metal = request.GET.get('metal')
    if not metal and 'metal' not in request.GET:
        metal = request.session.get('active_metal', 'gold')
    elif metal:
        request.session['active_metal'] = metal

    selected_metal = metal.lower() if metal else 'gold'
    if selected_metal == 'silver':
        products = products.filter(
            Q(karat_metal__icontains='Silver') |
            Q(materials__name__icontains='Silver') |
            Q(title__icontains='Silver')
        ).distinct()
    elif selected_metal == 'demifine':
        products = products.filter(
            Q(karat_metal__icontains='Demifine') |
            Q(karat_metal__icontains='Vermeil') |
            Q(materials__name__icontains='Demifine') |
            Q(title__icontains='Demifine')
        ).distinct()
    elif selected_metal == 'gold':
        products = products.filter(
            Q(karat_metal__icontains='Gold') |
            Q(karat_metal__icontains='Platinum') |
            Q(materials__name__icontains='Gold') |
            Q(materials__name__icontains='Platinum') |
            Q(title__icontains='Gold')
        ).distinct()

    # 1. Category Filter
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # 2. Material Filter
    material_slug = request.GET.get('material')
    selected_material = None
    if material_slug:
        selected_material = get_object_or_404(Material, slug=material_slug)
        products = products.filter(materials=selected_material)

    # 3. Style Filter
    style = request.GET.get('style')
    if style:
        products = products.filter(style=style)

    # 4. Collection Filter
    collection_slug = request.GET.get('collection')
    selected_collection = None
    if collection_slug:
        selected_collection = get_object_or_404(Collection, slug=collection_slug)
        products = products.filter(collection=selected_collection)

    # 5. Price Range Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # 6. Search Query
    search_query = request.GET.get('q', '').strip()
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(karat_metal__icontains=search_query) |
            Q(gemstone__icontains=search_query) |
            Q(sku__icontains=search_query)
        )

    # 7. Sorting
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        products = products.annotate(avg_rate=Avg('reviews__rating')).order_by('-avg_rate')
    else: # featured
        products = products.order_by('-is_featured', '-created_at')

    # Pagination
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context for Filter Sidebars
    all_categories = Category.objects.all()
    all_materials = Material.objects.all()
    all_collections = Collection.objects.filter(is_active=True)

    page_title = "The High Jewelry Collection"
    page_desc = "Explore handcrafted diamond rings, solid 18k gold necklaces, and luxury jewelry creations at Luckjary."
    if selected_category:
        page_title = f"{selected_category.name} Collection"
        page_desc = selected_category.description or page_desc
    elif selected_material:
        page_title = f"{selected_material.name} Jewelry"
    elif selected_collection:
        page_title = f"{selected_collection.name} Collection"
        page_desc = selected_collection.description or page_desc
    elif selected_metal == 'silver':
        page_title = "925 Sterling Silver Jewellery"
        page_desc = "Discover luminous 925 sterling silver necklaces, pavé rings, and heirloom pieces."
    elif selected_metal == 'demifine':
        page_title = "18K Gold Vermeil & Demifine Jewellery"
        page_desc = "Elevate your daily signature with heavy 18K solid gold layered over pure sterling silver."
    elif selected_metal == 'gold':
        page_title = "Solid 18K Gold & Haute Joaillerie"

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': products.count(),
        'all_categories': all_categories,
        'all_materials': all_materials,
        'all_collections': all_collections,
        'selected_category': selected_category,
        'selected_material': selected_material,
        'selected_metal': selected_metal,
        'selected_style': style,
        'selected_sort': sort_by,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'search_query': search_query,
        'meta_title': f"{page_title} | Luckjary Fine Jewelry",
        'meta_description': page_desc[:160],
    }
    return render(request, 'catalog/product_list.html', context)


def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, is_available=True)

    metal = request.GET.get('metal') or request.session.get('active_metal', 'gold')
    if request.GET.get('metal'):
        request.session['active_metal'] = request.GET.get('metal')
    selected_metal = metal.lower() if metal else 'gold'

    if selected_metal == 'silver':
        matched = products.filter(
            Q(karat_metal__icontains='Silver') |
            Q(materials__name__icontains='Silver') |
            Q(title__icontains='Silver')
        ).distinct()
        if matched.exists():
            products = matched
    elif selected_metal == 'demifine':
        matched = products.filter(
            Q(karat_metal__icontains='Demifine') |
            Q(karat_metal__icontains='Vermeil') |
            Q(materials__name__icontains='Demifine') |
            Q(title__icontains='Demifine')
        ).distinct()
        if matched.exists():
            products = matched
    elif selected_metal == 'gold':
        matched = products.filter(
            Q(karat_metal__icontains='Gold') |
            Q(karat_metal__icontains='Platinum') |
            Q(materials__name__icontains='Gold') |
            Q(title__icontains='Gold')
        ).distinct()
        if matched.exists():
            products = matched

    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-is_featured', '-created_at')

    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': products.count(),
        'selected_category': category,
        'all_categories': Category.objects.all(),
        'all_materials': Material.objects.all(),
        'meta_title': category.meta_title or f"{category.name} | Luckjary Fine Jewelry",
        'meta_description': category.meta_description or f"Shop luxury {category.name.lower()} handcrafted in 18K solid gold and platinum.",
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    images = product.images.all()
    reviews = product.reviews.filter(is_approved=True)
    related_products = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]

    # Handle review submission
    if request.method == 'POST' and 'submit_review' in request.POST:
        author_name = request.POST.get('author_name', '').strip()
        rating = request.POST.get('rating', '5')
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        if author_name and title and comment:
            try:
                r_val = int(rating)
                if 1 <= r_val <= 5:
                    ProductReview.objects.create(
                        product=product,
                        user=request.user if request.user.is_authenticated else None,
                        author_name=author_name,
                        rating=r_val,
                        title=title,
                        comment=comment,
                        is_verified_buyer=request.user.is_authenticated,
                        is_approved=True # Auto-approve for demo realism
                    )
                    messages.success(request, "Thank you! Your verified review has been published.")
                    return redirect('catalog:product_detail', slug=product.slug)
            except ValueError:
                pass
        messages.error(request, "Please fill in all review fields.")

    # Generate Google Rich Snippet JSON-LD Product Schema
    image_urls = [img.image_url for img in images] if images.exists() else [product.primary_image]
    schema_data = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": product.title,
        "image": image_urls,
        "description": product.meta_description or product.description[:200],
        "sku": product.sku,
        "mpn": product.sku,
        "brand": {
            "@type": "Brand",
            "name": "Luckjary"
        },
        "offers": {
            "@type": "Offer",
            "url": request.build_absolute_uri(product.get_absolute_url()),
            "priceCurrency": "USD",
            "price": str(product.price),
            "priceValidUntil": "2027-12-31",
            "itemCondition": "https://schema.org/NewCondition",
            "availability": "https://schema.org/InStock" if product.inventory > 0 else "https://schema.org/OutOfStock",
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {
                    "@type": "MonetaryAmount",
                    "value": "0.00",
                    "currency": "USD"
                },
                "deliveryTime": {
                    "@type": "ShippingDeliveryTime",
                    "businessDays": {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "transitTime": {
                        "@type": "QuantitativeValue",
                        "minValue": 1,
                        "maxValue": 3,
                        "unitCode": "DAY"
                    }
                }
            }
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(product.average_rating),
            "reviewCount": str(max(1, product.review_count))
        }
    }

    context = {
        'product': product,
        'images': images,
        'reviews': reviews,
        'related_products': related_products,
        'schema_json': json.dumps(schema_data),
        'meta_title': product.meta_title or f"{product.title} | Luckjary",
        'meta_description': product.meta_description or product.description[:160],
        'og_image': product.primary_image,
    }
    return render(request, 'catalog/product_detail.html', context)
