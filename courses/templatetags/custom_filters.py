from django import template

register = template.Library()


@register.filter
def add(value, arg):
    """
    Allows adding a value to another value.
    Used for dictionary-like access in templates.

    Usage: form|add:"field_name"
    """
    try:
        return value[str(arg)]
    except (KeyError, TypeError, AttributeError):
        return ''


@register.filter
def field_errors(field):
    """Get errors from a form field"""
    try:
        return field.errors
    except:
        return []


@register.filter
def endswith(value, arg):
    """Check if value ends with the given suffix"""
    return str(value).endswith(str(arg))


@register.filter
def is_code_field(value):
    """Check if this is a code field (ends with _code)"""
    return str(value).endswith('_code')
