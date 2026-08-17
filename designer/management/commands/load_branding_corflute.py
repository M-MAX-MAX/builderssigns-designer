import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from designer.models import Product, Template, TemplateGroup

# Real Branding Corflute catalog, supplied by the designer as page1_bc.html.
# Scoped to only touch the Branding Corflute product so it's safe to run
# on production without risk to Banner Mesh / Compliance Corflute data.

BASIC_FIELDS = [
    {'key': 'website', 'label': 'Website Link', 'type': 'url', 'required': True},
    {'key': 'phone', 'label': 'Phone Number', 'type': 'text', 'required': True},
    {'key': 'builders_no', 'label': 'Builders No.', 'type': 'text', 'required': True},
]

FULL_FIELDS = BASIC_FIELDS + [
    {
        'key': 'social_media',
        'label': 'Social Media',
        'type': 'social',
        'required': True,
        'platforms': ['Facebook', 'Instagram'],
    },
    {'key': 'qr_code', 'label': 'Generate QR Code', 'type': 'url', 'required': True},
    {
        'key': 'association',
        'label': 'Association',
        'type': 'choice',
        'required': False,
        'choices': ['Master Builders', 'HIA'],
        'note': "Have a different association? Upload it along with your logo below.",
    },
]

FULL_CUSTOM_FIELDS = FULL_FIELDS + [
    {'key': 'custom_text', 'label': 'Custom Text', 'type': 'text', 'required': False},
]

UPLOADS = 'https://builderssigns.com.au/wp-content/uploads/2026/07/Branding-Corflutes-Templates'

GROUPS = [
    {
        'name': 'Logo + Website Link + Contact/Builders No. (Portrait)',
        'slug': 'branding-corflute-basic-portrait',
        'order': 1,
        'field_schema': BASIC_FIELDS,
        'templates': [
            (f'Basic Portrait {i}', f'{UPLOADS}_{i}-Branding-Corflute-Logo-Contact-Builders-No-Portrait-1.jpg')
            for i in (1, 2, 3)
        ],
    },
    {
        'name': 'Logo + Website Link + Contact/Builders No. + Social Media/Association + QR Code (Portrait)',
        'slug': 'branding-corflute-full-portrait',
        'order': 2,
        'field_schema': FULL_FIELDS,
        'templates': [
            (f'Full Details Portrait {n}', f'{UPLOADS}_{i}-Branding-Corflute-Contact-Builders-No.-Social-Media-Association-QR-Code-Portrait-1.jpg')
            for n, i in enumerate((4, 5, 6), start=1)
        ],
    },
    {
        'name': 'Logo + Website Link + Contact/Builders No. + Social Media/Association + QR Code + Custom Text (Portrait)',
        'slug': 'branding-corflute-custom-portrait',
        'order': 3,
        'field_schema': FULL_CUSTOM_FIELDS,
        'templates': [
            (f'Custom Text Portrait {i}', f'{UPLOADS}_{i}-BC-Logo-Contact-Builders-No.-Social-Media-Association-QR-Code-Custom-Text-Portrait.jpg')
            for i in (1, 2, 3)
        ],
    },
    {
        'name': 'Logo + Website Link + Contact/Builders No. (Landscape)',
        'slug': 'branding-corflute-basic-landscape',
        'order': 4,
        'field_schema': BASIC_FIELDS,
        'templates': [
            (f'Basic Landscape {i}', f'{UPLOADS}_{i}-Branding-Corflute-Logo-Contact-Builders-No-Landscape-1.jpg')
            for i in (1, 2, 3, 4)
        ],
    },
    {
        'name': 'Logo + Website Link + Contact/Builders No. + Social Media/Association + QR Code (Landscape)',
        'slug': 'branding-corflute-full-landscape',
        'order': 5,
        'field_schema': FULL_FIELDS,
        'templates': [
            (f'Full Details Landscape {n}', f'{UPLOADS}_{i}-Branding-Corflute-Logo-Contact-Builders-No-Social-Media-Association-QR-Code-Landscape-1.jpg')
            for n, i in enumerate((5, 6, 7, 8), start=1)
        ],
    },
    {
        'name': 'Logo + Website Link + Contact/Builders No. + Social Media/Association + QR Code + Custom Text (Landscape)',
        'slug': 'branding-corflute-custom-landscape',
        'order': 6,
        'field_schema': FULL_CUSTOM_FIELDS,
        'templates': [
            (f'Custom Text Landscape {i}', f'{UPLOADS}_{i}-Branding-Corflute-Logo-Contact-Builders-No-Social-Media-Association-QR-Code-CustomTxT-L.jpg')
            for i in (1, 2, 3, 4)
        ],
    },
]

# Old placeholder group created before the real catalog was available.
OLD_PLACEHOLDER_GROUP_SLUG = 'branding-corflute-logo-only'


class Command(BaseCommand):
    help = 'Load the real Branding Corflute template catalog (6 groups, 21 templates) with live images.'

    def handle(self, *args, **options):
        product = Product.objects.filter(slug='branding-corflute').first()
        if not product:
            self.stdout.write(self.style.ERROR(
                "No Product with slug 'branding-corflute' found — run seed_templates first."
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
                        template.svg_asset.save(f'{slug}.jpg', ContentFile(data), save=True)
                        self.stdout.write(f'  fetched image for {template.name}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  could not fetch image for {template.name}: {e}'))

        self.stdout.write(self.style.SUCCESS('Branding Corflute catalog loaded.'))
