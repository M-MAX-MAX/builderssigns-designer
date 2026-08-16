from django.db import migrations


def backfill_product(apps, schema_editor):
    Product = apps.get_model('designer', 'Product')
    TemplateGroup = apps.get_model('designer', 'TemplateGroup')

    if TemplateGroup.objects.filter(product__isnull=True).exists():
        banner_mesh, _ = Product.objects.get_or_create(
            slug='banner-mesh', defaults={'name': 'Banner Mesh', 'order': 1}
        )
        TemplateGroup.objects.filter(product__isnull=True).update(product=banner_mesh)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('designer', '0008_product_templategroup_product'),
    ]

    operations = [
        migrations.RunPython(backfill_product, noop_reverse),
    ]
