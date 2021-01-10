from django.shortcuts import render
from .simple_pages_interface import get_sp
from .release import __version__


# empty object to store some attributes at runtime
class Container(object):
    pass


def view_simple_page(request, pagetype=None, base_container=None):
    """
    Render (almost) static page
    :param request:
    :param pagetype:
    :param base_container:
    :return:
    """

    # TODO: merge the base-object and the sp-object
    if base_container is None:
        base_container = Container()
    lang = None

    sp = get_sp(pagetype=pagetype, lang=lang)

    format_dict = getattr(base_container, "format_dict", None)
    if format_dict:
        sp.content = sp.content.format(**format_dict)

    context = {"pagetype": pagetype, "sp": sp, "base": base_container, "app_version": __version__}
    return render(request, 'moodpoll/main_simple_page.html', context)
