from django.db import migrations

def seed_materials(apps, schema_editor):
    Material = apps.get_model('catalog', 'Material')
    materials_data = [
        ('18K Gold Vermeil & Demifine', '18k-gold-vermeil-demifine', 'Demifine', 'Electroplated finish on sterling base'),
        ('18K Rose Gold', '18k-rose-gold', '18K Rose Gold', 'Solid gold warm copper blush alloy'),
        ('18K Solid Yellow Gold', '18k-solid-yellow-gold', '18K Yellow Gold', 'Traditional high-carat royal gold'),
        ('18K White Gold', '18k-white-gold', '18K White Gold', 'Premium palladium-rich white alloy'),
        ('925 Sterling Silver', '925-sterling-silver', 'Sterling Silver', 'Anti-tarnish dipped fine silver'),
        ('Freshwater Cultured Pearl', 'freshwater-cultured-pearl', 'South Sea Pearl', 'Organic gem, high overtone luster'),
        ('Natural Colombian Emerald', 'natural-colombian-emerald', 'Colombian Emerald', 'Beryl variety with fine jardin inclusions'),
        ('Platinum 950', 'platinum-950', 'Platinum', 'Pure dense noble metal alloy'),
        ('Royal Ceylon Sapphire', 'royal-ceylon-sapphire', 'Royal Sapphire', 'Sri Lankan natural corundum'),
        ('VVS1 Lab-Grown Diamonds', 'vvs1-lab-grown-diamonds', 'VVS Diamonds', 'CVD crystallized carbon, IGI certified'),
    ]
    for name, slug, badge, desc in materials_data:
        obj, created = Material.objects.get_or_create(
            name=name,
            defaults={'slug': slug, 'badge_label': badge, 'description': desc}
        )
        if not created:
            if not obj.slug:
                obj.slug = slug
            if not obj.badge_label:
                obj.badge_label = badge
            if not obj.description:
                obj.description = desc
            obj.save()

def reverse_seed(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_alter_product_available_metals_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_materials, reverse_seed),
    ]
