from django import forms

FONT_CHOICES = [
    ('inter', 'Inter (Default)'),
    ('your_company', 'Your Company'),
    ('other', "Other — tell us below"),
]


class DetailsForm(forms.Form):
    """Universal fields (always shown) + dynamic fields built from the
    selected TemplateGroup.field_schema."""

    client_email = forms.EmailField(label='Your Email')
    order_number = forms.CharField(label='Order Number', max_length=100)
    background_colour = forms.CharField(
        label='Background Colour', widget=forms.TextInput(attrs={'type': 'color'})
    )
    font_choice = forms.ChoiceField(label='Choose Font', choices=FONT_CHOICES, required=False)
    font_custom_text = forms.CharField(
        label="Can't find your brand font? Tell us what it is", required=False
    )
    style_guide_upload = forms.FileField(label='Upload Brand Style Here', required=False)
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

            elif field['type'] == 'choice_or_upload':
                self.fields[key] = forms.MultipleChoiceField(
                    label=label,
                    choices=[(c, c) for c in field.get('choices', [])],
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                )
                self.fields[f'{key}_upload'] = forms.FileField(
                    label=f'Or upload your own {label.lower()} logo', required=False
                )

    def clean(self):
        cleaned = super().clean()
        if not self.group:
            return cleaned

        # choice_or_upload fields: require one of the two sub-fields, not both empty
        for field in self.group.field_schema:
            if field['type'] == 'choice_or_upload':
                key = field['key']
                if not cleaned.get(key) and not cleaned.get(f'{key}_upload'):
                    if field.get('required'):
                        self.add_error(key, 'Choose an option or upload your own.')
        return cleaned

    def extract_field_values(self, cleaned_data):
        """Pull just the dynamic (group-specific) answers into a plain dict
        for storage on DesignRequest.field_values — files are handled by the
        view separately since JSONField can't hold them."""
        values = {}
        for field in self.group.field_schema if self.group else []:
            key = field['key']
            if field['type'] == 'social':
                values[key] = {
                    'handle': cleaned_data.get(key, ''),
                    'platforms': cleaned_data.get(f'{key}_platforms', []),
                }
            elif field['type'] == 'choice_or_upload':
                values[key] = {'choices': cleaned_data.get(key, [])}
            else:
                values[key] = cleaned_data.get(key, '')
        values['font_choice'] = cleaned_data.get('font_choice', '')
        values['font_custom_text'] = cleaned_data.get('font_custom_text', '')
        return values


class LogoDecisionForm(forms.Form):
    NOW = 'now'
    LATER = 'later'
    CHOICES = [(NOW, 'Upload logo now'), (LATER, "I'll upload it later")]

    decision = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    logo_file = forms.FileField(required=False)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('decision') == self.NOW and not cleaned.get('logo_file'):
            self.add_error('logo_file', 'Please choose a logo file, or select "upload it later".')
        return cleaned
