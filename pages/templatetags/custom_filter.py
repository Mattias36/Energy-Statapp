from django import template
import re
from django.utils.text import slugify

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def remove_units(value):
    """Usuwa jednostki w nawiasach kwadratowych, np. [GWh]"""
    return re.sub(r'\s*\[.*?\]', '', value)

@register.filter
def to_slug(value):
    clean = re.sub(r'\s*\[.*?\]', '', value)  # usuń jednostki
    return slugify(clean)