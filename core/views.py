from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from catalog.models import Product, Category, Collection
from .models import NewsletterSubscriber, ContactInquiry

def home(request):
    featured_products = Product.objects.filter(is_available=True, is_featured=True)[:8]
    bestsellers = Product.objects.filter(is_available=True, is_bestseller=True)[:4]
    new_arrivals = Product.objects.filter(is_available=True, is_new_arrival=True)[:4]
    categories = Category.objects.filter(is_featured=True)[:5]
    collections = Collection.objects.filter(is_active=True)[:3]

    context = {
        'featured_products': featured_products,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'collections': collections,
        'meta_title': 'Luckjary | Fine Jewelry, Solid 18K Gold & Certified Diamonds',
        'meta_description': 'Discover exquisite handcrafted luxury jewelry at Luckjary. Explore engagement rings, 18K solid gold necklaces, diamond tennis bracelets, and bespoke bridal heirlooms.',
    }
    return render(request, 'core/home.html', context)

def about(request):
    return render(request, 'core/about.html', {
        'meta_title': 'The Luckjary Heritage & Atelier | Crafting Modern Heirlooms',
        'meta_description': 'Learn about the artisans, sustainable sourcing, and master gemology behind Luckjary fine jewelry.',
    })

def faq(request):
    return render(request, 'core/faq.html', {
        'meta_title': 'Frequently Asked Questions & Care Guide | Luckjary Concierge',
        'meta_description': 'Find answers on our insured worldwide shipping, ring sizing guide, lifetime warranties, and bespoke commissions.',
    })

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            ContactInquiry.objects.create(name=name, email=email, subject=subject or 'General Inquiry', message=message)
            messages.success(request, "Thank you for reaching out to the Luckjary Concierge. A personal gemologist advisor will respond within 24 hours.")
            return redirect('core:contact')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'core/contact.html', {
        'meta_title': 'Contact the Luckjary Concierge | Bespoke Consultations',
        'meta_description': 'Speak with our certified gemologists and personal stylists for custom jewelry commissions and inquiries.',
    })

def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if email:
            sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                messages.success(request, "Welcome to the Luckjary Privé Club. Please use code VIPLUCK20 on your next purchase.")
            else:
                messages.info(request, "You are already a distinguished member of the Luckjary Privé Club.")
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))
    return redirect('core:home')

def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = request.session.get('wishlist', [])

    if product_id in wishlist:
        wishlist.remove(product_id)
        action = 'removed'
        msg = f"{product.title} removed from your wishlist."
    else:
        wishlist.append(product_id)
        action = 'added'
        msg = f"{product.title} saved to your wishlist."

    request.session['wishlist'] = wishlist
    request.session.modified = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'action': action, 'count': len(wishlist), 'message': msg})

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'catalog:product_list'))

def wishlist_view(request):
    wishlist_ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist_ids, is_available=True)
    return render(request, 'catalog/wishlist.html', {
        'products': products,
        'meta_title': 'Your Curated Wishlist | Luckjary Fine Jewelry',
        'meta_description': 'View your saved high jewelry favorites and custom selections.',
    })

def robots_txt(request):
    content = "User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /oms/\nDisallow: /checkout/\nDisallow: /accounts/\n\nSitemap: https://www.luckjary.com/sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain")

def sitemap_xml(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    collections = Collection.objects.filter(is_active=True)
    
    xml_content = render(request, 'core/sitemap.xml', {
        'products': products,
        'categories': categories,
        'collections': collections,
    })
    return HttpResponse(xml_content, content_type="application/xml")
