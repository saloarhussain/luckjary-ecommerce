from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import CustomUser, Address

class AddressInline(admin.StackedInline):
    model = Address
    extra = 0

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('client_display', 'vip_badge', 'is_email_verified_pill', 'newsletter_pill', 'date_joined')
    list_filter = ('is_email_verified', 'newsletter_subscribed', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    inlines = [AddressInline]
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Verification & Club', {'fields': ('is_email_verified', 'email_verification_token', 'newsletter_subscribed')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    @admin.display(description='Client / Email', ordering='email')
    def client_display(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip() or "Patron"
        initials = (obj.first_name[:1] + obj.last_name[:1]).upper() or obj.email[:2].upper()
        return format_html(
            '<div style="display:flex; align-items:center; gap:0.6rem;">'
            '<div style="width:30px; height:30px; border-radius:50%; background:#242432; border:1px solid #C5A059; color:#DFBE76; font-size:0.75rem; font-weight:700; display:flex; align-items:center; justify-content:center;">{}</div>'
            '<div>'
            '<div style="font-weight:600; color:#FFFFFF;">{}</div>'
            '<div style="color:#DFBE76; font-size:0.72rem;">{}</div>'
            '</div>'
            '</div>',
            initials,
            name,
            obj.email
        )

    @admin.display(description='Tier / Role')
    def vip_badge(self, obj):
        if obj.is_superuser:
            return mark_safe('<span class="badge-luxury" style="background:rgba(197,160,89,0.2); color:#DFBE76; border:1px solid #C5A059;">👑 Atelier Director</span>')
        elif obj.is_staff:
            return mark_safe('<span class="badge-luxury badge-processing">💎 Atelier Staff</span>')
        return mark_safe('<span class="badge-luxury badge-delivered">✨ VIP Patron</span>')

    @admin.display(description='Email Verification', ordering='is_email_verified')
    def is_email_verified_pill(self, obj):
        if obj.is_email_verified:
            return mark_safe('<span class="badge-luxury badge-paid">✓ Verified</span>')
        return mark_safe('<span class="badge-luxury badge-pending">⏳ Unverified</span>')

    @admin.display(description='Haute Gazette', ordering='newsletter_subscribed')
    def newsletter_pill(self, obj):
        if obj.newsletter_subscribed:
            return mark_safe('<span class="badge-luxury" style="background:rgba(99,102,241,0.12); color:#A5B4FC; border:1px solid rgba(99,102,241,0.3);">Subscribed</span>')
        return mark_safe('<span style="color:#666677;">No</span>')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'city', 'state_province', 'country', 'is_default')
    list_filter = ('address_type', 'country', 'is_default')
    search_fields = ('user__email', 'full_name', 'street_address', 'city')
