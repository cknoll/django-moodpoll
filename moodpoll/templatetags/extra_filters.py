from django import template
import markdown
import bleach
from .. import utils
from django.utils import timezone
# from moodpoll.release import __version__

register = template.Library()
bleach.sanitizer.ALLOWED_TAGS += ["p", "br", "h1", "h2", "h3", "h4"]


@register.filter
def render_markdown_bleach(txt):
    # !!! here we should check if there is no harmfull code in txt
    # because we will pass it through `safe` later
    # however it should be possible to discuss about code (even javascript)

    if txt is None:
        txt = ""
    return bleach.clean(markdown.markdown(txt))


@register.filter
def add_num_prefix(num):
    if 0 < num:
        return '+{}'.format(num)
    if 0 == num:
        return '±{}'.format(num)
    return '{}'.format(num)


@register.filter
def time_until(time):
    if time < timezone.now():
        return 'passed'
    else:
        return '{} left'.format(utils.get_time_until(time))
