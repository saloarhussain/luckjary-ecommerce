from django.db import models, OperationalError, ProgrammingError

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ContactInquiry(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Contact Inquiries"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} from {self.name}"


def ensure_core_migrated():
    """Ensure core migrations are applied (needed on Vercel where build skips migrate)."""
    from django.db import connection
    from django.core.management import call_command

    if getattr(connection, 'needs_rollback', False):
        connection.rollback()
    call_command('migrate', 'core', verbosity=0, interactive=False)


class HeroVideoAsset(models.Model):
    """Stores metadata for an uploaded hero render video persisted in DB."""

    CHUNK_SIZE = 1536 * 1024  # 1.5 MiB (safely below Vercel 4.5 MB payload limit)

    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, default='video/mp4')
    total_size = models.PositiveBigIntegerField(default=0)
    total_chunks = models.PositiveIntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} ({self.total_size} bytes)"


class HeroVideoChunk(models.Model):
    """Binary slice of a HeroVideoAsset."""

    asset = models.ForeignKey(HeroVideoAsset, on_delete=models.CASCADE, related_name='chunks')
    index = models.PositiveIntegerField()
    data = models.BinaryField()

    class Meta:
        unique_together = ('asset', 'index')
        ordering = ['index']


class StorefrontThemeSettings(models.Model):
    """Singleton configuration for homepage scroll-video hero and storefront theme customization."""

    PLAYBACK_MODE_CHOICES = [
        ('scrub', 'Apple-Style Scroll Scrub'),
        ('autoplay', 'Autoplay While Visible'),
    ]

    # Hero Video & Scroll Playback
    hero_video_enabled = models.BooleanField(default=True)
    hero_video_mode = models.CharField(max_length=20, choices=PLAYBACK_MODE_CHOICES, default='scrub')
    hero_video_url = models.CharField(max_length=500, blank=True, default='/static/videos/hero-render.mp4')
    hero_video_webm_url = models.CharField(max_length=500, blank=True, default='/static/videos/hero-render.webm')
    hero_poster_url = models.CharField(
        max_length=500,
        blank=True,
        default='https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=2000&q=85',
    )

    # Scroll Choreography & Visual Tuning
    hero_scroll_height_vh = models.PositiveIntegerField(default=280)
    hero_scrub_smoothing = models.FloatField(default=0.16)
    hero_video_opacity = models.PositiveIntegerField(default=90)
    hero_vignette_strength = models.PositiveIntegerField(default=45)
    hero_fade_overlay_on_scroll = models.BooleanField(default=True)
    hero_overlay_fade_start = models.PositiveIntegerField(default=70)
    hero_show_scroll_cue = models.BooleanField(default=True)
    hero_show_progress_bar = models.BooleanField(default=True)

    # Hero Editorial Copy & CTAs
    hero_badge_text = models.CharField(max_length=120, default='The 925 Sterling Silver Heirlooms')
    hero_title_line1 = models.CharField(max_length=120, default='Lustrous Silver.')
    hero_title_line2 = models.CharField(max_length=120, default='Radiant for Every Moment.')
    hero_subtitle = models.TextField(
        default='Discover handcrafted 925 solid sterling silver heirlooms treated with a microscopic rhodium anti-tarnish barrier and certified brilliant stones.'
    )
    hero_primary_cta_text = models.CharField(max_length=80, default='Explore The Collection')
    hero_secondary_cta_text = models.CharField(max_length=80, default='The Bridal Atelier')

    # Design Tokens JSON (accent, typography, radius, spotlight_bento)
    design_tokens_json = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    DEFAULT_SPOTLIGHT_BENTO = {
        'enabled': True,
        'left': {
            'eyebrow': 'LUCKJARY • ATELIER SPOTLIGHT',
            'title': 'The Solstice Heritage',
            'subtitle': 'Handcrafted 925 sterling silver heirlooms with rhodium anti-tarnish seal & certified stones.',
            'cta': 'Explore Collection',
            'image_url': 'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?auto=format&fit=crop&w=1200&q=85',
            'link_url': '/products/?collection=solstice-heritage',
        },
        'top_right': {
            'eyebrow': 'NEW ARRIVALS',
            'title': 'Sculpted Silver Designs',
            'subtitle': 'New & Most-Loved Styles for Every Occasion',
            'image_url': 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?auto=format&fit=crop&w=1200&q=85',
            'link_url': '/products/?category=necklaces',
        },
        'bottom_right': {
            'eyebrow': 'FOR THE FINEST IN 925 SILVER',
            'title': 'Everyday Radiance',
            'subtitle': 'Timeless rhodium-sealed rings & bracelets crafted for daily brilliance.',
            'image_url': 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=1200&q=85',
            'link_url': '/products/?category=rings',
        },
    }

    class Meta:
        verbose_name = "Storefront Theme Customize"
        verbose_name_plural = "Storefront Theme Customize"

    def __str__(self):
        return "Luckjary Storefront Theme & Hero Render Settings"

    @classmethod
    def get_solo(cls):
        try:
            obj, _ = cls.objects.get_or_create(pk=1)
            return obj
        except (ProgrammingError, OperationalError):
            try:
                ensure_core_migrated()
                obj, _ = cls.objects.get_or_create(pk=1)
                return obj
            except Exception:
                return cls()

    def hero_vignette_alpha(self):
        return f"{self.hero_vignette_strength / 100:.2f}"

    def get_spotlight_bento(self):
        saved = (self.design_tokens_json or {}).get('spotlight_bento')
        merged = {}
        for slot in ('left', 'top_right', 'bottom_right'):
            base = dict(self.DEFAULT_SPOTLIGHT_BENTO[slot])
            if isinstance(saved, dict) and isinstance(saved.get(slot), dict):
                for k, v in saved[slot].items():
                    if v is not None and str(v).strip() != '':
                        base[k] = str(v).strip()
            merged[slot] = base
        merged['enabled'] = bool(saved.get('enabled', True)) if isinstance(saved, dict) else True
        return merged

    def to_dict(self):
        tokens = dict(self.design_tokens_json or {})
        tokens.pop('spotlight_bento', None)
        return {
            'hero_video_enabled': self.hero_video_enabled,
            'hero_video_mode': self.hero_video_mode,
            'hero_video_url': self.hero_video_url,
            'hero_video_webm_url': self.hero_video_webm_url,
            'hero_poster_url': self.hero_poster_url,
            'hero_scroll_height_vh': self.hero_scroll_height_vh,
            'hero_scrub_smoothing': self.hero_scrub_smoothing,
            'hero_video_opacity': self.hero_video_opacity,
            'hero_vignette_strength': self.hero_vignette_strength,
            'hero_vignette_alpha': f"{self.hero_vignette_strength / 100:.2f}",
            'hero_fade_overlay_on_scroll': self.hero_fade_overlay_on_scroll,
            'hero_overlay_fade_start': self.hero_overlay_fade_start,
            'hero_show_scroll_cue': self.hero_show_scroll_cue,
            'hero_show_progress_bar': self.hero_show_progress_bar,
            'hero_badge_text': self.hero_badge_text,
            'hero_title_line1': self.hero_title_line1,
            'hero_title_line2': self.hero_title_line2,
            'hero_subtitle': self.hero_subtitle,
            'hero_primary_cta_text': self.hero_primary_cta_text,
            'hero_secondary_cta_text': self.hero_secondary_cta_text,
            'spotlight_bento': self.get_spotlight_bento(),
            'design_tokens': tokens,
        }
