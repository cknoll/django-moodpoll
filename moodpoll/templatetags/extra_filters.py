from django import template
import markdown
# from moodpoll.release import __version__

register = template.Library()


@register.filter
def render_markdown(txt):
    # !!! here we shoud check if there is no harmfull code in txt
    # because we will pass it through `safe` later
    # however it should be possible to discuss about code (even javascript)
    return markdown.markdown(txt)
