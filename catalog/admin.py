from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Material, Collection, Product, ProductImage, ProductReview

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
