import json
import os
from pathlib import Path
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from catalog.models import Product, Category, Collection
from .models import NewsletterSubscriber, ContactInquiry, StorefrontThemeSettings

from django.db.models import Q

def home(request):
    all_featured = Product.objects.filter(is_available=True, is_featured=True)
    featured_products = all_featured.filter(
        Q(karat_metal__icontains='Silver') | Q(materials__name__icontains='Silver') | Q(title__icontains='Silver')
    ).distinct()
    if not featured_products.exists():
        featured_products = Product.objects.filter(is_available=True, materials__name__icontains='Silver')
    if not featured_products.exists():
        featured_products = all_featured

    bestsellers = Product.objects.filter(is_available=True, is_bestseller=True)[:4]
    new_arrivals = Product.objects.filter(is_available=True, is_new_arrival=True)[:4]
    categories = Category.objects.filter(is_featured=True)[:5]
    collections = Collection.objects.filter(is_active=True)[:3]
    theme_settings = StorefrontThemeSettings.get_solo()

    context = {
        'featured_products': featured_products[:8],
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'collections': collections,
        'theme_settings': theme_settings,
        'active_metal': 'silver',
        'meta_title': 'Luckjary | Handcrafted 925 Sterling Silver Jewellery',
        'meta_description': 'Discover exquisite handcrafted 925 sterling silver jewelry at Luckjary. Explore sterling silver rings, necklaces, bracelets, and earrings treated with rhodium anti-tarnish finish.',
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


def set_currency(request):
    """
    Set active store and admin currency in session and persistent cookie.
    Accepts GET /set-currency/?currency=USD or POST /set-currency/ with currency=USD
    """
    currency = request.POST.get('currency') or request.GET.get('currency') or 'INR'
    currency = currency.upper().strip()
    valid_currencies = ['INR', 'USD', 'EUR', 'GBP', 'AED']
    if currency not in valid_currencies:
        currency = 'INR'

    if hasattr(request, 'session') and request.session is not None:
        request.session['currency'] = currency
        request.session.modified = True

    redirect_url = request.META.get('HTTP_REFERER') or '/admin/'

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        from django.http import JsonResponse
        response = JsonResponse({'status': 'ok', 'currency': currency})
    else:
        from django.http import HttpResponseRedirect
        response = HttpResponseRedirect(redirect_url)

    response.set_cookie('admin_currency', currency, max_age=365*24*60*60, samesite='Lax')
    return response


def _to_bool(val, default=True):
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    return str(val).strip().lower() in ('1', 'true', 'yes', 'on')


def _clamp_int(val, low, high, default):
    try:
        return max(low, min(high, int(val)))
    except (TypeError, ValueError):
        return default


def _clamp_float(val, low, high, default):
    try:
        return max(low, min(high, round(float(val), 2)))
    except (TypeError, ValueError):
        return default


@require_http_methods(["GET", "POST"])
def admin_theme_customize_api(request):
    """Read, update, upload hero render video, or reset StorefrontThemeSettings."""
    theme = StorefrontThemeSettings.get_solo()

    if request.method == 'GET':
        return JsonResponse({'status': 'ok', 'settings': theme.to_dict()})

    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload.'}, status=400)
    else:
        payload = request.POST.dict()
        if 'payload' in payload:
            try:
                payload = {**payload, **json.loads(payload['payload'])}
            except json.JSONDecodeError:
                pass

    if payload.get('action') == 'reset':
        theme.delete()
        fresh = StorefrontThemeSettings.get_solo()
        return JsonResponse({'status': 'ok', 'message': 'Theme settings reset to Luckjary defaults.', 'settings': fresh.to_dict()})

    # Handle direct video upload when running on writable filesystem
    uploaded_video = request.FILES.get('hero_video_file')
    if uploaded_video:
        ext = os.path.splitext(uploaded_video.name)[1].lower()
        if ext not in ('.mp4', '.webm', '.mov'):
            return JsonResponse(
                {'status': 'error', 'message': 'Unsupported video format. Please upload .mp4, .webm, or .mov.'},
                status=400,
            )
        if os.environ.get('VERCEL'):
            return JsonResponse(
                {
                    'status': 'error',
                    'message': 'Direct file upload is disabled on Vercel read-only serverless runtime. Paste a hosted video URL (Vercel Blob / Cloudinary / S3) or upload locally before deploying.',
                },
                status=400,
            )

        target_name = f"hero-render{ext}"
        static_videos_dir = Path(settings.BASE_DIR) / 'static' / 'videos'
        static_videos_dir.mkdir(parents=True, exist_ok=True)
        static_file_path = static_videos_dir / target_name
        with open(static_file_path, 'wb+') as dest:
            for chunk in uploaded_video.chunks():
                dest.write(chunk)

        # Keep staticfiles/ synced as well for WhiteNoise / Vercel deploys
        staticfiles_videos_dir = Path(settings.STATIC_ROOT) / 'videos'
        staticfiles_videos_dir.mkdir(parents=True, exist_ok=True)
        staticfiles_file_path = staticfiles_videos_dir / target_name
        with open(static_file_path, 'rb') as src, open(staticfiles_file_path, 'wb') as dst:
            dst.write(src.read())

        served_url = f"/static/videos/{target_name}"
        if ext == '.webm':
            theme.hero_video_webm_url = served_url
        else:
            theme.hero_video_url = served_url

    if 'hero_video_enabled' in payload:
        theme.hero_video_enabled = _to_bool(payload.get('hero_video_enabled'), theme.hero_video_enabled)
    if 'hero_video_mode' in payload and payload.get('hero_video_mode') in ('scrub', 'autoplay'):
        theme.hero_video_mode = payload['hero_video_mode']
    if 'hero_video_url' in payload and not uploaded_video:
        theme.hero_video_url = str(payload.get('hero_video_url', '')).strip()[:500]
    if 'hero_video_webm_url' in payload and not (uploaded_video and uploaded_video.name.lower().endswith('.webm')):
        theme.hero_video_webm_url = str(payload.get('hero_video_webm_url', '')).strip()[:500]
    if 'hero_poster_url' in payload:
        theme.hero_poster_url = str(payload.get('hero_poster_url', '')).strip()[:500]

    if 'hero_scroll_height_vh' in payload:
        theme.hero_scroll_height_vh = _clamp_int(payload.get('hero_scroll_height_vh'), 150, 500, theme.hero_scroll_height_vh)
    if 'hero_scrub_smoothing' in payload:
        theme.hero_scrub_smoothing = _clamp_float(payload.get('hero_scrub_smoothing'), 0.04, 0.50, theme.hero_scrub_smoothing)
    if 'hero_video_opacity' in payload:
        theme.hero_video_opacity = _clamp_int(payload.get('hero_video_opacity'), 20, 100, theme.hero_video_opacity)
    if 'hero_vignette_strength' in payload:
        theme.hero_vignette_strength = _clamp_int(payload.get('hero_vignette_strength'), 0, 90, theme.hero_vignette_strength)
    if 'hero_fade_overlay_on_scroll' in payload:
        theme.hero_fade_overlay_on_scroll = _to_bool(payload.get('hero_fade_overlay_on_scroll'), theme.hero_fade_overlay_on_scroll)
    if 'hero_overlay_fade_start' in payload:
        theme.hero_overlay_fade_start = _clamp_int(payload.get('hero_overlay_fade_start'), 20, 95, theme.hero_overlay_fade_start)
    if 'hero_show_scroll_cue' in payload:
        theme.hero_show_scroll_cue = _to_bool(payload.get('hero_show_scroll_cue'), theme.hero_show_scroll_cue)
    if 'hero_show_progress_bar' in payload:
        theme.hero_show_progress_bar = _to_bool(payload.get('hero_show_progress_bar'), theme.hero_show_progress_bar)

    if 'hero_badge_text' in payload:
        theme.hero_badge_text = str(payload.get('hero_badge_text', '')).strip()[:120]
    if 'hero_title_line1' in payload:
        theme.hero_title_line1 = str(payload.get('hero_title_line1', '')).strip()[:120]
    if 'hero_title_line2' in payload:
        theme.hero_title_line2 = str(payload.get('hero_title_line2', '')).strip()[:120]
    if 'hero_subtitle' in payload:
        theme.hero_subtitle = str(payload.get('hero_subtitle', '')).strip()
    if 'hero_primary_cta_text' in payload:
        theme.hero_primary_cta_text = str(payload.get('hero_primary_cta_text', '')).strip()[:80]
    if 'hero_secondary_cta_text' in payload:
        theme.hero_secondary_cta_text = str(payload.get('hero_secondary_cta_text', '')).strip()[:80]

    if 'design_tokens' in payload and isinstance(payload['design_tokens'], dict):
        theme.design_tokens_json = payload['design_tokens']

    theme.save()
    return JsonResponse({
        'status': 'ok',
        'message': 'Theme Customize settings saved & published to homepage.',
        'settings': theme.to_dict(),
    })


