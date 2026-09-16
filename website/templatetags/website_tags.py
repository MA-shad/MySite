from django import template

register = template.Library()

@register.filter
def short_description(value, length=120):
    return value[:length] + "..." if len(value) > length else value