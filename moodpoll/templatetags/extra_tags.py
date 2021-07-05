from django import template
from django.urls import reverse
from django.conf import settings
from ..import utils

register = template.Library()
from django.utils import timezone


@register.simple_tag
def make_html_width(min, max, current):
    if min == max:
        return '100%'
    return str(100.0 * (float(current) - float(min))/(float(max) - float(min))) + '%'


@register.simple_tag
def make_redgreen_css_gradient(min, max, current):
    frac = (float(current) - float(min))/(float(max) - float(min))
    color_frac_r = int(216.0 * (1 - frac))
    color_frac_g = int(216.0 * frac)

    return '#{:02x}{:02x}00'.format(color_frac_r, color_frac_g)


@register.simple_tag
def get_poll_link(poll, request):
    urlargs = {
        'pk': poll.pk,
        'key': poll.key,
    }
    path = reverse('show_poll', kwargs=urlargs)

    return request.build_absolute_uri(path)


@register.simple_tag
def pop_toasts(request):
    utils.init_session_toasts(request)
    request.session.pop('toasts')

    return ""


@register.simple_tag
def server_time():
    return timezone.now().strftime('%Y-%m-%d %H:%M:%S')


@register.simple_tag
def server_timezone():
    return settings.TIME_ZONE
