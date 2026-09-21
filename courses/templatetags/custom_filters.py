from django import template

register = template.Library()


@register.filter
def add(value, arg):
    """Concatenate two strings. Usage: "topic_"|add:idx|add:"_code" """
    return f'{value}{arg}'


@register.filter
def get_field(form, name):
    """Look up a bound field on a form by its constructed name"""
    try:
        return form[name]
    except KeyError:
        return ''


@register.filter
def endswith(value, arg):
    """Check if value ends with the given suffix"""
    return str(value).endswith(str(arg))


@register.filter
def is_code_field(value):
    """Check if this is a code field (ends with _code)"""
    return str(value).endswith('_code')
