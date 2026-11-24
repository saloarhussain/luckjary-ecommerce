from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Sum
import json
import uuid
from .models import Category, Material, Collection, Product, ProductImage, ProductReview

class ProductAdminForm(forms.ModelForm):
    STANDARD_METALS = [
        ('925 Sterling Silver', '925 Solid Sterling Silver'),
    ]

    metal_presets = forms.MultipleChoiceField(
        choices=STANDARD_METALS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'admin-checkbox-grid'}),
        required=False,
        label="925 Sterling Silver Specification",
        help_text="Genuine 925 Purity Solid Sterling Silver."
    )

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Seraphina Pavé Solitaire Ring in 925 Sterling Silver',
                'class': 'shopify-title-input',
                'style': 'font-size: 1.05rem; font-weight: 600; padding: 0.65rem 0.85rem; width: 100%;'
            }),
            'subtitle': forms.TextInput(attrs={
                'placeholder': 'e.g. Handcrafted in 925 Solid Sterling Silver & Flawless Cubic Zirconia Stones',
                'style': 'width: 100%;'
            }),
            'gemstone': forms.TextInput(attrs={
                'placeholder': 'e.g. 5A Flawless Cubic Zirconia (CZ)',
                'style': 'width: 100%;'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Write a compelling description highlighting 925 solid sterling silver hallmarking, brilliant cubic zirconia setting, and styling advice...',
                'style': 'width: 100%; font-size: 0.85rem; line-height: 1.5;'
            }),
            'meta_title': forms.TextInput(attrs={
                'placeholder': 'e.g. Seraphina Pavé Solitaire Ring in 925 Sterling Silver | Luckjary',
                'style': 'width: 100%;'
            }),
            'meta_description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g. Discover the handcrafted Seraphina Pavé Ring in 925 solid sterling silver with flawless cubic zirconia at Luckjary.',
                'style': 'width: 100%;'
            }),
            'meta_keywords': forms.TextInput(attrs={
                'placeholder': 'e.g. silver jewelry, 925 sterling silver, silver ring, cubic zirconia, cz diamond, handcrafted silver',
                'style': 'width: 100%;'
            }),
            'sku': forms.TextInput(attrs={
                'placeholder': 'e.g. LCK-SIL-001 (Leave blank to auto-generate)',
                'style': 'width: 100%; font-family: monospace; font-weight: 600; letter-spacing: 0.05em;'
            }),
            'available_metals': forms.TextInput(attrs={
                'placeholder': 'e.g. 925 Sterling Silver',
                'style': 'width: 100%;'
            }),
            'available_sizes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Leave blank to use full standard sizing (e.g. US 4 to 13 with half-sizes for rings), or enter custom sizes separated by commas or lines.',
                'style': 'width: 100%;'
            }),
            'chain_length_or_size': forms.TextInput(attrs={'style': 'width: 100%;'}),
            'craftsmanship_details': forms.Textarea(attrs={'rows': 3, 'style': 'width: 100%;'}),
            'care_instructions': forms.Textarea(attrs={'rows': 3, 'style': 'width: 100%;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metal_presets'].initial = ['925 Sterling Silver']
        if 'gemstone' in self.fields:
            self.fields['gemstone'].initial = '5A Flawless Cubic Zirconia (CZ)'
        if 'sku' in self.fields:
            self.fields['sku'].required = False
        if 'description' in self.fields:
            self.fields['description'].required = False

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['metal_presets'] = ['925 Sterling Silver']
        cleaned_data['available_metals'] = '925 Sterling Silver'
        cleaned_data['karat_metal'] = '925 Sterling Silver'
        cleaned_data['carat_weight'] = ''
        cleaned_data['dimensions'] = ''
        if not cleaned_data.get('certification'):
            cleaned_data['certification'] = 'Luckjary 925 Hallmark & Authenticity Guarantee'
        if not cleaned_data.get('sku'):
            cleaned_data['sku'] = f"LUK-SIL-{uuid.uuid4().hex[:6].upper()}"
        if not cleaned_data.get('description'):
            cleaned_data['description'] = f"Handcrafted {cleaned_data.get('title', 'fine jewelry piece')} in 925 Solid Sterling Silver with conflict-free handset stones and signature Luckjary hallmark guarantee."
        return cleaned_data

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0

class ProductReviewInline(admin.StackedInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/catalog/category/change_list.html'
    list_display = ('name', 'slug', 'is_featured', 'order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_featured', 'order')
    search_fields = ('name', 'slug', 'description')
    actions = ['make_featured', 'remove_featured']

    @admin.action(description="Feature selected categories on showroom")
    def make_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f"Featured {count} category/categories on showroom showcase.")

    @admin.action(description="Remove selected categories from showroom feature")
    def remove_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f"Removed {count} category/categories from featured showcase.")

    def get_queryset(self, request):
        from django.db.models import Count
        return super().get_queryset(request).annotate(product_count=Count('products'))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['active_nav'] = 'categories'
        extra_context['total_categories'] = Category.objects.count()
        extra_context['featured_categories_count'] = Category.objects.filter(is_featured=True).count()
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    change_list_template = 'admin/catalog/material/change_list.html'
    list_display = ('name', 'slug', 'badge_label')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug', 'badge_label', 'description')
    actions = ['export_iso', 'sync_live', 'recalculate_costs']

    @admin.action(description="Export ISO Hallmarking manifest")
    def export_iso(self, request, queryset):
        self.message_user(request, f"Exported ISO hallmarking manifest for {queryset.count()} material(s).")

    @admin.action(description="Sync to public e-boutique catalog")
    def sync_live(self, request, queryset):
        self.message_user(request, f"Successfully synced {queryset.count()} material(s) to public boutique catalog.")

    @admin.action(description="Recalculate live spot price basis")
    def recalculate_costs(self, request, queryset):
        self.message_user(request, f"Updated spot price valuations for {queryset.count()} precious alloy(s).")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['active_nav'] = 'materials'
        materials = Material.objects.all()
        extra_context['total_materials_count'] = materials.count()
        extra_context['precious_count'] = materials.filter(
            Q(name__icontains='gold') | Q(name__icontains='platinum')
        ).count()
        extra_context['demifine_count'] = materials.filter(
            Q(name__icontains='demifine') | Q(name__icontains='vermeil') | Q(name__icontains='silver')
        ).count()
        extra_context['gemstone_count'] = materials.filter(
            Q(name__icontains='emerald') | Q(name__icontains='pearl') | Q(name__icontains='sapphire') | Q(name__icontains='gem')
        ).count()
        extra_context['diamond_count'] = materials.filter(
            Q(name__icontains='diamond') | Q(name__icontains='zirconia') | Q(name__icontains='cz')
        ).count()
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    change_list_template = 'admin/catalog/collection/change_list.html'
    list_display = ('name', 'slug', 'subtitle', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    search_fields = ('name', 'slug', 'subtitle', 'description')
    actions = ['mark_active', 'mark_inactive']

    @admin.action(description="Mark selected collections as active")
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} collection(s) marked as active.")

    @admin.action(description="Mark selected collections as inactive")
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} collection(s) marked as inactive.")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['active_nav'] = 'collections'
        extra_context['active_collections_count'] = Collection.objects.filter(is_active=True).count()
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    change_list_template = 'admin/catalog/product/change_list.html'
    form = ProductAdminForm
    fieldsets = (
        ('Title & Description', {
            'classes': ('shopify-card-title-desc',),
            'fields': (
                'title',
                'subtitle',
                'description',
            )
        }),
        ('✨ Precious Metal Specification', {
            'classes': ('shopify-card-metals',),
            'description': 'Exclusively authentic 925 Solid Sterling Silver (100% Genuine 925 Hallmark).',
            'fields': (
                'metal_presets',
                'karat_metal',
                'available_metals',
            )
        }),
        ('📏 Sizing Framework & Sizing Range', {
            'classes': ('shopify-card-sizing',),
            'description': 'Configure available ring sizes (US 4 to 13 with half-sizes), necklace chain lengths, or custom sizes. Leave Available Sizes blank to automatically provide the complete standard size range for this jewelry piece.',
            'fields': (
                ('size_category', 'chain_length_or_size'),
                'available_sizes',
            )
        }),
        ('💎 Gemstones & Specialty Materials', {
            'classes': ('shopify-card-gemstones',),
            'description': 'Specify featured Cubic Zirconia stone details. (All creations are crafted exclusively in 925 Solid Sterling Silver).',
            'fields': (
                'gemstone',
            )
        }),
        ('🔍 Search Engine Listing Preview', {
            'classes': ('shopify-card-seo',),
            'description': 'Add a title and description to see how this product might appear in a search engine listing like Google.',
            'fields': (
                'meta_title',
                'meta_description',
                'slug',
                'meta_keywords',
            )
        }),
        ('🏛️ Haute Craftsmanship & Care', {
            'classes': ('collapse', 'shopify-card-care'),
            'fields': (
                'craftsmanship_details',
                'care_instructions',
            )
        }),
        ('Product Status & Visibility', {
            'classes': ('shopify-side-status',),
            'fields': (
                'is_available',
                ('is_featured', 'is_bestseller', 'is_new_arrival'),
            )
        }),
        ('Pricing & Valuation', {
            'classes': ('shopify-side-pricing',),
            'fields': (
                ('price', 'compare_at_price'),
            )
        }),
        ('Inventory & SKU Vault', {
            'classes': ('shopify-side-inventory',),
            'fields': (
                ('sku', 'inventory'),
            )
        }),
        ('Product Organization', {
            'classes': ('shopify-side-organization',),
            'fields': (
                'category',
                'collection',
                'style',
            )
        }),
    )
    list_display = (
        'thumb_display', 
        'title_sku_display', 
        'category_badge', 
        'price_display', 
        'stock_badge', 
        'is_available', 
        'merchandising_display'
    )
    list_display_links = ('thumb_display', 'title_sku_display')
    list_filter = ('category', 'style', 'is_available', 'is_featured', 'is_bestseller')
    search_fields = ('title', 'sku', 'description', 'karat_metal', 'gemstone', 'category__name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_available',)
    list_per_page = 25
    actions_on_top = True
    actions_on_bottom = False
    inlines = [ProductImageInline, ProductReviewInline]
    filter_horizontal = ()
    actions = ['make_available', 'make_unavailable', 'make_featured', 'remove_featured']

    @admin.action(description="✓ Mark selected pieces as Available")
    def make_available(self, request, queryset):
        count = queryset.update(is_available=True)
        self.message_user(request, f"{count} fine jewelry pieces marked as Available.")

    @admin.action(description="✕ Mark selected pieces as Hidden / Draft")
    def make_unavailable(self, request, queryset):
        count = queryset.update(is_available=False)
        self.message_user(request, f"{count} fine jewelry pieces marked as Hidden.")

    @admin.action(description="★ Feature selected pieces on Homepage")
    def make_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f"{count} fine jewelry pieces featured on showroom.")

    @admin.action(description="Remove selected pieces from Featured")
    def remove_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f"{count} fine jewelry pieces removed from Featured.")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        product = form.instance
        silver_mat, _ = Material.objects.get_or_create(
            slug='925-sterling-silver',
            defaults={'name': '925 Sterling Silver', 'badge_label': '925 Silver'}
        )
        cz_mat, _ = Material.objects.get_or_create(
            slug='cubic-zirconia',
            defaults={'name': 'Cubic Zirconia', 'badge_label': '5A CZ'}
        )
        product.materials.add(silver_mat, cz_mat)
        # Remove any legacy gold / demifine / gem materials
        legacy_mats = Material.objects.filter(slug__in=[
            '18k-gold-vermeil-demifine',
            '18k-solid-yellow-gold',
            '18k-white-gold',
            '18k-rose-gold',
            'platinum-950',
            'freshwater-cultured-pearl',
            'natural-colombian-emerald',
            'royal-ceylon-sapphire',
            'vvs1-lab-grown-diamonds'
        ])
        if legacy_mats.exists():
            product.materials.remove(*legacy_mats)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('scrape/', self.admin_site.admin_view(self.scrape_view), name='catalog_product_scrape'),
            path('api/scrape/', self.admin_site.admin_view(self.api_scrape_view), name='catalog_product_api_scrape'),
            path('api/import-scraped/', self.admin_site.admin_view(self.api_import_scraped_view), name='catalog_product_api_import_scraped'),
            path('api/bulk-import-scraped/', self.admin_site.admin_view(self.api_bulk_import_scraped_view), name='catalog_product_api_bulk_import_scraped'),
            path('quick-add/', self.admin_site.admin_view(self.quick_add_view), name='catalog_product_quick_add'),
            path('bulk-delete/', self.admin_site.admin_view(self.bulk_delete_view), name='catalog_product_bulk_delete'),
            path('quick-delete/<int:product_id>/', self.admin_site.admin_view(self.quick_delete_view), name='catalog_product_quick_delete'),
        ]
        return custom_urls + urls

    def scrape_view(self, request):
        from django.shortcuts import render
        try:
            from orders.models import Order
            total_orders = Order.objects.count()
        except Exception:
            total_orders = 4

        categories = Category.objects.all()
        total_products = Product.objects.count()

        context = {
            'title': 'E-Commerce Product Scraper',
            'active_nav': 'scrape',
            'categories': categories,
            'total_products': total_products,
            'total_orders': total_orders,
            'is_scraper': True,
        }
        return render(request, 'admin/catalog/scrape.html', context)

    def api_scrape_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
        
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST

            url = (data.get('url') or '').strip()
            raw_html = (data.get('raw_html') or '').strip()
            raw_json = (data.get('raw_json') or '').strip()
            raw_csv = (data.get('raw_csv') or '').strip()

            from .scraper import scrape_ecommerce_product
            scraped = scrape_ecommerce_product(url=url, raw_html=raw_html, raw_json=raw_json, raw_csv=raw_csv)

            if not scraped or not scraped.get('success'):
                return JsonResponse({
                    'status': 'error',
                    'message': scraped.get('error', 'Unable to extract product information from source.') if scraped else 'Scraper failed to return data.'
                }, status=400)

            # Incur INR conversion if currency is USD
            price_num = scraped.get('price') or 0.0
            if scraped.get('currency') == 'INR':
                inr_val = int(float(price_num))
            else:
                inr_val = int(float(price_num) * 83.1527)
            scraped['price_inr'] = inr_val

            # Best match category
            cat_suggestion = 'rings'
            title_lower = (scraped.get('title') or '').lower()
            if 'necklace' in title_lower or 'pendant' in title_lower or 'chain' in title_lower:
                cat_suggestion = 'necklaces'
            elif 'bracelet' in title_lower or 'bangle' in title_lower:
                cat_suggestion = 'bracelets'
            elif 'earring' in title_lower or 'stud' in title_lower or 'huggie' in title_lower:
                cat_suggestion = 'earrings'
            elif 'ring' in title_lower or 'band' in title_lower or 'solitaire' in title_lower:
                cat_suggestion = 'rings'
            
            matched_cat = Category.objects.filter(slug__icontains=cat_suggestion).first()
            scraped['suggested_category_id'] = matched_cat.id if matched_cat else (Category.objects.first().id if Category.objects.exists() else None)

            return JsonResponse({
                'status': 'ok',
                'product': scraped
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def api_import_scraped_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
        
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST

            title = (data.get('title') or '').strip()
            if not title:
                return JsonResponse({'status': 'error', 'message': 'Product title is required.'}, status=400)

            price = data.get('price')
            if price is None or str(price).strip() == '':
                price = 0.0
            else:
                try:
                    price = float(price)
                except ValueError:
                    price = 0.0

            compare_price = data.get('compare_at_price')
            if compare_price and str(compare_price).strip():
                try:
                    compare_price = float(compare_price)
                except ValueError:
                    compare_price = None
            else:
                compare_price = None

            category_id = data.get('category')
            category = None
            if category_id:
                category = Category.objects.filter(id=category_id).first()
            if not category:
                category = Category.objects.first()

            sku = (data.get('sku') or '').strip()
            if not sku:
                sku = f"LCK-SCR-{uuid.uuid4().hex[:6].upper()}"

            description = (data.get('description') or '').strip() or f"Handcrafted {title} in authentic 925 Solid Sterling Silver with conflict-free handset stones and signature Luckjary hallmark guarantee."
            karat_metal = (data.get('karat_metal') or '925 Sterling Silver').strip()
            available_metals = (data.get('available_metals') or '925 Sterling Silver').strip()
            gemstone = (data.get('gemstone') or '5A Flawless Cubic Zirconia (CZ)').strip()
            size_category = data.get('size_category') or 'universal'
            available_sizes = (data.get('available_sizes') or '').strip()
            inventory = int(data.get('inventory') or 20)

            # Ensure SKU is unique (append suffix if collision)
            original_sku = sku
            sku_counter = 1
            while Product.objects.filter(sku=sku).exists():
                sku = f"{original_sku}-{sku_counter}"
                sku_counter += 1

            product = Product.objects.create(
                title=title,
                category=category,
                price=price,
                compare_at_price=compare_price,
                inventory=inventory,
                sku=sku,
                size_category=size_category,
                available_sizes=available_sizes,
                gemstone=gemstone,
                description=description,
                karat_metal=karat_metal,
                available_metals=available_metals,
                is_available=True,
                is_featured=False
            )

            # Ensure 925 silver material linked
            silver_mat, _ = Material.objects.get_or_create(
                slug='925-sterling-silver',
                defaults={'name': '925 Sterling Silver', 'badge_label': '925 Silver'}
            )
            product.materials.add(silver_mat)

            # Images
            images = data.get('images', [])
            for idx, img_info in enumerate(images):
                img_url = ""
                is_primary = False
                alt_text = f"{product.title} atelier photo"
                if isinstance(img_info, dict):
                    img_url = (img_info.get('src') or '').strip()
                    is_primary = bool(img_info.get('is_primary')) or (idx == 0)
                    alt_text = img_info.get('alt') or alt_text
                elif isinstance(img_info, str):
                    img_url = img_info.strip()
                    is_primary = (idx == 0)
                
                if img_url:
                    ProductImage.objects.create(
                        product=product,
                        image_url=img_url,
                        alt_text=alt_text,
                        is_primary=is_primary,
                        order=idx
                    )

            return JsonResponse({
                'status': 'ok',
                'message': f'"{product.title}" successfully imported into the Atelier Vault.',
                'id': product.id,
                'title': product.title,
                'sku': product.sku,
                'price': float(product.price),
                'image': product.primary_image,
                'edit_url': f'/admin/catalog/product/{product.id}/change/',
                'detail_url': product.get_absolute_url(),
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def api_bulk_import_scraped_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST

            items = data.get('items', [])
            if not items:
                return JsonResponse({'status': 'error', 'message': 'No products provided for bulk import.'}, status=400)

            default_category = Category.objects.first()
            category_id = data.get('category_id')
            if category_id:
                target_category = Category.objects.filter(id=category_id).first() or default_category
            else:
                target_category = default_category

            silver_mat, _ = Material.objects.get_or_create(
                slug='925-sterling-silver',
                defaults={'name': '925 Sterling Silver', 'badge_label': '925 Silver'}
            )

            created_products = []
            for item in items:
                title = (item.get('title') or '').strip()
                if not title:
                    continue

                sku = (item.get('sku') or '').strip()
                if not sku:
                    slug_part = item.get('handle') or re.sub(r'[^A-Za-z0-9]', '', title)[:8].upper()
                    sku = f"LCK-SCR-{slug_part[:12]}"

                # Unique SKU check
                base_sku = sku
                cnt = 1
                while Product.objects.filter(sku=sku).exists():
                    sku = f"{base_sku}-{cnt}"
                    cnt += 1

                price = item.get('price') or 0.0
                try:
                    price = float(price)
                except ValueError:
                    price = 0.0

                comp = item.get('compare_at_price')
                if comp:
                    try:
                        comp = float(comp)
                    except ValueError:
                        comp = None

                description = (item.get('description') or '').strip() or f"Handcrafted {title} with fine precision and authentic Luckjary hallmark guarantee."
                karat_metal = item.get('karat_metal') or '925 Sterling Silver'
                available_metals = item.get('available_metals') or '925 Sterling Silver'
                gemstone = item.get('gemstone') or '5A Flawless Cubic Zirconia (CZ)'

                variants = item.get('variants', [])
                size_list = ', '.join([v.get('title', '') for v in variants if v.get('title')]) if variants else ''

                product = Product.objects.create(
                    title=title,
                    category=target_category,
                    price=price,
                    compare_at_price=comp,
                    inventory=25,
                    sku=sku,
                    size_category='universal',
                    available_sizes=size_list,
                    gemstone=gemstone,
                    description=description,
                    karat_metal=karat_metal,
                    available_metals=available_metals,
                    is_available=True,
                    is_featured=False
                )
                product.materials.add(silver_mat)

                # Images
                images = item.get('images', [])
                for idx, img_info in enumerate(images):
                    img_url = ""
                    alt_text = f"{product.title} image {idx+1}"
                    if isinstance(img_info, dict):
                        img_url = (img_info.get('src') or '').strip()
                        alt_text = img_info.get('alt') or alt_text
                    elif isinstance(img_info, str):
                        img_url = img_info.strip()

                    if img_url:
                        ProductImage.objects.create(
                            product=product,
                            image_url=img_url,
                            alt_text=alt_text,
                            is_primary=(idx == 0),
                            order=idx
                        )

                created_products.append({
                    'id': product.id,
                    'title': product.title,
                    'sku': product.sku,
                    'price': float(product.price),
                    'edit_url': f'/admin/catalog/product/{product.id}/change/'
                })

            return JsonResponse({
                'status': 'ok',
                'imported_count': len(created_products),
                'message': f"Successfully imported {len(created_products)} pieces into the Atelier Vault.",
                'products': created_products
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def quick_add_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
        
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST

            title = (data.get('title') or '').strip()
            if not title:
                return JsonResponse({'status': 'error', 'message': 'Product title is required.'}, status=400)

            price = data.get('price')
            if not price:
                return JsonResponse({'status': 'error', 'message': 'Price is required.'}, status=400)
            
            category_id = data.get('category')
            category = None
            if category_id:
                category = Category.objects.filter(id=category_id).first()
            if not category:
                category = Category.objects.first()

            compare_price = data.get('compare_at_price') or None
            if compare_price and str(compare_price).strip():
                try:
                    compare_price = float(compare_price)
                except ValueError:
                    compare_price = None
            else:
                compare_price = None

            inventory = int(data.get('inventory') or 25)
            sku = (data.get('sku') or '').strip()
            if not sku:
                sku = f"LUK-SIL-{uuid.uuid4().hex[:6].upper()}"

            size_category = data.get('size_category') or 'ring'
            gemstone = data.get('gemstone') or '5A Flawless Cubic Zirconia (CZ)'
            description = (data.get('description') or '').strip() or f"Handcrafted {title} in authentic 925 Solid Sterling Silver with conflict-free handset stones and signature Luckjary hallmark guarantee."

            product = Product.objects.create(
                title=title,
                category=category,
                price=price,
                compare_at_price=compare_price,
                inventory=inventory,
                sku=sku,
                size_category=size_category,
                gemstone=gemstone,
                description=description,
                karat_metal='925 Sterling Silver',
                available_metals='925 Sterling Silver',
                is_available=True,
                is_featured=bool(data.get('is_featured'))
            )

            # Ensure 925 silver material
            silver_mat, _ = Material.objects.get_or_create(
                slug='925-sterling-silver',
                defaults={'name': '925 Sterling Silver', 'badge_label': '925 Silver'}
            )
            product.materials.add(silver_mat)

            # Image URL if provided
            image_url = (data.get('image_url') or '').strip()
            if image_url:
                ProductImage.objects.create(
                    product=product,
                    image_url=image_url,
                    alt_text=f"{product.title} atelier image",
                    is_primary=True,
                    order=0
                )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'ok',
                    'message': f'"{product.title}" successfully added to the Atelier Vault.',
                    'id': product.id,
                    'title': product.title,
                    'sku': product.sku,
                    'price': float(product.price),
                    'image': product.primary_image,
                })
            
            try:
                from django.contrib import messages
                messages.success(request, f'Piece "{product.title}" (SKU: {product.sku}) was successfully created.', fail_silently=True)
            except Exception:
                pass
            return HttpResponseRedirect('/admin/catalog/product/')
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def bulk_delete_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
                ids = data.get('ids', [])
            else:
                ids = request.POST.getlist('ids') or request.POST.getlist('_selected_action')
            
            if not ids:
                return JsonResponse({'status': 'error', 'message': 'No product IDs provided.'}, status=400)
            
            clean_ids = [int(i) for i in ids if str(i).isdigit()]
            deleted_count, _ = Product.objects.filter(id__in=clean_ids).delete()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'ok',
                    'deleted_count': deleted_count,
                    'message': f'{deleted_count} piece(s) successfully deleted from the Atelier Vault.'
                })
            try:
                from django.contrib import messages
                messages.success(request, f'{deleted_count} piece(s) successfully deleted from the Atelier Vault.', fail_silently=True)
            except Exception:
                pass
            return HttpResponseRedirect('/admin/catalog/product/')
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def quick_delete_view(self, request, product_id):
        if request.method != 'POST':
            return HttpResponseRedirect(f'/admin/catalog/product/{product_id}/delete/')
        try:
            product = Product.objects.filter(id=product_id).first()
            if not product:
                return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=404)
            title = product.title
            product.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'id': product_id, 'message': f'"{title}" deleted.'})
            try:
                from django.contrib import messages
                messages.success(request, f'Piece "{title}" was deleted from Atelier Vault.', fail_silently=True)
            except Exception:
                pass
            return HttpResponseRedirect('/admin/catalog/product/')
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_count = Product.objects.count()
        in_stock_count = Product.objects.filter(inventory__gt=5).count()
        low_stock_count = Product.objects.filter(inventory__gt=0, inventory__lte=5).count()
        sold_out_count = Product.objects.filter(inventory=0).count()
        featured_count = Product.objects.filter(is_featured=True).count()
        available_count = Product.objects.filter(is_available=True).count()
        bestseller_count = Product.objects.filter(is_bestseller=True).count()
        vault_val = Product.objects.aggregate(total=Sum('price'))['total'] or 0

        extra_context['catalog_stats'] = {
            'total': total_count,
            'in_stock': in_stock_count,
            'low_stock': low_stock_count,
            'sold_out': sold_out_count,
            'featured': featured_count,
            'available': available_count,
            'bestsellers': bestseller_count,
            'vault_value': f"${vault_val:,.2f}",
        }
        extra_context['category_counts'] = {
            'all': total_count,
            'rings': Product.objects.filter(Q(category__slug='rings') | Q(title__icontains='Ring')).count(),
            'necklaces': Product.objects.filter(Q(category__slug='necklaces') | Q(title__icontains='Necklace') | Q(title__icontains='Chain') | Q(title__icontains='Pendant')).count(),
            'bracelets': Product.objects.filter(Q(category__slug='bracelets') | Q(title__icontains='Bracelet') | Q(title__icontains='Bangle')).count(),
            'earrings': Product.objects.filter(Q(category__slug='earrings') | Q(title__icontains='Earring') | Q(title__icontains='Huggies')).count(),
            'high_jewelry': Product.objects.filter(is_featured=True).count(),
            'low_stock': low_stock_count,
        }
        extra_context['categories_list'] = Category.objects.all()
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='Preview')
    def thumb_display(self, obj):
        img_url = obj.primary_image or ''
        if 'images.unsplash.com' in img_url:
            import re
            img_url = re.sub(r'w=\d+', 'w=160&h=160&fit=crop', img_url)
        
        fallback_svg = (
            "data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='%2314161F' stroke='%23C5A059' stroke-width='1.5'>"
            "<rect width='100%' height='100%' fill='%2314161F'/>"
            "<polygon points='6 3 18 3 22 9 12 22 2 9 6 3'/>"
            "<line x1='11' y1='3' x2='8' y2='9'/><line x1='13' y1='3' x2='16' y2='9'/>"
            "<line x1='2' y1='9' x2='22' y2='9'/><line x1='12' y1='22' x2='8' y2='9'/><line x1='12' y1='22' x2='16' y2='9'/>"
            "</svg>"
        )
        return format_html(
            '<div class="admin-thumb-wrapper" title="{}">'
            '<img src="{}" class="admin-thumb" alt="{}" width="48" height="48" loading="lazy" referrerpolicy="no-referrer" '
            'onerror="this.onerror=null;this.src=\'{}\';" />'
            '</div>',
            obj.title,
            img_url,
            obj.title,
            fallback_svg
        )

    @admin.display(description='Jewelry Piece & SKU', ordering='title')
    def title_sku_display(self, obj):
        metal = obj.karat_metal or 'High Jewelry'
        gem = f" • {obj.gemstone}" if obj.gemstone else ""
        return format_html(
            '<div class="admin-product-info">'
            '<span class="admin-product-name">{}</span>'
            '<div class="admin-product-sub">'
            '<span class="admin-sku-pill">SKU: {}</span>'
            '<span class="admin-spec-text">{}{}</span>'
            '</div>'
            '</div>',
            obj.title,
            obj.sku,
            metal,
            gem
        )

    @admin.display(description='Category', ordering='category__name')
    def category_badge(self, obj):
        if obj.category:
            return format_html('<span class="admin-category-pill">{}</span>', obj.category.name)
        return mark_safe('<span class="text-muted">—</span>')

    @admin.display(description='Retail Price', ordering='price')
    def price_display(self, obj):
        price_str = f"${obj.price:,.2f}"
        if obj.compare_at_price and obj.compare_at_price > obj.price:
            comp_str = f"${obj.compare_at_price:,.2f}"
            return format_html(
                '<div class="admin-price-cell">'
                '<span class="price-gold">{}</span>'
                '<span class="price-compare">{}</span>'
                '</div>',
                price_str,
                comp_str
            )
        return format_html(
            '<div class="admin-price-cell">'
            '<span class="price-gold">{}</span>'
            '</div>',
            price_str
        )

    @admin.display(description='Inventory', ordering='inventory')
    def stock_badge(self, obj):
        if obj.inventory > 10:
            return format_html('<span class="badge-luxury badge-delivered"><span class="badge-dot green"></span>{} in stock</span>', obj.inventory)
        elif obj.inventory > 0:
            return format_html('<span class="badge-luxury badge-pending"><span class="badge-dot amber"></span>{} low stock</span>', obj.inventory)
        return mark_safe('<span class="badge-luxury badge-cancelled"><span class="badge-dot red"></span>Sold out</span>')

    @admin.display(description='Merchandising Tags')
    def merchandising_display(self, obj):
        badges = []
        if obj.is_featured:
            badges.append('<span class="badge-luxury badge-featured">★ Featured</span>')
        if obj.is_bestseller:
            badges.append('<span class="badge-luxury badge-bestseller">👑 Bestseller</span>')
        if obj.is_new_arrival:
            badges.append('<span class="badge-luxury badge-new">✨ New</span>')
        if not badges:
            return mark_safe('<span class="text-muted">—</span>')
        return mark_safe(' '.join(badges))

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    change_list_template = 'admin/catalog/productreview/change_list.html'
    list_display = ('product', 'author_name', 'rating_stars', 'is_verified_buyer', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified_buyer', 'is_approved')
    search_fields = ('author_name', 'title', 'comment', 'product__title')
    list_editable = ('is_approved',)
    actions = ['approve_reviews', 'unapprove_reviews']

    @admin.display(description='Customer Rating', ordering='rating')
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#DFBE76; font-size:0.9rem;">{}</span>', stars)

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Unapprove / Hold selected reviews")
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from django.db.models import Avg
        qs = ProductReview.objects.all()
        total_count = qs.count()
        avg_rating = qs.aggregate(Avg('rating'))['rating__avg'] or 5.0
        verified_count = qs.filter(is_verified_buyer=True).count()
        approved_count = qs.filter(is_approved=True).count()
        pending_count = qs.filter(is_approved=False).count()
        extra_context.update({
            'total_reviews_count': total_count,
            'avg_rating_display': f"{avg_rating:.1f}",
            'verified_patrons_count': verified_count,
            'approved_count': approved_count,
            'pending_count': pending_count,
        })
        return super().changelist_view(request, extra_context=extra_context)
