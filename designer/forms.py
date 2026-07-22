from django import forms

# Google Fonts offered on step 2, matching the supplied design reference.
# Bold weight throughout — Merienda One, Anton, and Bebas Neue only ship one
# (already-heavy) weight on Google Fonts, so those load at 400 instead of a
# synthetic/faked 700.
FONT_OPTIONS = [
    {'value': 'inter', 'label': 'Inter (Default)', 'family': 'Inter', 'weight': 700},
    {'value': 'poppins', 'label': 'Poppins', 'family': 'Poppins', 'weight': 700},
    {'value': 'roboto_condensed', 'label': 'Roboto Condensed', 'family': 'Roboto Condensed', 'weight': 700},
    {'value': 'merienda_one', 'label': 'Merienda One', 'family': 'Merienda One', 'weight': 400},
    {'value': 'passion_one', 'label': 'Passion One', 'family': 'Passion One', 'weight': 700},
    {'value': 'oswald', 'label': 'Oswald', 'family': 'Oswald', 'weight': 700},
    {'value': 'merriweather', 'label': 'Merriweather', 'family': 'Merriweather', 'weight': 700},
    {'value': 'anton', 'label': 'Anton', 'family': 'Anton', 'weight': 400},
    {'value': 'bebas_neue', 'label': 'Bebas Neue', 'family': 'Bebas Neue', 'weight': 400},
    {'value': 'oxanium', 'label': 'Oxanium', 'family': 'Oxanium', 'weight': 700},
]
FONT_CHOICES = [(f['value'], f['label']) for f in FONT_OPTIONS] + [
    ('other', "Can't find my font - type it below")
]


class DetailsForm(forms.Form):
    """Universal fields (always shown) + dynamic fields built from the
    selected TemplateGroup.field_schema."""

    client_email = forms.EmailField(label='Your Email')
    order_number = forms.CharField(label='Order Number', max_length=100)
    background_colour = forms.CharField(
        label='Background Colour', widget=forms.TextInput(attrs={'type': 'color'})
    )
    font_choice = forms.ChoiceField(
        label='Choose Font', choices=FONT_CHOICES, required=False, initial='inter'
    )
    font_custom_text = forms.CharField(
        label="Can't find your brand font? Tell us what it is", required=False
    )
    comments = forms.CharField(label='Comments', widget=forms.Textarea, required=False)

    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        self.dynamic_field_keys = []
        if not group:
            return

        for field in group.field_schema:
            key = field['key']
            label = field['label']
            required = field.get('required', False)
            self.dynamic_field_keys.append(key)

            if field['type'] in ('text', 'url'):
                self.fields[key] = forms.CharField(label=label, required=required)

            elif field['type'] == 'social':
                self.fields[key] = forms.CharField(label=f'{label} Handle', required=required)
                self.fields[f'{key}_platforms'] = forms.MultipleChoiceField(
                    label=f'{label} Platforms',
                    choices=[(p, p) for p in field.get('platforms', [])],
                    widget=forms.CheckboxSelectMultiple,
                    required=required,
                )

            elif field['type'] == 'choice':
                self.fields[key] = forms.MultipleChoiceField(
                    label=label,
                    choices=[(c, c) for c in field.get('choices', [])],
                    widget=forms.CheckboxSelectMultiple,
                    required=required,
                )

    def extract_field_values(self, cleaned_data):
        """Pull just the dynamic (group-specific) answers into a plain dict
        for storage on DesignRequest.field_values."""
        values = {}
        for field in self.group.field_schema if self.group else []:
            key = field['key']
            if field['type'] == 'social':
                values[key] = {
                    'handle': cleaned_data.get(key, ''),
                    'platforms': cleaned_data.get(f'{key}_platforms', []),
                }
            elif field['type'] == 'choice':
                values[key] = {'choices': cleaned_data.get(key, [])}
            else:
                values[key] = cleaned_data.get(key, '')
        values['font_choice'] = cleaned_data.get('font_choice', '')
        values['font_custom_text'] = cleaned_data.get('font_custom_text', '')
        return values
