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


class SiteImageAsset(models.Model):
    """Stores uploaded storefront images (Bento cards, Hero poster) in DB for Vercel persistence."""

    key = models.SlugField(max_length=80, unique=True)
    content_type = models.CharField(max_length=80, default='image/webp')
    data = models.BinaryField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


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
        'height_px': 672,
        'gap_px': 16,
        'radius_px': 16,
        'scrim_strength': 75,
        'left': {
            'eyebrow': 'LUCKJARY • ATELIER SPOTLIGHT',
            'title': 'The Solstice Heritage',
            'subtitle': 'Handcrafted 925 sterling silver heirlooms with rhodium anti-tarnish seal & certified stones.',
            'cta': 'Explore Collection',
            'image_url': 'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?auto=format&fit=crop&w=1200&q=85',
            'link_url': '/shop/?collection=solstice-heritage',
        },
        'top_right': {
            'eyebrow': 'NEW ARRIVALS',
            'title': 'Sculpted Silver Designs',
            'subtitle': 'New & Most-Loved Styles for Every Occasion',
            'image_url': 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?auto=format&fit=crop&w=1200&q=85',
            'link_url': '/shop/?category=necklaces',
        },
        'bottom_right': {
            'eyebrow': 'FOR THE FINEST IN 925 SILVER',
            'title': 'Everyday Radiance',
            'subtitle': 'Timeless rhodium-sealed rings & bracelets crafted for daily brilliance.',
            'image_url': 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=1200&q=85',
            'link_url': '/shop/?category=rings',
        },
    }

    DEFAULT_PRICE_CARDS = {
        'enabled': True,
        'eyebrow': 'CURATED VALUE',
        'heading': 'Shop by Price',
        'cards': [
            {
                'badge': 'Everyday Silver',
                'title': 'Under ₹999',
                'price_cap': '999',
                'subtitle': 'Minimalist 925 studs, charms & stacking rings for daily wear.',
                'cta': 'Shop Under ₹999',
                'link_url': '/shop/?max_price=999',
            },
            {
                'badge': 'Gifting Edit',
                'title': 'Under ₹1,499',
                'price_cap': '1499',
                'subtitle': 'Thoughtful pendants, chains & dainty bracelets in velvet gift boxes.',
                'cta': 'Shop Under ₹1,499',
                'link_url': '/shop/?max_price=1499',
            },
            {
                'badge': 'Signature Pieces',
                'title': 'Under ₹2,499',
                'price_cap': '2499',
                'subtitle': 'Certified brilliant-stone solitaires, tennis bracelets & statement sets.',
                'cta': 'Shop Under ₹2,499',
                'link_url': '/shop/?max_price=2499',
            },
        ],
    }

    DEFAULT_PERSONALISED_SECTION = {
        'enabled': True,
        'eyebrow': 'BESPOKE ATELIER • CUSTOM CRAFT',
        'title': 'Personalised 925 Silver Jewellery',
        'subtitle': 'Crafted exclusively to carry your story — custom name & initial pendants, secret inner-band engraving, zodiac talismans, and hand-set birthstones in solid 925 sterling silver.',
        'tag1': 'Custom Name & Initials',
        'tag2': 'Laser Inner-Band Engraving',
        'tag3': 'Birthstone & Couple Sets',
        'cta_text': 'Commission Personalised Piece',
        'cta_url': '/contact/?subject=personalised',
        'secondary_cta_text': 'Browse Ready Pieces',
        'secondary_cta_url': '/shop/',
        'image_url': 'https://images.unsplash.com/photo-1617038260897-41a1f14a8ca0?auto=format&fit=crop&w=1200&q=85',
    }

    DEFAULT_HOMEPAGE_CONTENT = {
        'announcement': {
            'enabled': True,
            'text': 'Luckjary Festive Carnival is LIVE:',
            'link_text': 'Shop Now!',
            'link_url': '/shop/',
            'secondary_text': 'Easy 15-Day Return Policy, No Questions Asked',
            'brand_name': 'LUCKJARY',
            'brand_sub': 'HAUTE JOAILLERIE',
        },
        'hero': {
            'enabled': True,
            'eyebrow': 'LUCKJARY Atelier Event',
            'title': 'Golden Atelier Days',
            'offer_badge': 'Exclusive Offer',
            'offer_highlight': '50% Off',
            'offer_subtitle': 'On Making Charges · All Diamond & 925 Designs',
            'cta_text': 'Shop the Event',
            'cta_url': '/shop/',
            'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrDWj4ycR5DsdpR6vZpqQhlyYMhEDAfaYN7OSj4mVHivd4PpUrWhIlBtB73Qv00wVwSuF-Ipa5n44aEbo1RPI0MQ8mqSasAgJsmWUrgQ7V-E4dQDplRx3sSJFO9LDGu-o75xnqaFHAbq5G36EWrArKOus36HjAh9qc7TmHSiwWoGR6FxM3CeJMiRFq011WLcH7f9Qa-xjMp4YLe56VGviDUo7ZoiF8vCm1H73jC5Qd8KK9p66IOPm_rjATdM2vzt',
            'strip_enabled': True,
            'strip_icon': 'credit_card',
            'strip_text_primary': '10% Instant Bank Savings up to $75 on Fine Solitaires',
            'strip_text_secondary': 'Complimentary Insured Shipping · Valid through Nov 30',
        },
        'carousel': {
            'enabled': True,
            'eyebrow': 'LUCKJARY 925 Diamonds',
            'title': 'Flat 20% Off Natural Diamonds in 925 Silver',
            'subtitle': 'Starting at $120',
            'header_cta_text': 'Shop Now',
            'header_cta_url': '#bento-grid',
            'bottom_cta_text': 'Shop Now',
            'bottom_cta_url': '/shop/',
            'bg_image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrDP_IcnNfDkcpHWYDd3qpzHOQpmoq_CkZOYkEph9DmkCIUkbHDGfJkjCZQ3L6anZTpPGq5cWYMGMU2lhaV-NovnX_FrFwCzm0AZMfgQLR3djnaG87UVeN2GUbuRv8YMPInr-uKealgx98Wbqn-kBThiWaZzb7mP5IX9rgFlAmiuDC_nNPF1vhFlsvXJ9qRQEsvheKDjSnppDoZ-yIdFngSajia1L7OeGqdOH2M2M1KZiyJ1KcqDMgjFOKegx8a9tg',
            'source_mode': 'auto',
            'cards': [
                {
                    'title': 'Anchor 925 Silver Band',
                    'price': '$120',
                    'compare_price': '$150',
                    'link_url': '/category/rings/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCjbhsSorM7Qp6-L5feydmQQVJlC-PhW8b2ugauC8c1RLZQOyR8EgO0ZbukbUQXIZjgYuEJgpXUH1SO88an6Qq8bBdHg_MYL9T9uVNOyg3BYk057GlYBi0wDgsGf_GsFiZW2T0s2zugvweVpeEUXCXVCPswOR0Vp8TtDt9j86UXej2I7bMJNBWJI6FfmgqszWD4Ejg0YTpnpDkUu71XsuCZZ3PWtcfJTdI1CbprNhEX4QcUx_n7xRKQ-YG1',
                },
                {
                    'title': 'Alex Vermeil Cuff',
                    'price': '$165',
                    'compare_price': '$205',
                    'link_url': '/category/bracelets/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCYw8Gviu40Rm80-l1jI7PVPGgrllhuiNz6S00c28x7MNitC3Psb9ENuBniBCL4rpJJVLVnX_aBgZ7oReUVCwm--LkGSD2LDyKWNjlFZutpbH2tWss5K7zNoy3LjDEmSBcj1n6f-xcvtGDMgZCqVcwXvUeEIUwKP2y2fs0qJ5S9Ed0NmnenQfpu-yltiA3wtCI0ffScsDB1-HnSBVartQykTnfFWdbnv1fOZ67pSq1CNLDyqqFXkpqwl8aBHBDV',
                },
                {
                    'title': 'Knot Sterling Hoops',
                    'price': '$190',
                    'compare_price': '$240',
                    'link_url': '/category/earrings/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrBWYmHm5OOMLtcaoD8sIIKeIuQ8AXkOBmCm6woTG7JOxpo6PKicjQyOBwy0ByTjbbSJ3upXnMYQXm7-tNVz1UME1i8wQSrhOY9Uj6oMz4yhfuW0LrDfZhBDefcHt0orBrFfL8VIgQJhXoDyUM9BeJrs5uBNAAvhsXZlyPTNpv7iAs4M0zLyHrwstXMmR-y4M8GOeBYV3MCP_iA9UP_P9Mh6Yzq9LX4R09N3CzSQT81GQlh1gC2K6m5C5zUuWlIm',
                },
            ],
        },
        'bento': {
            'enabled': True,
            'left': {
                'brand_label': 'LUCKJARY · 925',
                'pill_badge': '925 Sterling',
                'eyebrow': 'LUCKJARY 925 Sterling',
                'title': 'Crafted in Pure 925 Silver',
                'cta_badge': 'Flat 50% Off',
                'link_url': '/shop/?material=925-sterling-silver',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCmre7oRMBVhPOjfmUlkiILE4umPCXOvCgZMFLueCSp5Eei9gJngQuvWuvnwLx2FrWHTuf-KjRXkfco1bVllp1G9lHdPZ-1n0rVcLk_tgq_Ekq-sWEUTGd7ohC9zCwIJo9zH4CnJtLmvNSxsxOI7a9rd9o34hz_UPR0FVF2f7f4LkGmJTX3EMcAn5TyNBkGmROmKVT8Q4e2Qg-fwb3SKhj-u9GM2DLeVcNjzAhGpx6GRzgBiFNEUP21mHBLtw',
            },
            'top_right': {
                'eyebrow': '73 Facets · By LUCKJARY',
                'title': 'Lumiere Solitaires',
                'subtitle': 'Precision-cut diamonds for maximum fire and brilliance.',
                'cta_text': 'Shop Now',
                'link_url': '/shop/?style=classic',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCvGEgzfNKcuOAwg-VjC-zWApMM97581vsBdrUmeJAO1VI0WSeniOYxqlTTeqckR9bZwhDG2OEspOhD70SOmzss6w33Mw8iVSKFR5yq5Z2tLm-WTVzRue8c3fswAzmxAOjn8HjzGKI9QxMq-fjMqWAtV0Uxay6ffFSERS7hwN15khorXJ_Ip_x4ehZlP6SdTBFODRyg2knZb34MH_54bjFiUPk6P4Morcg3ys9BHHYeZ1XdxvnhZ2KN_Wiz4z0',
            },
            'bottom_right': {
                'eyebrow': 'Statement Edit',
                'title': 'New Cocktail Rings',
                'subtitle': 'Sculptural silhouettes designed for evening occasions.',
                'link_url': '/category/rings/',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCfPW96Hys0yHphB-fCQYB7HLdDTMbxBqsM7-VjOdLAB3lZFuueQtaO14zyCyaBMZIcZRbaaJVvMNF6qlxcYlxQcKEGwMWVKUlwKUC9gUZlmeA-1aZhydDlL6vaa0sjHqIhjwzUdLriPWhnSXemsYO5mb8S9wlzXXCd2c47YIBJptmTyzFjdzuhZEHJYA_FmyGi7uCaR1yB4yu89afENZRdgLsoWyIu90tVzRGsCdF9q3U_cx-zs8KtDdE4srINmg',
            },
        },
        'wrapped': {
            'enabled': True,
            'icon': 'redeem',
            'title': 'Wrapped with love',
            'items': [
                {
                    'label': 'New Rings',
                    'link_url': '/category/rings/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCjbhsSorM7Qp6-L5feydmQQVJlC-PhW8b2ugauC8c1RLZQOyR8EgO0ZbukbUQXIZjgYuEJgpXUH1SO88an6Qq8bBdHg_MYL9T9uVNOyg3BYk057GlYBi0wDgsGf_GsFiZW2T0s2zugvweVpeEUXCXVCPswOR0Vp8TtDt9j86UXej2I7bMJNBWJI6FfmgqszWD4Ejg0YTpnpDkUu71XsuCZZ3PWtcfJTdI1CbprNhEX4QcUx_n7xRKQ-YG1',
                },
                {
                    'label': 'Festive Styles',
                    'link_url': '/category/bridal-high-jewelry/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrBA0bjRv83qCEOYMdLmZSJVgnLha5Yk1PCiFMiaDE86R0k3q5vBEY4vRpSNImay56cZIOO9QWpIzzAdGd6h8j-R91mtFFkxda_ywal4zTaDoD69jQn8nstXAqkM_54mySKaidOQY2kJbja_OhgZIt10Tec-MhQrrNcJO560OZ4c2iBZNTXdIvQqAL39HGkqzE68K9eiA4Pd1OgHteWPlNfNZJIHVgnltRp0y69YLg5jYd8qMCO7rqeIfFO4ORLTyg',
                },
                {
                    'label': 'Drop Earrings',
                    'link_url': '/category/earrings/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrDHGZiHeC86ec9VnTzChyJ-TGfu2w3-DtmXROisrYWPRrFiDBFFWiqYohh08pCPHl025IT0CYnWhOgT1Ktr8UwMCprbkosqUfb6qMgvxtBCWKg0Ymg5hKJE42jY0pqRVaL2-T50AUSlCSSeOYC65GbydQdjATTTk0NpcE-eXOzg4HckOpis0GQI5iCPEW6-AbLWMRXIobeLgaC8lzkCaMNFq7eq_ytd5z4A5pR_6RDNMOdXWs8Aua908z-gYdokUJY',
                },
                {
                    'label': 'Vermeil Cuffs',
                    'link_url': '/category/bracelets/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCYw8Gviu40Rm80-l1jI7PVPGgrllhuiNz6S00c28x7MNitC3Psb9ENuBniBCL4rpJJVLVnX_aBgZ7oReUVCwm--LkGSD2LDyKWNjlFZutpbH2tWss5K7zNoy3LjDEmSBcj1n6f-xcvtGDMgZCqVcwXvUeEIUwKP2y2fs0qJ5S9Ed0NmnenQfpu-yltiA3wtCI0ffScsDB1-HnSBVartQykTnfFWdbnv1fOZ67pSq1CNLDyqqFXkpqwl8aBHBDV',
                },
                {
                    'label': 'Sculpted Hoops',
                    'link_url': '/category/necklaces/',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrBWYmHm5OOMLtcaoD8sIIKeIuQ8AXkOBmCm6woTG7JOxpo6PKicjQyOBwy0ByTjbbSJ3upXnMYQXm7-tNVz1UME1i8wQSrhOY9Uj6oMz4yhfuW0LrDfZhBDefcHt0orBrFfL8VIgQJhXoDyUM9BeJrs5uBNAAvhsXZlyPTNpv7iAs4M0zLyHrwstXMmR-y4M8GOeBYV3MCP_iA9UP_P9Mh6Yzq9LX4R09N3CzSQT81GQlh1gC2K6m5C5zUuWlIm',
                },
                {
                    'label': 'Solitaires',
                    'link_url': '/shop/?style=classic',
                    'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrCvGEgzfNKcuOAwg-VjC-zWApMM97581vsBdrUmeJAO1VI0WSeniOYxqlTTeqckR9bZwhDG2OEspOhD70SOmzss6w33Mw8iVSKFR5yq5Z2tLm-WTVzRue8c3fswAzmxAOjn8HjzGKI9QxMq-fjMqWAtV0Uxay6ffFSERS7hwN15khorXJ_Ip_x4ehZlP6SdTBFODRyg2knZb34MH_54bjFiUPk6P4Morcg3ys9BHHYeZ1XdxvnhZ2KN_Wiz4z0',
                },
            ],
        },
        'price_and_personalised': {
            'enabled': True,
            'price_cards': [
                {
                    'eyebrow': 'Shop by Price',
                    'title': 'Under $1,000',
                    'cta_text': 'Explore',
                    'link_url': '/shop/?max_price=1000',
                },
                {
                    'eyebrow': 'Shop by Price',
                    'title': 'Under $2,000',
                    'cta_text': 'Explore',
                    'link_url': '/shop/?max_price=2000',
                },
            ],
            'personalised': {
                'enabled': True,
                'eyebrow': 'Bespoke Atelier',
                'title': 'Personalized Jewellery',
                'subtitle': 'Custom engravings, initials, and birthstones crafted to order.',
                'cta_text': 'Personalize Yours',
                'link_url': '/contact/?subject=personalised',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrDziJVAl1Tv9RTD5IRGFAO7-OJ7UPnbN1evt40F_oe2QGmVjZaYzacca8qPYN7HxOwIsSG0G-w4dfRCarFPeAJN9dQAVP750_UoT0GKIbacnIaOTEgA7_PRLq8DuDfvHT5-TEKRiAiF5WJdM4BelWD0rHE8R5ZoY3sBsaqMYg8FqBFj2RviewocNgWhdWr0gqPFmEV_1hVslxLMISJFmtHNoIh50VYPgScno5v9aax_ofML9D3ZqMtPsdRhFtDO1A',
            },
        },
        'trust_guarantees': {
            'enabled': True,
            'items': [
                {'icon': 'verified', 'label': '100% Certified'},
                {'icon': 'event_repeat', 'label': '15 Day Exchange'},
                {'icon': 'autorenew', 'label': 'Lifetime Exchange'},
                {'icon': 'workspace_premium', 'label': 'One Year Warranty'},
            ],
        },
        'vault_atelier': {
            'enabled': True,
            'vault': {
                'eyebrow': 'LUCKJARY Vault Plan',
                'title': '9=10 Monthly Saving Scheme',
                'subtitle': 'Pay 9 monthly instalments toward your next heirloom, and the 10th is on LUCKJARY.',
                'link_url': '/contact/?subject=vault-plan',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrBayDAuFjshNXMyoDhcc8QiqUIJfHHC0rJuoa0C2rbv0QLPkrXEZLbihb7aGpFpRL6un7A82FQlD5pJlAnLlRUDEPij1aknV4eDIfqogih3H_FzUlF_gdRAdwERob3-oFMc1kf4yr2jvUEoZCIH0BkbSqX7VC56CJ3yOCdgE44opDYPx0hO39Tb8ABMabXFDO1b1CWGHZzNaMoUE5GsCcbphtQJxfDMFXiFde4NgVQpbUXXuwJAQK1OSetIV_mIUg',
            },
            'top_right': {
                'eyebrow': 'Everyday 18k Vermeil',
                'title': 'Minimalist Chains & Bands',
                'subtitle': 'Lightweight pieces built for daily layering.',
                'link_url': '/category/necklaces/',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrBA0bjRv83qCEOYMdLmZSJVgnLha5Yk1PCiFMiaDE86R0k3q5vBEY4vRpSNImay56cZIOO9QWpIzzAdGd6h8j-R91mtFFkxda_ywal4zTaDoD69jQn8nstXAqkM_54mySKaidOQY2kJbja_OhgZIt10Tec-MhQrrNcJO560OZ4c2iBZNTXdIvQqAL39HGkqzE68K9eiA4Pd1OgHteWPlNfNZJIHVgnltRp0y69YLg5jYd8qMCO7rqeIfFO4ORLTyg',
            },
            'bottom_right': {
                'eyebrow': 'Private Salons',
                'title': 'Visit a LUCKJARY Boutique',
                'subtitle': 'Complimentary ultrasonic cleaning & styling.',
                'link_url': '/about/#boutiques',
                'image_url': 'https://lh3.googleusercontent.com/aida/ALJJyrDHGZiHeC86ec9VnTzChyJ-TGfu2w3-DtmXROisrYWPRrFiDBFFWiqYohh08pCPHl025IT0CYnWhOgT1Ktr8UwMCprbkosqUfb6qMgvxtBCWKg0Ymg5hKJE42jY0pqRVaL2-T50AUSlCSSeOYC65GbydQdjATTTk0NpcE-eXOzg4HckOpis0GQI5iCPEW6-AbLWMRXIobeLgaC8lzkCaMNFq7eq_ytd5z4A5pR_6RDNMOdXWs8Aua908z-gYdokUJY',
            },
        },
        'footer': {
            'enabled': True,
            'brand_name': 'LUCKJARY',
            'tagline': 'Hallmarked 925 sterling silver, natural diamonds, and 18k vermeil heirlooms.',
            'col1_heading': 'Know Your Jewelry',
            'col1_links': [
                {'label': 'Diamond Guide', 'url': '/faq/'},
                {'label': '925 Silver Purity', 'url': '/about/'},
                {'label': 'Ring Size Guide', 'url': '/faq/#sizing'},
            ],
            'col2_heading': 'Customer Care',
            'col2_links': [
                {'label': '15-Day Returns', 'url': '/faq/'},
                {'label': 'Track Order', 'url': '/track-order/'},
                {'label': 'Find a Store', 'url': '/about/#boutiques'},
            ],
            'newsletter_heading': 'Stay in Touch',
            'newsletter_placeholder': 'elena@example.com',
            'newsletter_button': 'Subscribe',
            'newsletter_note': 'Receive private previews and atelier offers.',
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

    def get_hero_pin_on_scroll(self):
        saved = self.design_tokens_json or {}
        return bool(saved.get('hero_pin_on_scroll', False))

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

        def _int_val(key, lo, hi, default):
            if not isinstance(saved, dict):
                return default
            try:
                return max(lo, min(hi, int(saved.get(key, default))))
            except (TypeError, ValueError):
                return default

        height_px = _int_val('height_px', 400, 950, self.DEFAULT_SPOTLIGHT_BENTO['height_px'])
        gap_px = _int_val('gap_px', 8, 36, self.DEFAULT_SPOTLIGHT_BENTO['gap_px'])
        radius_px = _int_val('radius_px', 0, 32, self.DEFAULT_SPOTLIGHT_BENTO['radius_px'])
        scrim_strength = _int_val('scrim_strength', 0, 90, self.DEFAULT_SPOTLIGHT_BENTO['scrim_strength'])

        merged['enabled'] = bool(saved.get('enabled', True)) if isinstance(saved, dict) else True
        merged['height_px'] = height_px
        merged['gap_px'] = gap_px
        merged['right_card_height_px'] = max(180, (height_px - gap_px) // 2)
        merged['radius_px'] = radius_px
        merged['scrim_strength'] = scrim_strength
        merged['scrim_alpha'] = f"{scrim_strength / 100:.2f}"
        return merged

    def get_price_cards(self):
        saved = (self.design_tokens_json or {}).get('price_cards')
        base = {
            'enabled': bool(saved.get('enabled', True)) if isinstance(saved, dict) else True,
            'eyebrow': str((saved or {}).get('eyebrow') or self.DEFAULT_PRICE_CARDS['eyebrow']).strip(),
            'heading': str((saved or {}).get('heading') or self.DEFAULT_PRICE_CARDS['heading']).strip(),
            'cards': [],
        }
        saved_cards = saved.get('cards') if isinstance(saved, dict) and isinstance(saved.get('cards'), list) else []
        for idx, default_card in enumerate(self.DEFAULT_PRICE_CARDS['cards']):
            merged_card = dict(default_card)
            if idx < len(saved_cards) and isinstance(saved_cards[idx], dict):
                for k, v in saved_cards[idx].items():
                    if v is not None and str(v).strip() != '':
                        merged_card[k] = str(v).strip()
            base['cards'].append(merged_card)
        return base

    def get_personalised_section(self):
        saved = (self.design_tokens_json or {}).get('personalised_section')
        merged = dict(self.DEFAULT_PERSONALISED_SECTION)
        if isinstance(saved, dict):
            for k, v in saved.items():
                if k == 'enabled':
                    merged['enabled'] = bool(v)
                elif v is not None and str(v).strip() != '':
                    merged[k] = str(v).strip()
        return merged

    @classmethod
    def _merge_homepage_node(cls, default_val, saved_val, key_name=''):
        if isinstance(default_val, dict):
            result = {}
            saved_dict = saved_val if isinstance(saved_val, dict) else {}
            for k, dv in default_val.items():
                result[k] = cls._merge_homepage_node(dv, saved_dict.get(k), k)
            return result
        if isinstance(default_val, list):
            saved_list = saved_val if isinstance(saved_val, list) else []
            merged_list = []
            for idx, dv in enumerate(default_val):
                sv = saved_list[idx] if idx < len(saved_list) else None
                merged_list.append(cls._merge_homepage_node(dv, sv, key_name))
            return merged_list
        if isinstance(default_val, bool):
            return bool(saved_val) if isinstance(saved_val, bool) else default_val
        if saved_val is None:
            return default_val
        text = str(saved_val).strip()
        if text == '' and ('image_url' in key_name or key_name in ('link_url', 'cta_url', 'url', 'source_mode')):
            return default_val
        return text

    def get_homepage_content(self):
        saved = (self.design_tokens_json or {}).get('homepage_content')
        return self._merge_homepage_node(self.DEFAULT_HOMEPAGE_CONTENT, saved)

    def to_dict(self):
        tokens = dict(self.design_tokens_json or {})
        tokens.pop('spotlight_bento', None)
        tokens.pop('hero_pin_on_scroll', None)
        tokens.pop('price_cards', None)
        tokens.pop('personalised_section', None)
        tokens.pop('homepage_content', None)
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
            'hero_pin_on_scroll': self.get_hero_pin_on_scroll(),
            'hero_badge_text': self.hero_badge_text,
            'hero_title_line1': self.hero_title_line1,
            'hero_title_line2': self.hero_title_line2,
            'hero_subtitle': self.hero_subtitle,
            'hero_primary_cta_text': self.hero_primary_cta_text,
            'hero_secondary_cta_text': self.hero_secondary_cta_text,
            'spotlight_bento': self.get_spotlight_bento(),
            'price_cards': self.get_price_cards(),
            'personalised_section': self.get_personalised_section(),
            'homepage_content': self.get_homepage_content(),
            'design_tokens': tokens,
        }
