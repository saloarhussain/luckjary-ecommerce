from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import CustomUser, Address

class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    verbose_name = "Saved Address"
    verbose_name_plural = "Customer Saved Addresses"
    fields = (
        ('address_type', 'is_default'),
        ('full_name', 'phone_number'),
        'street_address',
        ('apartment_suite', 'city'),
        ('state_province', 'postal_code', 'country'),
    )

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    show_facets = admin.ShowFacets.NEVER
    list_display = ('client_display', 'account_role_pill', 'is_email_verified_pill', 'newsletter_pill', 'date_joined', 'action_buttons')
    list_filter = ('is_email_verified', 'newsletter_subscribed', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    inlines = [AddressInline]
    
    # Organised: Customer Name -> Mobile Number -> Email -> Address (Inline below)
    fieldsets = (
        ("Customer Details", {
            'fields': (
                ('first_name', 'last_name'),
                ('phone_number', 'email'),
            ),
            'description': "Primary customer identity and contact information."
        }),
        ("Newsletter & Email Verification", {
            'fields': (
                ('is_email_verified', 'newsletter_subscribed'),
                'email_verification_token',
            ),
            'classes': ('collapse',),
        }),
        ("Account Credentials & Password", {
            'fields': ('password',),
            'classes': ('collapse',),
            'description': "Authentication credentials and raw password reset tools."
        }),
        ("Permissions & Roles", {
            'fields': (
                ('is_active', 'is_staff', 'is_superuser'),
                'groups',
                'user_permissions',
            ),
            'classes': ('collapse',),
        }),
        ("Activity & Dates", {
            'fields': (('last_login', 'date_joined'),),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ("Customer Details", {
            'classes': ('wide',),
            'fields': (
                ('first_name', 'last_name'),
                ('phone_number', 'email'),
                'usable_password',
                ('password1', 'password2'),
            ),
        }),
    )

    @admin.display(description='Customer / Contact', ordering='first_name')
    def client_display(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip() or "Patron"
        initials = (obj.first_name[:1] + obj.last_name[:1]).upper() or obj.email[:2].upper()
        phone_html = f'<div style="color:#94A3B8; font-size:0.71rem; margin-top:2px; font-family:monospace;">📞 {obj.phone_number}</div>' if obj.phone_number else ''
        return format_html(
            '<div style="display:flex; align-items:center; gap:0.75rem;">'
            '<div style="width:32px; height:32px; border-radius:50%; background:#242432; border:1px solid #C5A059; color:#DFBE76; font-size:0.75rem; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0;">{}</div>'
            '<div>'
            '<div style="font-weight:600; color:#FFFFFF; font-size:0.84rem;">{}</div>'
            '<div style="color:#DFBE76; font-size:0.73rem;">{}</div>'
            '{}'
            '</div>'
            '</div>',
            initials,
            name,
            obj.email,
            mark_safe(phone_html)
        )

    @admin.display(description='Action')
    def action_buttons(self, obj):
        edit_url = reverse('admin:accounts_customuser_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="display:inline-flex; align-items:center; gap:4px; padding:4px 10px; background:#1C202C; border:1px solid #2D3242; border-radius:6px; color:#E2E8F0; font-size:0.72rem; font-weight:600; text-decoration:none; transition:all 0.15s ease;">Edit</a>',
            edit_url
        )

    @admin.display(description='Role')
    def account_role_pill(self, obj):
        if obj.is_superuser:
            return mark_safe('<span class="badge-luxury" style="background:rgba(197,160,89,0.18); color:#DFBE76; border:1px solid #C5A059;">👑 Atelier Admin</span>')
        elif obj.is_staff:
            return mark_safe('<span class="badge-luxury" style="background:rgba(59,130,246,0.15); color:#93C5FD; border:1px solid rgba(59,130,246,0.3);">💎 Staff</span>')
        return mark_safe('<span class="badge-luxury" style="background:rgba(148,163,184,0.12); color:#CBD5E1; border:1px solid rgba(148,163,184,0.25);">Customer</span>')

    @admin.display(description='Email Verification', ordering='is_email_verified')
    def is_email_verified_pill(self, obj):
        if obj.is_email_verified:
            return mark_safe('<span class="badge-luxury badge-paid">✓ Verified</span>')
        return mark_safe('<span class="badge-luxury badge-pending">⏳ Unverified</span>')

    @admin.display(description='Newsletter', ordering='newsletter_subscribed')
    def newsletter_pill(self, obj):
        if obj.newsletter_subscribed:
            return mark_safe('<span class="badge-luxury" style="background:rgba(16,185,129,0.12); color:#34D399; border:1px solid rgba(16,185,129,0.3);">Subscribed</span>')
        return mark_safe('<span style="color:#64748B; font-size:0.75rem;">Not Subscribed</span>')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'city', 'state_province', 'country', 'is_default')
    list_filter = ('address_type', 'country', 'is_default')
    search_fields = ('user__email', 'full_name', 'street_address', 'city')
