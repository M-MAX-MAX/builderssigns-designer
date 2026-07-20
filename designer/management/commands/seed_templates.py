from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from designer.models import Template, TemplateGroup

PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">
  <rect width="400" height="250" fill="#111111"/>
  <text x="30" y="140" fill="#ffffff" font-family="sans-serif" font-size="26" font-weight="bold">Builders Signs</text>
</svg>"""

GROUPS = [
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
                'type': 'choice_or_upload',
                'required': True,
                'choices': ['Master Builders', 'HIA'],
            },
        ],
        'templates': ['Full Centered', 'Full Left', 'Full Stacked', 'Full Banner'],
    },
]


class Command(BaseCommand):
    help = 'Seed TemplateGroup/Template rows with placeholder SVGs for local dev'

    def handle(self, *args, **options):
        for group_data in GROUPS:
            templates = group_data.pop('templates')
            group, created = TemplateGroup.objects.update_or_create(
                slug=group_data['slug'], defaults=group_data
            )
            self.stdout.write(f"{'Created' if created else 'Updated'} group: {group.name}")

            for i, label in enumerate(templates, start=1):
                slug = f"{group.slug}-{i}"
                template, created = Template.objects.get_or_create(
                    slug=slug,
                    defaults={'group': group, 'name': label, 'order': i},
                )
                if not template.svg_asset:
                    template.svg_asset.save(f'{slug}.svg', ContentFile(PLACEHOLDER_SVG), save=True)
                self.stdout.write(f"  - {template.name}")

        self.stdout.write(self.style.SUCCESS('Seed complete.'))
