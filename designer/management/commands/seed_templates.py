import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from designer.models import Product, Template, TemplateGroup

PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">
  <rect width="400" height="250" fill="#111111"/>
  <text x="30" y="140" fill="#ffffff" font-family="sans-serif" font-size="26" font-weight="bold">Builders Signs</text>
</svg>"""

BANNER_MESH_GROUPS = [
    {
        'name': 'Logo only',
        'slug': 'logo-only',
        'order': 1,
        'field_schema': [],
        'templates': ['Logo Centered', 'Logo Left', 'Logo Stacked', 'Logo Banner'],
    },
    {
        'name': 'Logo + Contact + Builders No.',
        'slug': 'logo-contact-builders-no',
        'order': 2,
        'field_schema': [
            {'key': 'phone', 'label': 'Phone Number', 'type': 'text', 'required': True},
            {'key': 'builders_no', 'label': 'Builders No.', 'type': 'text', 'required': True},
        ],
        'templates': ['Contact Centered', 'Contact Left', 'Contact Stacked', 'Contact Banner'],
    },
    {
        'name': 'Logo + Contact + Builders No. + Social/Association + QR Code',
        'slug': 'logo-contact-social-qr',
        'order': 3,
        'field_schema': [
            {'key': 'phone', 'label': 'Phone Number', 'type': 'text', 'required': True},
            {'key': 'builders_no', 'label': 'Builders No.', 'type': 'text', 'required': True},
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
        ],
        'templates': ['Full Centered', 'Full Left', 'Full Stacked', 'Full Banner'],
    },
]

PRODUCTS = [
    {
        'name': 'Banner Mesh',
        'slug': 'banner-mesh',
        'order': 1,
        'card_image_url': 'https://builderssigns.com.au/wp-content/uploads/2026/07/Banner-Mesh-Templates.png',
        'groups': BANNER_MESH_GROUPS,
    },
    {
        # Placeholder groups only, for local testing of the multi-product
        # flow — real groups/templates should be added via /admin/.
        'name': 'Branding Corflute',
        'slug': 'branding-corflute',
        'order': 2,
        'card_image_url': 'https://builderssigns.com.au/wp-content/uploads/2026/07/Branding-Corflutes-Templates.png',
        'groups': [
            {
                'name': 'Logo only',
                'slug': 'branding-corflute-logo-only',
                'order': 1,
                'field_schema': [],
                'templates': ['Branding Corflute Logo Centered', 'Branding Corflute Logo Left'],
            },
        ],
    },
    {
        # Real catalog is loaded separately via `load_compliance_corflute`
        # (scoped command, safe to run on production) — this just creates
        # the Product row + card image.
        'name': 'Compliance Corflute',
        'slug': 'compliance-corflute',
        'order': 3,
        'card_image_url': 'https://builderssigns.com.au/wp-content/uploads/2026/07/Compliance-Corflutes-Templates.png',
        'groups': [],
    },
]


class Command(BaseCommand):
    help = 'Seed Product/TemplateGroup/Template rows with placeholder SVGs for local dev'

    def handle(self, *args, **options):
        for product_data in PRODUCTS:
            product_data = dict(product_data)
            groups = product_data.pop('groups')
            card_image_url = product_data.pop('card_image_url', None)

            product, created = Product.objects.update_or_create(
                slug=product_data['slug'], defaults=product_data
            )
            self.stdout.write(f"{'Created' if created else 'Updated'} product: {product.name}")

            if card_image_url and not product.card_image:
                try:
                    with urllib.request.urlopen(card_image_url, timeout=10) as resp:
                        product.card_image.save(
                            f'{product.slug}.png', ContentFile(resp.read()), save=True
                        )
                    self.stdout.write('  fetched card image')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  could not fetch card image: {e}'))

            for group_data in groups:
                templates = group_data.pop('templates')
                group, created = TemplateGroup.objects.update_or_create(
                    slug=group_data['slug'], defaults={**group_data, 'product': product}
                )
                self.stdout.write(f"  {'Created' if created else 'Updated'} group: {group.name}")

                for i, label in enumerate(templates, start=1):
                    slug = f"{group.slug}-{i}"
                    template, created = Template.objects.get_or_create(
                        slug=slug,
                        defaults={'group': group, 'name': label, 'order': i},
                    )
                    if not template.svg_asset:
                        template.svg_asset.save(f'{slug}.svg', ContentFile(PLACEHOLDER_SVG), save=True)
                    self.stdout.write(f"    - {template.name}")

        self.stdout.write(self.style.SUCCESS('Seed complete.'))
