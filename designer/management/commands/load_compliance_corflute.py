import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from designer.models import Product, Template, TemplateGroup

# Real Compliance Corflute catalog, supplied by the designer as page1_cc.html.
# Scoped to only touch the Compliance Corflute product so it's safe to run
# on production without risk to Banner Mesh / Branding Corflute data.
GROUPS = [
    {
        'name': 'Portrait',
        'slug': 'compliance-corflute-portrait',
        'order': 1,
        'field_schema': [],
        'templates': [
            ('Compliance Corflute Portrait 1', 'https://builderssigns.com.au/wp-content/uploads/2026/08/6.png'),
            ('Compliance Corflute Portrait 2', 'https://builderssigns.com.au/wp-content/uploads/2026/08/10.png'),
            ('Compliance Corflute Portrait 3', 'https://builderssigns.com.au/wp-content/uploads/2026/08/3.png'),
            ('Compliance Corflute Portrait 4', 'https://builderssigns.com.au/wp-content/uploads/2026/08/1.png'),
            ('Compliance Corflute Portrait 5', 'https://builderssigns.com.au/wp-content/uploads/2026/08/5.png'),
            ('Compliance Corflute Portrait 6', 'https://builderssigns.com.au/wp-content/uploads/2026/08/4.png'),
        ],
    },
    {
        'name': 'Landscape',
        'slug': 'compliance-corflute-landscape',
        'order': 2,
        'field_schema': [],
        'templates': [
            ('Compliance Corflute Landscape 1', 'https://builderssigns.com.au/wp-content/uploads/2026/08/8.png'),
            ('Compliance Corflute Landscape 2', 'https://builderssigns.com.au/wp-content/uploads/2026/08/7.png'),
            ('Compliance Corflute Landscape 3', 'https://builderssigns.com.au/wp-content/uploads/2026/08/9.png'),
            ('Compliance Corflute Landscape 4', 'https://builderssigns.com.au/wp-content/uploads/2026/08/11.png'),
        ],
    },
]

# Old placeholder group created before the real catalog was available.
OLD_PLACEHOLDER_GROUP_SLUG = 'compliance-corflute-logo-only'


class Command(BaseCommand):
    help = 'Load the real Compliance Corflute template catalog (Portrait/Landscape) with live images.'

    def handle(self, *args, **options):
        product = Product.objects.filter(slug='compliance-corflute').first()
        if not product:
            self.stdout.write(self.style.ERROR(
                "No Product with slug 'compliance-corflute' found — run seed_templates first."
            ))
            return

        old_group = TemplateGroup.objects.filter(slug=OLD_PLACEHOLDER_GROUP_SLUG, product=product).first()
        if old_group:
            count = old_group.templates.count()
            old_group.templates.all().delete()
            old_group.delete()
            self.stdout.write(f'Removed old placeholder group ({count} templates).')

        for group_data in GROUPS:
            templates = group_data.pop('templates')
            group, created = TemplateGroup.objects.update_or_create(
                slug=group_data['slug'], defaults={**group_data, 'product': product}
            )
            self.stdout.write(f"{'Created' if created else 'Updated'} group: {group.name}")

            for i, (label, image_url) in enumerate(templates, start=1):
                slug = f"{group.slug}-{i}"
                template, created = Template.objects.get_or_create(
                    slug=slug, defaults={'group': group, 'name': label, 'order': i}
                )
                if not template.svg_asset:
                    try:
                        with urllib.request.urlopen(image_url, timeout=10) as resp:
                            data = resp.read()
                        template.svg_asset.save(f'{slug}.png', ContentFile(data), save=True)
                        self.stdout.write(f'  fetched image for {template.name}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  could not fetch image for {template.name}: {e}'))

        self.stdout.write(self.style.SUCCESS('Compliance Corflute catalog loaded.'))
