"""
Custom template filters for lead management.
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)


@register.filter
def get_item_count(dictionary, key):
    """
    Get the count of items in a dictionary value.
    Usage: {{ dictionary|get_item_count:key }}
    """
    value = dictionary.get(key)
    if hasattr(value, 'count'):
        return value.count()
    elif hasattr(value, '__len__'):
        return len(value)
    return 0 