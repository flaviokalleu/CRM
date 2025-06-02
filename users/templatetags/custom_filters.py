# users/templatetags/custom_filters.py
from django import template
from django.utils.safestring import SafeString

register = template.Library()


@register.filter(name='get_key')
def get_key(value, arg):
    return value.get(arg, '')

@register.filter
def get_color(value):
    if isinstance(value, SafeString):
        try:
            value = float(value)
        except ValueError:
            return 'unknown'
        
    return 'green' if value > 0 else 'red'

@register.filter
def access(value, arg):
    if isinstance(value, dict):
        return value.get(arg)
    return None 



register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)