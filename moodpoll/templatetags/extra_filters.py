from django import template
import markdown
import bleach
# from moodpoll.release import __version__

register = template.Library()
bleach.sanitizer.ALLOWED_TAGS += ["p", "br"]


@register.filter
def render_markdown_bleach(txt):
    # !!! here we should check if there is no harmfull code in txt
    # because we will pass it through `safe` later
    # however it should be possible to discuss about code (even javascript)

    if txt is None:
        txt = ""
    return bleach.clean(markdown.markdown(txt))


