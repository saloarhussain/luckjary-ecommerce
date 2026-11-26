import json
import os
from pathlib import Path
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import OperationalError, ProgrammingError
from django.db.models import Q
from catalog.models import Product, Category, Collection
from .models import (
    NewsletterSubscriber,
    ContactInquiry,
    StorefrontThemeSettings,
    HeroVideoAsset,
    HeroVideoChunk,
    ensure_core_migrated,
)

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
        'spotlight_bento': theme_settings.get_spotlight_bento(),
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


def _apply_theme_payload(theme, payload, preserve_video_urls=False):
    if 'hero_video_enabled' in payload:
        theme.hero_video_enabled = _to_bool(payload.get('hero_video_enabled'), theme.hero_video_enabled)
    if 'hero_video_mode' in payload and payload.get('hero_video_mode') in ('scrub', 'autoplay'):
        theme.hero_video_mode = payload['hero_video_mode']
    if not preserve_video_urls:
        if 'hero_video_url' in payload:
            theme.hero_video_url = str(payload.get('hero_video_url', '')).strip()[:500]
        if 'hero_video_webm_url' in payload:
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

    existing_tokens = dict(theme.design_tokens_json or {})
    if 'design_tokens' in payload and isinstance(payload['design_tokens'], dict):
        saved_bento = existing_tokens.get('spotlight_bento')
        existing_tokens = dict(payload['design_tokens'])
        if saved_bento is not None:
            existing_tokens['spotlight_bento'] = saved_bento

    if 'spotlight_bento' in payload and isinstance(payload['spotlight_bento'], dict):
        existing_tokens['spotlight_bento'] = payload['spotlight_bento']

    theme.design_tokens_json = existing_tokens


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
        defaults = StorefrontThemeSettings()
        for field in StorefrontThemeSettings._meta.concrete_fields:
            if not field.primary_key and field.name != 'updated_at':
                setattr(theme, field.name, getattr(defaults, field.name))
        theme.save()
        return JsonResponse({'status': 'ok', 'message': 'Theme settings reset to Luckjary defaults.', 'settings': theme.to_dict()})

    # Legacy single-request upload fallback for small files (< 4 MB)
    uploaded_video = request.FILES.get('hero_video_file')
    if uploaded_video:
        ext = os.path.splitext(uploaded_video.name)[1].lower()
        if ext not in ('.mp4', '.webm', '.mov'):
            return JsonResponse(
                {'status': 'error', 'message': 'Unsupported video format. Please upload .mp4, .webm, or .mov.'},
                status=400,
            )
        raw_bytes = uploaded_video.read()
        mime = uploaded_video.content_type or ('video/webm' if ext == '.webm' else 'video/mp4')
        try:
            asset = HeroVideoAsset.objects.create(
                filename=uploaded_video.name[:255],
                content_type=mime,
                total_size=len(raw_bytes),
                total_chunks=1,
                is_complete=True,
            )
        except (ProgrammingError, OperationalError):
            ensure_core_migrated()
            asset = HeroVideoAsset.objects.create(
                filename=uploaded_video.name[:255],
                content_type=mime,
                total_size=len(raw_bytes),
                total_chunks=1,
                is_complete=True,
            )
        HeroVideoChunk.objects.create(asset=asset, index=0, data=raw_bytes)
        HeroVideoAsset.objects.exclude(pk=asset.pk).delete()
        served_url = f"/hero-video/{asset.id}/"
        if ext == '.webm':
            theme.hero_video_webm_url = served_url
        else:
            theme.hero_video_url = served_url
            if theme.hero_video_webm_url == '/static/videos/hero-render.webm':
                theme.hero_video_webm_url = ''

    _apply_theme_payload(theme, payload, preserve_video_urls=bool(uploaded_video))
    theme.save()
    return JsonResponse({
        'status': 'ok',
        'message': 'Theme Customize settings saved & published to homepage.',
        'settings': theme.to_dict(),
    })


@require_http_methods(["POST"])
def admin_hero_video_upload_init(request):
    """Initialize a chunked hero video upload (supports large files on Vercel)."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload.'}, status=400)

    filename = str(payload.get('filename', 'hero-render.mp4')).strip()[:255]
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.mp4', '.webm', '.mov'):
        return JsonResponse(
            {'status': 'error', 'message': 'Unsupported video format. Use .mp4, .webm, or .mov.'},
            status=400,
        )

    total_size = _clamp_int(payload.get('total_size'), 1, 80 * 1024 * 1024, 0)
    total_chunks = _clamp_int(payload.get('total_chunks'), 1, 200, 0)
    if total_size <= 0 or total_chunks <= 0:
        return JsonResponse(
            {'status': 'error', 'message': 'Video must be between 1 byte and 80 MB.'},
            status=400,
        )

    default_mime = 'video/webm' if ext == '.webm' else ('video/quicktime' if ext == '.mov' else 'video/mp4')
    content_type = str(payload.get('content_type') or default_mime).strip()[:100]

    try:
        asset = HeroVideoAsset.objects.create(
            filename=filename,
            content_type=content_type,
            total_size=total_size,
            total_chunks=total_chunks,
            is_complete=False,
        )
    except (ProgrammingError, OperationalError):
        ensure_core_migrated()
        asset = HeroVideoAsset.objects.create(
            filename=filename,
            content_type=content_type,
            total_size=total_size,
            total_chunks=total_chunks,
            is_complete=False,
        )

    return JsonResponse({'status': 'ok', 'asset_id': asset.id})


@require_http_methods(["POST"])
def admin_hero_video_upload_chunk(request):
    """Store one binary chunk (<= 1.5 MiB) of a HeroVideoAsset."""
    asset_id = request.POST.get('asset_id')
    index = request.POST.get('index')
    chunk_file = request.FILES.get('chunk')
    if not asset_id or index is None or not chunk_file:
        return JsonResponse({'status': 'error', 'message': 'Missing chunk parameters.'}, status=400)

    asset = get_object_or_404(HeroVideoAsset, pk=asset_id)
    idx = _clamp_int(index, 0, asset.total_chunks - 1, -1)
    if idx < 0:
        return JsonResponse({'status': 'error', 'message': 'Invalid chunk index.'}, status=400)

    HeroVideoChunk.objects.update_or_create(
        asset=asset,
        index=idx,
        defaults={'data': chunk_file.read()},
    )
    return JsonResponse({'status': 'ok', 'index': idx})


@require_http_methods(["POST"])
def admin_hero_video_upload_complete(request):
    """Finalize chunked upload, prune older video assets, and publish to StorefrontThemeSettings."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload.'}, status=400)

    asset_id = payload.get('asset_id')
    asset = get_object_or_404(HeroVideoAsset, pk=asset_id)
    received = asset.chunks.count()
    if received < asset.total_chunks:
        return JsonResponse(
            {'status': 'error', 'message': f'Upload incomplete ({received}/{asset.total_chunks} chunks).'},
            status=400,
        )

    asset.is_complete = True
    asset.save(update_fields=['is_complete'])
    HeroVideoAsset.objects.exclude(pk=asset.pk).delete()

    theme = StorefrontThemeSettings.get_solo()
    served_url = f"/hero-video/{asset.id}/"
    ext = os.path.splitext(asset.filename)[1].lower()
    if ext == '.webm':
        theme.hero_video_webm_url = served_url
    else:
        theme.hero_video_url = served_url
        if theme.hero_video_webm_url == '/static/videos/hero-render.webm':
            theme.hero_video_webm_url = ''
    theme.hero_video_enabled = True

    if isinstance(payload.get('theme_payload'), dict):
        _apply_theme_payload(theme, payload['theme_payload'], preserve_video_urls=True)
    theme.save()

    return JsonResponse({
        'status': 'ok',
        'message': 'Render video uploaded & published to homepage!',
        'settings': theme.to_dict(),
    })


@require_http_methods(["GET", "HEAD"])
def serve_hero_video(request, asset_id):
    """Stream DB-stored HeroVideoAsset with HTTP 206 Partial Content byte-ranges (<= 2 MiB per response)."""
    try:
        asset = get_object_or_404(HeroVideoAsset, pk=asset_id, is_complete=True)
    except (ProgrammingError, OperationalError):
        ensure_core_migrated()
        asset = get_object_or_404(HeroVideoAsset, pk=asset_id, is_complete=True)

    total = int(asset.total_size)
    if total <= 0:
        return HttpResponse(status=404)

    if request.method == 'HEAD':
        resp = HttpResponse(status=200, content_type=asset.content_type)
        resp['Content-Length'] = str(total)
        resp['Accept-Ranges'] = 'bytes'
        resp['Cache-Control'] = 'public, max-age=86400'
        return resp

    max_slice = 2 * 1024 * 1024  # 2 MiB cap keeps every response well under Vercel's 4.5 MB limit
    range_header = request.headers.get('Range', '').strip()

    start = 0
    end = min(total - 1, max_slice - 1)
    status_code = 206 if (range_header or total > max_slice) else 200

    if range_header.startswith('bytes='):
        spec = range_header[6:].split(',')[0].strip()
        start_str, _, end_str = spec.partition('-')
        try:
            if start_str == '':
                suffix_len = int(end_str)
                start = max(0, total - suffix_len)
                end = total - 1
            else:
                start = int(start_str)
                end = int(end_str) if end_str else total - 1
        except ValueError:
            return HttpResponse(status=416)

        if start >= total or start < 0 or end < start:
            resp = HttpResponse(status=416)
            resp['Content-Range'] = f'bytes */{total}'
            return resp

        end = min(end, total - 1, start + max_slice - 1)
        status_code = 206

    chunk_size = HeroVideoAsset.CHUNK_SIZE
    first_idx = start // chunk_size
    last_idx = end // chunk_size
    chunks = HeroVideoChunk.objects.filter(
        asset=asset,
        index__gte=first_idx,
        index__lte=last_idx,
    ).order_by('index')

    parts = []
    for c in chunks:
        c_start = c.index * chunk_size
        raw = bytes(c.data)
        slice_start = max(0, start - c_start)
        slice_end = min(len(raw), end - c_start + 1)
        if slice_start < slice_end:
            parts.append(raw[slice_start:slice_end])

    body = b''.join(parts)
    resp = HttpResponse(body, status=status_code, content_type=asset.content_type)
    resp['Accept-Ranges'] = 'bytes'
    resp['Content-Length'] = str(len(body))
    resp['Cache-Control'] = 'public, max-age=86400'
    if status_code == 206:
        resp['Content-Range'] = f'bytes {start}-{start + len(body) - 1}/{total}'
    return resp


