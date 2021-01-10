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
    # Todo: should become obsolete. use |bleach in template

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
