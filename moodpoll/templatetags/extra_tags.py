from django import template

register = template.Library()

@register.simple_tag
def make_html_width(min, max, current):
    if min == max:
        return '100%'
    return str(100.0 * (float(current) - float(min))/(float(max) - float(min))) + '%'
