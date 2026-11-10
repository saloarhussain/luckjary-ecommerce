from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Category, Material, Collection, Product, ProductImage, ProductReview
from orders.models import Coupon, Order, OrderItem, OrderStatusUpdate
from accounts.models import Address
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds database with realistic luxury jewelry catalog, users, addresses, and orders'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Luckjary luxury database...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            email='admin@luckjary.com',
            defaults={
                'username': 'admin',
                'first_name': 'Eleanor',
                'last_name': 'Vanderbilt',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True,
            }
        )
        if created:
            admin_user.set_password('admin12345')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin: admin@luckjary.com / admin12345"))

        # 2. Customer User
        customer, created = User.objects.get_or_create(
            email='isabella.vance@example.com',
            defaults={
                'username': 'isabellavance',
                'first_name': 'Isabella',
                'last_name': 'Vance',
                'is_email_verified': True,
                'phone_number': '+1 (212) 555-0198',
            }
        )
        if created:
            customer.set_password('luxury12345')
            customer.save()
            self.stdout.write(self.style.SUCCESS("Created customer: isabella.vance@example.com / luxury12345"))

        # Customer Addresses
        Address.objects.get_or_create(
            user=customer,
            street_address="740 Park Avenue, Apt 14B",
            city="New York",
            state_province="NY",
            postal_code="10021",
            country="United States",
            defaults={
                'full_name': 'Isabella Vance',
                'phone_number': '+1 (212) 555-0198',
                'address_type': 'shipping',
                'is_default': True,
            }
        )

        Address.objects.get_or_create(
            user=customer,
            street_address="320 Ocean Drive",
            city="Miami Beach",
            state_province="FL",
            postal_code="33139",
            country="United States",
            defaults={
                'full_name': 'Isabella Vance',
                'phone_number': '+1 (212) 555-0198',
                'address_type': 'billing',
                'is_default': False,
            }
        )

        # 3. Categories
        categories_data = [
            {
                'name': 'Rings',
                'description': 'Handcrafted engagement rings, diamond bands, and signature cocktail rings sculpted in 18K gold and platinum.',
                'image_url': 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80',
                'is_featured': True,
                'order': 1
            },
            {
                'name': 'Necklaces',
                'description': 'Delicate diamond pendants, radiant gemstone collars, and cascading golden chains designed for timeless allure.',
                'image_url': 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80',
                'is_featured': True,
                'order': 2
            },
            {
                'name': 'Earrings',
                'description': 'From minimalist diamond huggies to luminous chandelier drops, elevate every glance with radiant craftsmanship.',
                'image_url': 'https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=800&q=80',
                'is_featured': True,
                'order': 3
            },
            {
                'name': 'Bracelets',
                'description': 'Signature tennis bracelets and polished architectural cuffs fashioned from solid precious metals.',
                'image_url': 'https://images.unsplash.com/photo-1611591475870-760144f8ea56?auto=format&fit=crop&w=800&q=80',
                'is_featured': True,
                'order': 4
            },
            {
                'name': 'Bridal & High Jewelry',
                'description': 'Masterpiece heirloom creations commemorating lifelong love, crafted with certified D-flawless diamonds.',
                'image_url': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=800&q=80',
                'is_featured': True,
                'order': 5
            },
        ]
        cat_map = {}
        for c in categories_data:
            cat, _ = Category.objects.get_or_create(name=c['name'], defaults=c)
            cat_map[c['name']] = cat

        # 4. Materials
        materials_data = [
            ('18K Solid Yellow Gold', '18K Yellow Gold'),
            ('18K White Gold', '18K White Gold'),
            ('18K Rose Gold', '18K Rose Gold'),
            ('Platinum 950', 'Platinum'),
            ('925 Sterling Silver', 'Sterling Silver'),
            ('Freshwater Cultured Pearl', 'South Sea Pearl'),
            ('VVS1 Lab-Grown Diamonds', 'VVS Diamonds'),
            ('Natural Colombian Emerald', 'Colombian Emerald'),
            ('Royal Ceylon Sapphire', 'Royal Sapphire'),
        ]
        mat_map = {}
        for name, badge in materials_data:
            mat, _ = Material.objects.get_or_create(name=name, defaults={'badge_label': badge})
            mat_map[name] = mat

        # 5. Collections
        collections_data = [
            {
                'name': 'Solstice Heritage',
                'subtitle': 'Timeless architecture reimagined in pure 18K gold and solitaire diamonds.',
                'description': 'Inspired by classical Roman column symmetry and sun-drenched European coasts.',
                'banner_image': 'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'name': 'L\'Aura Fine Bridal',
                'subtitle': 'Eternal symbols of devotion forged with certified sustainable diamonds.',
                'description': 'Designed to accompany you on life’s most profound milestones with unmatched brilliance.',
                'banner_image': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'name': 'Celestial Luminary',
                'subtitle': 'Starry constellations captured in pave-encrusted precious stones.',
                'description': 'Shimmering micro-pave silhouettes that dance with ambient light from dawn till dusk.',
                'banner_image': 'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'name': 'Petite Minimalist',
                'subtitle': 'Subtle luxury designed for every day, effortless elegance.',
                'description': 'Whisper-thin solid gold chains and geometric accents tailored for effortless stacking.',
                'banner_image': 'https://images.unsplash.com/photo-1602751584552-8ba73aad10e1?auto=format&fit=crop&w=1200&q=80',
            },
        ]
        coll_map = {}
        for col in collections_data:
            c_obj, _ = Collection.objects.get_or_create(name=col['name'], defaults=col)
            coll_map[col['name']] = c_obj

        # 6. Luxury Products
        products_data = [
            {
                'title': 'The Celestia Solitaire Diamond Ring',
                'subtitle': '18K Solid Yellow Gold featuring a 1.80 ctw Oval Cut Lab Diamond',
                'sku': 'LCK-RNG-001',
                'category': cat_map['Rings'],
                'collection': coll_map['Solstice Heritage'],
                'materials': [mat_map['18K Solid Yellow Gold'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'classic',
                'price': 2450.00,
                'compare_at_price': 2850.00,
                'inventory': 14,
                'is_featured': True,
                'is_bestseller': True,
                'karat_metal': '18K Solid Yellow Gold (Hallmarked)',
                'gemstone': '1.80 ctw Oval Brilliant Lab Diamond (Color E, Clarity VVS1)',
                'carat_weight': '1.80 Carats Total Weight',
                'chain_length_or_size': 'Available in US Sizes 4 - 10 (Complimentary Resizing)',
                'dimensions': '8.8mm x 6.2mm Center Stone with 1.8mm Comfort Fit Band',
                'certification': 'IGI Certified Diamond & Luckjary Lifetime Guarantee',
                'description': 'The Celestia Solitaire is our definitive ode to eternal romance. Featuring an elongated oval-cut VVS1 diamond held in a refined four-prong hidden halo setting, this ring maximizes light return from every angle. Hand-finished by our master goldsmiths in New York.',
                'images': [
                    'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1603561591411-07134e71a2a9?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1598560917505-59a3ad559071?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1588444837495-c6cfeb53f32d?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': "L'Étoile Emerald & Diamond Trilogy Ring",
                'subtitle': '18K White Gold with Natural Colombian Emerald and Trapezoid Diamonds',
                'sku': 'LCK-RNG-002',
                'category': cat_map['Rings'],
                'collection': coll_map['Solstice Heritage'],
                'materials': [mat_map['18K White Gold'], mat_map['Natural Colombian Emerald'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'art_deco',
                'price': 3200.00,
                'compare_at_price': 3600.00,
                'inventory': 8,
                'is_featured': True,
                'is_bestseller': False,
                'karat_metal': '18K Solid White Gold with Rhodium Plating',
                'gemstone': '2.10 ctw Octagonal Muzo Colombian Emerald & 0.60 ctw Side Diamonds',
                'carat_weight': '2.70 Carats Total Weight',
                'chain_length_or_size': 'US Sizes 5 - 9',
                'dimensions': '9.0mm x 7.0mm Emerald Face',
                'certification': 'Gübelin Gem Lab Certificate & Luckjary Dossier',
                'description': 'Representing the past, present, and future, the L\'Étoile Trilogy Ring presents a vividly saturated deep-green natural emerald flanked by precision step-cut trapezoid diamonds. An enduring tribute to classic high jewelry glamour.',
                'images': [
                    'https://images.unsplash.com/photo-1603561591411-07134e71a2a9?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Aura Micro-Pavé Eternity Band',
                'subtitle': '18K Rose Gold Continuous Micro-Pavé Diamond Band',
                'sku': 'LCK-RNG-003',
                'category': cat_map['Rings'],
                'collection': coll_map['Petite Minimalist'],
                'materials': [mat_map['18K Rose Gold'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'minimalist',
                'price': 1150.00,
                'compare_at_price': 1300.00,
                'inventory': 22,
                'is_featured': False,
                'is_bestseller': True,
                'karat_metal': '18K Solid Rose Gold',
                'gemstone': '0.90 ctw Round Brilliant Diamonds (DEF Color, VS+ Clarity)',
                'carat_weight': '0.90 ctw',
                'chain_length_or_size': 'US Sizes 4 - 8',
                'dimensions': '2.0mm Band Width with French-cut setting',
                'certification': 'Luckjary Certificate of Authenticity',
                'description': 'Slender yet commanding, the Aura Eternity Band encircles your finger in unbroken starlight. Specially micro-set with microscopic prongs to ensure zero snagging and supreme day-to-night comfort.',
                'images': [
                    'https://images.unsplash.com/photo-1598560917505-59a3ad559071?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Lumière Teardrop Diamond Solitaire Pendant',
                'subtitle': '18K Yellow Gold with 1.25 ctw Pear Cut Diamond',
                'sku': 'LCK-NCK-001',
                'category': cat_map['Necklaces'],
                'collection': coll_map['Solstice Heritage'],
                'materials': [mat_map['18K Solid Yellow Gold'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'classic',
                'price': 1650.00,
                'compare_at_price': 1950.00,
                'inventory': 18,
                'is_featured': True,
                'is_bestseller': True,
                'is_new_arrival': True,
                'karat_metal': '18K Solid Yellow Gold Chain & Bezel',
                'gemstone': '1.25 ctw Pear-Shaped Diamond (VVS1, E Color)',
                'carat_weight': '1.25 Carats',
                'chain_length_or_size': 'Adjustable 16", 17", and 18" lengths with signature clasp',
                'dimensions': '9.5mm length x 6.0mm width pendant',
                'certification': 'IGI Lab Diamond Certificate',
                'description': 'Resting gracefully along the collarbone, the Lumière Teardrop Pendant captures purity and grace. The pear-cut diamond is set in an open-back bezel that catches every ray of sunshine.',
                'images': [
                    'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Sirena South Sea Baroque Pearl Choker',
                'subtitle': 'Genuine Luminous South Sea Pearl on Hand-Knotted Silk with 18K Clasp',
                'sku': 'LCK-NCK-002',
                'category': cat_map['Necklaces'],
                'collection': coll_map['Celestial Luminary'],
                'materials': [mat_map['Freshwater Cultured Pearl'], mat_map['18K Solid Yellow Gold']],
                'style': 'classic',
                'price': 1890.00,
                'compare_at_price': 2200.00,
                'inventory': 10,
                'is_featured': True,
                'is_bestseller': False,
                'karat_metal': '18K Yellow Gold Custom Ball Clasp with Safety Mechanism',
                'gemstone': '11-13mm AAA Lustre Golden South Sea Pearls',
                'carat_weight': 'N/A (Natural Pearls)',
                'chain_length_or_size': '16.5" Collar Length',
                'dimensions': 'Graduated 11mm to 13.5mm center pearl',
                'certification': 'GIA Pearl Identification & Grading Report',
                'description': 'Each pearl in the Sirena Choker was individually hand-selected over 18 months for its organic silhouette, mirror-like iridescence, and warm champagne overtone. Strung on double-knotted pure Japanese silk.',
                'images': [
                    'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Imperial Tennis Diamond Collet Necklace',
                'subtitle': 'Platinum 950 Handset with 8.5 ctw Brilliant Cut Diamonds',
                'sku': 'LCK-NCK-003',
                'category': cat_map['Bridal & High Jewelry'],
                'collection': coll_map['L\'Aura Fine Bridal'],
                'materials': [mat_map['Platinum 950'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'bridal',
                'price': 5400.00,
                'compare_at_price': 6200.00,
                'inventory': 5,
                'is_featured': True,
                'is_bestseller': False,
                'karat_metal': 'Solid Platinum 950 High Polish',
                'gemstone': '8.50 ctw Round Ideal Cut Diamonds (D-F Color, VS1+)',
                'carat_weight': '8.50 ctw',
                'chain_length_or_size': '17" Standard Riviera Length',
                'dimensions': 'Individual links graduated from 3.2mm to 4.5mm center',
                'certification': 'Complete IGI Dossier and Serialized Inscription',
                'description': 'A triumph of high jewelry craftsmanship. The Imperial Diamond Tennis Necklace features seamless continuous articulating links that lie perfectly flat against the neckline without rolling or flipping.',
                'images': [
                    'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Minimalist Crescent Huggie Diamond Hoops',
                'subtitle': '18K Yellow Gold with In-and-Out Pave Diamonds',
                'sku': 'LCK-EAR-001',
                'category': cat_map['Earrings'],
                'collection': coll_map['Petite Minimalist'],
                'materials': [mat_map['18K Solid Yellow Gold'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'minimalist',
                'price': 580.00,
                'compare_at_price': 690.00,
                'inventory': 35,
                'is_featured': False,
                'is_bestseller': True,
                'karat_metal': '18K Solid Yellow Gold',
                'gemstone': '0.35 ctw Hand-Selected White Diamonds',
                'carat_weight': '0.35 ctw Pair',
                'chain_length_or_size': '11mm Outer Diameter, 8.5mm Inner Clearance',
                'dimensions': '1.5mm Profile Width with Secure Click Lock',
                'certification': 'Luckjary Authenticity Hallmark',
                'description': 'The everyday luxury essential. Sized for comfortable 24/7 wear, our Crescent Huggies hug the lobe with effortless grace and sparkle from every perspective thanks to our dual-facing pave.',
                'images': [
                    'https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1588444837495-c6cfeb53f32d?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Giselle Cascading Diamond Chandelier Earrings',
                'subtitle': '18K White Gold Dramatic Art Deco Drop Earrings',
                'sku': 'LCK-EAR-002',
                'category': cat_map['Bridal & High Jewelry'],
                'collection': coll_map['L\'Aura Fine Bridal'],
                'materials': [mat_map['18K White Gold'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'bridal',
                'price': 3450.00,
                'compare_at_price': 3900.00,
                'inventory': 6,
                'is_featured': True,
                'is_bestseller': False,
                'karat_metal': '18K Solid White Gold',
                'gemstone': '3.20 ctw Marquise, Pear, and Round Diamonds',
                'carat_weight': '3.20 ctw Pair',
                'chain_length_or_size': '45mm Total Drop Length',
                'dimensions': '12mm Maximum Width',
                'certification': 'Luckjary Master Atelier Certificate',
                'description': 'Designed for galas, red carpet entrances, and black-tie bridal moments. The Giselle Earrings shimmer with dynamic fluidity as you move, capturing dramatic candlelight brilliance.',
                'images': [
                    'https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Royal Sapphire & Diamond Drop Earrings',
                'subtitle': '18K Yellow Gold with Pear-Cut Blue Sapphires',
                'sku': 'LCK-EAR-003',
                'category': cat_map['Earrings'],
                'collection': coll_map['Solstice Heritage'],
                'materials': [mat_map['18K Solid Yellow Gold'], mat_map['Royal Ceylon Sapphire'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'classic',
                'price': 2100.00,
                'compare_at_price': 2400.00,
                'inventory': 9,
                'is_featured': False,
                'is_bestseller': False,
                'karat_metal': '18K Yellow Gold',
                'gemstone': '2.40 ctw Pear Ceylon Royal Blue Sapphires with 0.50 ctw Diamonds',
                'carat_weight': '2.90 ctw Total',
                'chain_length_or_size': '26mm Drop Length',
                'dimensions': '8mm x 6mm Sapphire Pear',
                'certification': 'Luckjary Precious Gemstone Certificate',
                'description': 'A timeless tribute to royal elegance. Vivid royal blue sapphires are crowned by diamond clusters, creating an aristocratic contrast against warm 18K yellow gold.',
                'images': [
                    'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'The Sovereign Diamond Tennis Bracelet',
                'subtitle': '18K Solid Yellow Gold with 5.0 ctw Brilliant Cut Diamonds',
                'sku': 'LCK-BRC-001',
                'category': cat_map['Bracelets'],
                'collection': coll_map['Solstice Heritage'],
                'materials': [mat_map['18K Solid Yellow Gold'], mat_map['VVS1 Lab-Grown Diamonds']],
                'style': 'classic',
                'price': 4200.00,
                'compare_at_price': 4800.00,
                'inventory': 12,
                'is_featured': True,
                'is_bestseller': True,
                'karat_metal': '18K Solid Yellow Gold',
                'gemstone': '5.00 ctw Round Brilliant Diamonds (F Color, VS1 Clarity)',
                'carat_weight': '5.00 Carats Total Weight',
                'chain_length_or_size': '7.0" Length with Dual Hidden Safety Clasps',
                'dimensions': '2.8mm Width Profile',
                'certification': 'IGI Jewelry Report & Insurance Appraisal',
                'description': 'The quintessence of refined luxury. Each diamond in The Sovereign is four-prong basket set with micro-joints that flex silkily across the wrist, securing with our proprietary double-latch clasp.',
                'images': [
                    'https://images.unsplash.com/photo-1611591475870-760144f8ea56?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1602751584552-8ba73aad10e1?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?auto=format&fit=crop&w=1200&q=85',
                ]
            },
            {
                'title': 'Aurelia Twisted Cable Bangle',
                'subtitle': 'Solid 18K Yellow and White Gold Dual Tone Cuff',
                'sku': 'LCK-BRC-002',
                'category': cat_map['Bracelets'],
                'collection': coll_map['Petite Minimalist'],
                'materials': [mat_map['18K Solid Yellow Gold'], mat_map['18K White Gold']],
                'style': 'minimalist',
                'price': 1450.00,
                'compare_at_price': 1650.00,
                'inventory': 17,
                'is_featured': False,
                'is_bestseller': False,
                'is_new_arrival': True,
                'karat_metal': 'Solid 18K Two-Tone Gold',
                'gemstone': 'Twin Faceted Diamond Endcaps (0.20 ctw)',
                'carat_weight': '0.20 ctw',
                'chain_length_or_size': 'Inner Circumference 6.5" - 7.0"',
                'dimensions': '4mm Twisted Cable Gauge',
                'certification': 'Luckjary Fine Gold Certificate',
                'description': 'Masterfully twisted by hand, the Aurelia Bangle interlaces warm yellow gold and cool white gold cords into a resilient, flexible silhouette capped with brilliant diamond finials.',
                'images': [
                    'https://images.unsplash.com/photo-1602751584552-8ba73aad10e1?auto=format&fit=crop&w=1200&q=85',
                    'https://images.unsplash.com/photo-1611591475870-760144f8ea56?auto=format&fit=crop&w=1200&q=85',
                ]
            },
        ]

        for p_data in products_data:
            images = p_data.pop('images')
            materials = p_data.pop('materials')
            prod, created = Product.objects.get_or_create(sku=p_data['sku'], defaults=p_data)
            if created or not prod.images.exists():
                prod.materials.set(materials)
                for idx, img_url in enumerate(images):
                    ProductImage.objects.create(
                        product=prod,
                        image_url=img_url,
                        alt_text=f"{prod.title} view {idx+1}",
                        is_primary=(idx == 0),
                        order=idx
                    )

            # Seed realistic reviews
            if not prod.reviews.exists():
                ProductReview.objects.create(
                    product=prod,
                    user=customer,
                    author_name='Isabella V.',
                    rating=5,
                    title='Absolute perfection and incredible brilliance',
                    comment='The craftsmanship is truly second to none. The sparkle under natural sunlight took my breath away. The velvet box and certificate of authenticity made the unboxing feel like high haute joaillerie.',
                    is_verified_buyer=True,
                    is_approved=True
                )
                ProductReview.objects.create(
                    product=prod,
                    author_name='Sophia R.',
                    rating=5,
                    title='Worth every penny — Cartier quality at fair pricing',
                    comment='Ordered this for our 10th anniversary. Arrived in overnight insured FedEx packaging. My partner hasn’t taken it off since.',
                    is_verified_buyer=True,
                    is_approved=True
                )

        # 7. Coupons
        coupons = [
            {'code': 'LUCKJARY10', 'discount_percent': 10, 'is_percent': True, 'min_spend': 200, 'description': '10% Welcome Discount for fine jewelry lovers'},
            {'code': 'VIPLUCK20', 'discount_percent': 20, 'is_percent': True, 'min_spend': 1000, 'description': '20% Privé VIP Collector Discount'},
            {'code': 'GOLD100', 'discount_amount': 100, 'is_percent': False, 'min_spend': 500, 'description': '$100 off purchases above $500'},
        ]
        coupon_objs = {}
        for c in coupons:
            cpn, _ = Coupon.objects.get_or_create(code=c['code'], defaults=c)
            coupon_objs[c['code']] = cpn

        # 8. Sample Realistic Orders in Different OMS States (Customer & Admin tracking)
        orders_data = [
            {
                'order_number': 'LCK-202611-884102',
                'user': customer,
                'email': 'isabella.vance@example.com',
                'full_name': 'Isabella Vance',
                'phone': '+1 (212) 555-0198',
                'shipping_street': '740 Park Avenue, Apt 14B',
                'shipping_city': 'New York',
                'shipping_state': 'NY',
                'shipping_zip': '10021',
                'shipping_country': 'United States',
                'status': 'SHIPPED',
                'payment_status': 'PAID',
                'carrier': 'FedEx Luxury Priority Overnight',
                'tracking_number': 'FDX-994827104921-USA',
                'tracking_url': 'https://www.fedex.com/fedextrack/?trknbr=FDX994827104921USA',
                'subtotal': 4200.00,
                'shipping_cost': 0.00,
                'discount_amount': 420.00,
                'total_amount': 3780.00,
                'coupon': coupon_objs['LUCKJARY10'],
                'gift_wrapping': True,
                'gift_message': 'To my dearest Isabella, celebrating a glorious milestone. With all my love.',
                'items': [
                    {
                        'sku': 'LCK-BRC-001',
                        'size': '7.0" Wrist Length',
                        'material': '18K Solid Yellow Gold',
                        'price': 4200.00,
                        'qty': 1
                    }
                ],
                'updates': [
                    ('PENDING', 'Order Authenticated & Payment Secured', 'Payment verified via 3D Secure Luxury gateway. Assigned to master atelier.', 'Luckjary Financial Vault, New York'),
                    ('PROCESSING', 'Quality Inspection & Hand Polishing', 'Gemologist inspection passed with 100% score. Ultrasonic cleaned and packaged in signature velvet lockbox.', 'Luckjary Atelier, New York'),
                    ('SHIPPED', 'Dispatched with Armored FedEx Courier', 'Package in transit under high-security courier protocol. Direct signature required on delivery.', 'FedEx Air Hub, Newark, NJ'),
                ]
            },
            {
                'order_number': 'LCK-202611-739201',
                'user': customer,
                'email': 'isabella.vance@example.com',
                'full_name': 'Isabella Vance',
                'phone': '+1 (212) 555-0198',
                'shipping_street': '740 Park Avenue, Apt 14B',
                'shipping_city': 'New York',
                'shipping_state': 'NY',
                'shipping_zip': '10021',
                'shipping_country': 'United States',
                'status': 'DELIVERED',
                'payment_status': 'PAID',
                'carrier': 'Ferrari Armored Logistics / White Glove',
                'tracking_number': 'FAR-3329104882',
                'tracking_url': '#',
                'subtotal': 2450.00,
                'shipping_cost': 0.00,
                'discount_amount': 0.00,
                'total_amount': 2450.00,
                'gift_wrapping': True,
                'gift_message': 'Happy 30th Birthday to me!',
                'items': [
                    {
                        'sku': 'LCK-RNG-001',
                        'size': 'US Size 6.5',
                        'material': '18K Solid Yellow Gold',
                        'price': 2450.00,
                        'qty': 1
                    }
                ],
                'updates': [
                    ('PENDING', 'Order Placed & Confirmed', 'Order confirmed and registered into Luckjary registry.', 'New York, NY'),
                    ('PROCESSING', 'Master Setting & Ultrasonic Cleanse', 'Crafted and prepared in signature satin packaging.', 'Luckjary Atelier, NY'),
                    ('SHIPPED', 'In Transit via Armored White Glove Courier', 'Out for insured courier transit.', 'JFK Cargo Logistics, NY'),
                    ('DELIVERED', 'Delivered & Signed', 'Delivered safely to recipient at Park Ave residence. Signature confirmed.', '740 Park Ave, New York, NY'),
                ]
            },
            {
                'order_number': 'LCK-202611-194056',
                'user': None, # Guest Order
                'email': 'charlotte.dupre@gmail.com',
                'full_name': 'Charlotte Dupré',
                'phone': '+1 (415) 882-9901',
                'shipping_street': '1000 California Street',
                'shipping_city': 'San Francisco',
                'shipping_state': 'CA',
                'shipping_zip': '94108',
                'shipping_country': 'United States',
                'status': 'PROCESSING',
                'payment_status': 'PAID',
                'carrier': 'DHL Express Luxury Network',
                'tracking_number': 'DHL-8839201948',
                'tracking_url': '#',
                'subtotal': 1650.00,
                'shipping_cost': 0.00,
                'discount_amount': 165.00,
                'total_amount': 1485.00,
                'coupon': coupon_objs['LUCKJARY10'],
                'gift_wrapping': True,
                'gift_message': 'Happy Graduation, Charlotte!',
                'items': [
                    {
                        'sku': 'LCK-NCK-001',
                        'size': '18" Adjustable Chain',
                        'material': '18K Solid Yellow Gold',
                        'price': 1650.00,
                        'qty': 1
                    }
                ],
                'updates': [
                    ('PENDING', 'Guest Order Verified', 'Credit card transaction authenticated via Stripe.', 'San Francisco Gateway'),
                    ('PROCESSING', 'Custom Bezel Setting Underway', 'Artisan setting 1.25ct teardrop diamond into solid gold casing.', 'Luckjary Main Atelier'),
                ]
            },
            {
                'order_number': 'LCK-202611-304918',
                'user': None, # Guest Order
                'email': 'julian.stewart@icloud.com',
                'full_name': 'Julian Stewart',
                'phone': '+1 (310) 902-4411',
                'shipping_street': '9641 Sunset Blvd',
                'shipping_city': 'Beverly Hills',
                'shipping_state': 'CA',
                'shipping_zip': '90210',
                'shipping_country': 'United States',
                'status': 'PENDING',
                'payment_status': 'PAID',
                'carrier': 'FedEx Luxury Priority Overnight',
                'subtotal': 3450.00,
                'shipping_cost': 0.00,
                'discount_amount': 0.00,
                'total_amount': 3450.00,
                'gift_wrapping': True,
                'items': [
                    {
                        'sku': 'LCK-EAR-002',
                        'size': 'Standard Chandelier Post',
                        'material': '18K White Gold',
                        'price': 3450.00,
                        'qty': 1
                    }
                ],
                'updates': [
                    ('PENDING', 'Order Received', 'New order received. Awaiting atelier intake queue.', 'Beverly Hills Intake'),
                ]
            }
        ]

        for o_info in orders_data:
            items = o_info.pop('items')
            updates = o_info.pop('updates')
            ord_obj, created = Order.objects.get_or_create(order_number=o_info['order_number'], defaults=o_info)
            if created:
                for item in items:
                    prod = Product.objects.get(sku=item['sku'])
                    OrderItem.objects.create(
                        order=ord_obj,
                        product=prod,
                        product_name=prod.title,
                        product_sku=prod.sku,
                        product_image=prod.primary_image,
                        selected_size=item['size'],
                        selected_material=item['material'],
                        unit_price=item['price'],
                        quantity=item['qty']
                    )
                for st, title, desc, loc in updates:
                    OrderStatusUpdate.objects.create(
                        order=ord_obj,
                        status=st,
                        title=title,
                        description=desc,
                        location=loc
                    )

        self.stdout.write(self.style.SUCCESS("Luckjary database seeded successfully! Ready with premium inventory, categories, coupons, and orders."))
