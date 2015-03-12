from django import template

register = template.Library()

@register.filter(name='get_type')
def get_type(value):
    return type(value).__name__