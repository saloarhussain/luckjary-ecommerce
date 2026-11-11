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
    list_display = ('thumb_display', 'title_sku_display', 'category', 'price_display', 'stock_badge', 'is_available', 'merchandising_display')
    list_filter = ('category', 'style', 'is_available', 'is_featured', 'is_bestseller', 'materials')
    search_fields = ('title', 'sku', 'description', 'karat_metal', 'gemstone')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_available',)
    inlines = [ProductImageInline, ProductReviewInline]
    filter_horizontal = ('materials',)

    @admin.display(description='Piece Preview')
    def thumb_display(self, obj):
        img_url = obj.primary_image
        return format_html('<img src="{}" class="admin-thumb" alt="{}" loading="lazy" />', img_url, obj.title)

    @admin.display(description='Jewelry Title & SKU', ordering='title')
    def title_sku_display(self, obj):
        return format_html(
            '<div style="line-height:1.35;">'
            '<div style="font-weight:600; color:#FFFFFF;">{}</div>'
            '<div style="font-family:monospace; color:#DFBE76; font-size:0.72rem;">SKU: {}</div>'
            '<div style="color:#8A8A9C; font-size:0.7rem;">{}</div>'
            '</div>',
            obj.title,
            obj.sku,
            obj.karat_metal
        )

    @admin.display(description='Retail Price', ordering='price')
    def price_display(self, obj):
        price_str = f"{obj.price:,.2f}"
        if obj.compare_at_price:
            comp_str = f"{obj.compare_at_price:,.2f}"
            return format_html(
                '<div><span class="price-gold">${}</span><span style="color:#777788; text-decoration:line-through; font-size:0.75rem; margin-left:4px;">${}</span></div>',
                price_str,
                comp_str
            )
        return format_html(
            '<div><span class="price-gold">${}</span></div>',
            price_str
        )

    @admin.display(description='Vault Inventory', ordering='inventory')
    def stock_badge(self, obj):
        if obj.inventory > 10:
            return format_html('<span class="badge-luxury badge-delivered">● In Stock ({})</span>', obj.inventory)
        elif obj.inventory > 0:
            return format_html('<span class="badge-luxury badge-pending">● Low Stock ({})</span>', obj.inventory)
        return mark_safe('<span class="badge-luxury badge-cancelled">● Sold Out (0)</span>')

    @admin.display(description='Badges')
    def merchandising_display(self, obj):
        badges = []
        if obj.is_featured:
            badges.append('<span class="badge-luxury" style="background:rgba(197,160,89,0.2); color:#DFBE76; border:1px solid #C5A059;">★ Featured</span>')
        if obj.is_bestseller:
            badges.append('<span class="badge-luxury" style="background:rgba(217,119,6,0.15); color:#FBBF24; border:1px solid #D97706;">👑 Bestseller</span>')
        if obj.is_new_arrival:
            badges.append('<span class="badge-luxury" style="background:rgba(99,102,241,0.15); color:#A5B4FC; border:1px solid #6366F1;">✨ New</span>')
        if not badges:
            return mark_safe('<span style="color:#555566;">-</span>')
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
