from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    meta_title = models.CharField(max_length=150, blank=True)
    meta_description = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = f"{self.name} Collection | Fine Fashion Jewelry - Luckjary"
        if not self.meta_description:
            self.meta_description = f"Explore handcrafted {self.name.lower()} at Luckjary. Luxury solid gold, sterling silver, and ethically sourced diamond jewelry with complimentary gift packaging."
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:category_products', kwargs={'category_slug': self.slug})

    def __str__(self):
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    badge_label = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.badge_label:
            self.badge_label = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Collection(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    banner_image = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    STYLE_CHOICES = [
        ('classic', 'Timeless Classic'),
        ('minimalist', 'Modern Minimalist'),
        ('bridal', 'Bridal & High Glamour'),
        ('art_deco', 'Art Deco Vintage'),
        ('celestial', 'Celestial & Statement'),
    ]

    SIZE_CATEGORY_CHOICES = [
        ('ring', 'Ring Sizes (US 4 to 13 with half-sizes)'),
        ('necklace', 'Necklace Lengths (14" to 24")'),
        ('bracelet', 'Bracelet Circumferences (6.0" to 8.0")'),
        ('earring', 'Earring Fit & Security Backings'),
        ('universal', 'One Size / Universal Luxury Fit'),
        ('custom', 'Custom Size / Specification List'),
    ]

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    subtitle = models.CharField(max_length=255, blank=True, help_text="e.g., Handcrafted in 18K Solid Gold & VVS Diamonds")
    sku = models.CharField(max_length=60, unique=True)
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    materials = models.ManyToManyField(Material, related_name='products', blank=True)
    style = models.CharField(max_length=30, choices=STYLE_CHOICES, default='classic')

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Stock & Merchandising
    inventory = models.PositiveIntegerField(default=25)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    
    # Luxury Specifications & Precious Metals
    karat_metal = models.CharField(max_length=120, default='18K Solid Yellow Gold', help_text="Default primary metal for this piece")
    available_metals = models.CharField(
        max_length=400, 
        blank=True, 
        default='18K Solid Yellow Gold, 18K Solid White Gold, 18K Solid Rose Gold, Platinum 950',
        help_text="Comma-separated precious metal options available to the client on the product page. e.g. 18K Solid Yellow Gold, 18K Solid White Gold, 18K Solid Rose Gold, Platinum 950"
    )
    gemstone = models.CharField(max_length=150, blank=True, default='VVS Clarity Lab Diamonds')
    carat_weight = models.CharField(max_length=60, blank=True, default='1.25 ctw')
    
    # Sizing & Dimensions
    size_category = models.CharField(
        max_length=30, 
        choices=SIZE_CATEGORY_CHOICES, 
        default='ring', 
        blank=True,
        help_text="Select category sizing framework (Rings: US 4-13 with half-sizes, Necklaces: 14\"-24\", etc.)"
    )
    available_sizes = models.TextField(
        blank=True, 
        help_text="Custom sizes (one per line or comma-separated). Leave blank to automatically generate full standard sizing range for this category (e.g. US 4 through 13 with half-sizes for rings)."
    )
    chain_length_or_size = models.CharField(max_length=100, blank=True, default='US Sizes 4 - 13 (Complimentary Resizing)')
    dimensions = models.CharField(max_length=100, blank=True, default='14.5mm x 9.2mm')
    certification = models.CharField(max_length=120, default='Luckjary Seal & IGI Laboratory Certificate')

    # Descriptions
    description = models.TextField()
    craftsmanship_details = models.TextField(blank=True, default="Hand-forged by master jewellers using certified recycled precious metals and conflict-free gemstones. Every piece undergoes rigorous 5-stage microscopic inspection.")
    care_instructions = models.TextField(blank=True, default="Store in the provided velvet Luckjary lockbox. Avoid perfumes, lotion, and chlorine. Gently polish with the included microfiber jeweler cloth.")

    # SEO & Organic Growth
    meta_title = models.CharField(max_length=140, blank=True)
    meta_description = models.CharField(max_length=260, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True, default="luxury jewelry, 18k gold, handcrafted necklace, diamond ring, fine jewelry")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_title:
            self.meta_title = f"{self.title} | Luxury Jewelry - Luckjary"
        if not self.meta_description:
            self.meta_description = f"Discover the {self.title} by Luckjary. Crafted in {self.karat_metal} with {self.gemstone or 'flawless finish'}. Enjoy complimentary insured worldwide delivery & gift packaging."
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def metal_options(self):
        """Returns list of precious metal options available for this product."""
        if self.available_metals:
            options = [m.strip() for m in self.available_metals.split(',') if m.strip()]
            if options:
                return options
        default_metals = []
        if self.karat_metal:
            default_metals.append(self.karat_metal)
        for m in ['18K Solid Yellow Gold', '18K Solid White Gold', '18K Solid Rose Gold', 'Platinum 950']:
            if m not in default_metals:
                default_metals.append(m)
        return default_metals

    @property
    def size_options(self):
        """Returns list of size strings for dropdown selection."""
        if self.available_sizes:
            custom_list = []
            for line in self.available_sizes.replace('\n', ',').split(','):
                val = line.strip()
                if val:
                    custom_list.append(val)
            if custom_list:
                return custom_list

        cat_slug = self.category.slug.lower() if self.category else ''
        size_type = self.size_category or ('ring' if 'ring' in cat_slug else 'universal')

        if size_type == 'ring' or 'ring' in cat_slug:
            return [
                'US Size 4 (46.8mm circumference)',
                'US Size 4.5 (48.0mm circumference)',
                'US Size 5 (49.3mm circumference)',
                'US Size 5.5 (50.6mm circumference)',
                'US Size 6 (51.9mm circumference)',
                'US Size 6.5 (53.1mm circumference)',
                'US Size 7 (54.4mm - Most Popular)',
                'US Size 7.5 (55.7mm circumference)',
                'US Size 8 (57.0mm circumference)',
                'US Size 8.5 (58.3mm circumference)',
                'US Size 9 (59.5mm circumference)',
                'US Size 9.5 (60.8mm circumference)',
                'US Size 10 (62.1mm circumference)',
                'US Size 10.5 (63.4mm circumference)',
                'US Size 11 (64.6mm circumference)',
                'US Size 11.5 (65.9mm circumference)',
                'US Size 12 (67.2mm circumference)',
                'US Size 12.5 (68.5mm circumference)',
                'US Size 13 (69.7mm circumference)',
                'Custom Bespoke Sizing (Concierge will contact you)',
            ]
        elif size_type == 'necklace' or 'necklace' in cat_slug:
            return [
                '14" Choker Length (35.5cm)',
                '16" Standard Collar (40.6cm)',
                '18" Princess Length - Most Popular (45.7cm)',
                '20" Matinee Length (50.8cm)',
                '22" Opera Length (55.9cm)',
                '24" Lariat Length (61.0cm)',
                'Custom Bespoke Sizing (Concierge will contact you)',
            ]
        elif size_type == 'bracelet' or 'bracelet' in cat_slug:
            return [
                '6.0" (15.2cm - Petite Wrist)',
                '6.5" (16.5cm - Small Wrist)',
                '7.0" (17.8cm - Standard / Most Popular)',
                '7.5" (19.0cm - Medium Wrist)',
                '8.0" (20.3cm - Large Wrist)',
                'Custom Bespoke Sizing (Concierge will contact you)',
            ]
        elif size_type == 'earring' or 'earring' in cat_slug:
            return [
                'Standard Pierced Post & Friction Back',
                'Screw Back (High Security Locking)',
                'La Poussette Luxury Locking Back',
                'Clip-On (Non-Pierced Atelier Fitting)',
            ]
        else:
            if self.chain_length_or_size:
                return [self.chain_length_or_size, 'Custom Bespoke Sizing (Concierge will contact you)']
            return [
                'One Size / Universal Luxury Fit',
                'Custom Bespoke Sizing (Concierge will contact you)',
            ]

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            diff = self.compare_at_price - self.price
            return int((diff / self.compare_at_price) * 100)
        return 0

    @property
    def primary_image(self):
        first = self.images.filter(is_primary=True).first() or self.images.first()
        return first.image_url if first else "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=1000&q=80"

    @property
    def secondary_image(self):
        sec = self.images.filter(is_primary=False).first()
        return sec.image_url if sec else self.primary_image

    @property
    def image_list(self):
        """Returns ordered list of all unique image URLs for this product."""
        urls = [img.image_url for img in self.images.all() if img.image_url]
        if not urls:
            if self.primary_image:
                urls.append(self.primary_image)
            if self.secondary_image and self.secondary_image not in urls:
                urls.append(self.secondary_image)
        return urls

    @property
    def images_json(self):
        """Returns JSON string of image URLs for safe carousel dataset attribute."""
        import json
        return json.dumps(self.image_list)

    @property
    def average_rating(self):
        approved = self.reviews.filter(is_approved=True)
        if approved.exists():
            avg = approved.aggregate(models.Avg('rating'))['rating__avg']
            return round(avg, 1)
        return 5.0

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=600)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_primary', 'order']

    def __str__(self):
        return f"Image for {self.product.title} (Order: {self.order})"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=150)
    comment = models.TextField()
    is_verified_buyer = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ by {self.author_name} on {self.product.title}"
