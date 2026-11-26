from django.contrib import admin
from .models import ContactInquiry, NewsletterSubscriber, StorefrontThemeSettings

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_resolved',)

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)

@admin.register(StorefrontThemeSettings)
class StorefrontThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'hero_video_enabled', 'hero_video_mode', 'hero_scroll_height_vh', 'updated_at')
