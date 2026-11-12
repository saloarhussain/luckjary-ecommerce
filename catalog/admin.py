from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Material, Collection, Product, ProductImage, ProductReview

class ProductAdminForm(forms.ModelForm):
    STANDARD_METALS = [
        # 18K Solid Gold
        ('18K Solid Yellow Gold', '18K Solid Yellow Gold'),
        ('18K Solid White Gold', '18K Solid White Gold'),
        ('18K Solid Rose Gold', '18K Solid Rose Gold'),
        # 18K Gold Vermeil & Demi-Fine
        ('18K Yellow Gold Vermeil', '18K Yellow Gold Vermeil'),
        ('18K Rose Gold Vermeil', '18K Rose Gold Vermeil'),
        ('18K White Gold Vermeil', '18K White Gold Vermeil'),
        # Platinum & Sterling Silver
        ('Platinum 950', 'Platinum 950'),
        ('925 Sterling Silver', '925 Sterling Silver'),
        # 14K Solid Gold
        ('14K Solid Yellow Gold', '14K Solid Yellow Gold'),
        ('14K Solid White Gold', '14K Solid White Gold'),
        ('14K Solid Rose Gold', '14K Solid Rose Gold'),
    ]

    metal_presets = forms.MultipleChoiceField(
        choices=STANDARD_METALS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'admin-checkbox-grid'}),
        required=False,
        label="Precious Metal Quick Checkboxes",
        help_text="Check the precious metals available for clients to select on the product page. Automatically synced with Available Metals below."
    )

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'available_metals': forms.TextInput(attrs={
                'placeholder': 'e.g. 18K Solid Yellow Gold, 18K Solid White Gold, 18K Solid Rose Gold, Platinum 950',
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
            'meta_description': forms.Textarea(attrs={'rows': 2, 'style': 'width: 100%;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current = self.instance.metal_options
            matched = [c[0] for c in self.STANDARD_METALS if c[0] in current]
            self.fields['metal_presets'].initial = matched
        else:
            self.fields['metal_presets'].initial = [
                '18K Solid Yellow Gold',
                '18K Solid White Gold',
                '18K Solid Rose Gold',
                'Platinum 950'
            ]

    def clean(self):
        cleaned_data = super().clean()
        presets = cleaned_data.get('metal_presets') or []
        custom_metals = cleaned_data.get('available_metals') or ''
        karat = (cleaned_data.get('karat_metal') or '').strip()
        
        # Combine presets with custom metals entered
        existing = [m.strip() for m in custom_metals.split(',') if m.strip()]
        combined = []
        for p in presets:
            if p not in combined:
                combined.append(p)
        for e in existing:
            if e not in combined:
                combined.append(e)
                
        if combined:
            cleaned_data['available_metals'] = ', '.join(combined)
            if not karat:
                cleaned_data['karat_metal'] = combined[0]
            
        return cleaned_data

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductReviewInline(admin.StackedInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_featured', 'order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_featured', 'order')

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'badge_label')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'subtitle', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    fieldsets = (
        ('💎 Jewelry Identity', {
            'fields': (
                ('title', 'slug'),
                ('sku', 'category', 'collection'),
                'subtitle',
                'description',
            )
        }),
        ('💰 Pricing & Inventory Vault', {
            'fields': (
                ('price', 'compare_at_price'),
                ('inventory', 'is_available'),
                ('is_featured', 'is_bestseller', 'is_new_arrival'),
            )
        }),
        ('✨ Precious Metals & Live Swatches', {
            'description': 'Select which precious metal variants are offered for this piece. Clients can switch between these metals with live swatches on the boutique product page.',
            'fields': (
                'metal_presets',
                'karat_metal',
                'available_metals',
            )
        }),
        ('💎 Gemstones & Specialty Materials', {
            'description': 'Specify featured gemstones, pearl varieties, and diamond grades. (Precious metals selected above are automatically mapped to catalog filters on save).',
            'fields': (
                ('gemstone', 'carat_weight'),
                'materials',
            )
        }),
        ('📏 Sizing Framework & Specifications', {
            'description': 'Configure available ring sizes (US 4 to 13 with half-sizes), necklace chain lengths, or custom dimensions. Leave Available Sizes blank to automatically provide the complete standard size range for this jewelry piece.',
            'fields': (
                ('size_category', 'chain_length_or_size'),
                'available_sizes',
                ('dimensions', 'certification'),
            )
        }),
        ('🏛️ Haute Craftsmanship & Care', {
            'classes': ('collapse',),
            'fields': (
                'craftsmanship_details',
                'care_instructions',
            )
        }),
        ('🔍 SEO & Meta Optimization', {
            'classes': ('collapse',),
            'fields': (
                'meta_title',
                'meta_description',
                'meta_keywords',
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
    list_filter = ('category', 'style', 'is_available', 'is_featured', 'is_bestseller', 'materials')
    search_fields = ('title', 'sku', 'description', 'karat_metal', 'gemstone', 'category__name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_available',)
    list_per_page = 25
    actions_on_top = True
    actions_on_bottom = False
    inlines = [ProductImageInline, ProductReviewInline]
    filter_horizontal = ('materials',)
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
        metals_text = f"{product.karat_metal} {product.available_metals}".lower()
        
        to_add = []
        if 'vermeil' in metals_text or 'demifine' in metals_text or 'demifne' in metals_text:
            m = Material.objects.filter(slug='18k-gold-vermeil-demifine').first()
            if m:
                to_add.append(m)
        if '18k solid yellow' in metals_text or ('18k' in metals_text and 'yellow' in metals_text and 'vermeil' not in metals_text):
            m = Material.objects.filter(slug='18k-solid-yellow-gold').first()
            if m:
                to_add.append(m)
        if 'white gold' in metals_text and 'vermeil' not in metals_text:
            m = Material.objects.filter(slug='18k-white-gold').first()
            if m:
                to_add.append(m)
        if 'rose gold' in metals_text and 'vermeil' not in metals_text:
            m = Material.objects.filter(slug='18k-rose-gold').first()
            if m:
                to_add.append(m)
        if 'platinum' in metals_text:
            m = Material.objects.filter(slug='platinum-950').first()
            if m:
                to_add.append(m)
        if 'sterling silver' in metals_text or ('silver' in metals_text and 'vermeil' not in metals_text):
            m = Material.objects.filter(slug='925-sterling-silver').first()
            if m:
                to_add.append(m)
                
        if to_add:
            product.materials.add(*to_add)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from django.db.models import Sum
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
    list_display = ('product', 'author_name', 'rating_stars', 'is_verified_buyer', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified_buyer', 'is_approved')
    search_fields = ('author_name', 'title', 'comment', 'product__title')
    list_editable = ('is_approved',)

    @admin.display(description='Customer Rating', ordering='rating')
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#DFBE76; font-size:0.9rem;">{}</span>', stars)
