from django import template

register = template.Library()


@register.filter
def get_item(form, key):
    """Look up a BoundField on a form by a dynamic key, e.g. {{ form|get_item:key }}."""
    return form[key]
