
"""
crearted: 2019-12-04 00:29:45 (copied from sober)
author: ck
"""

import os
from collections import defaultdict

from django.shortcuts import get_object_or_404
from . import models
from django.core.exceptions import PermissionDenied
from django.utils import timezone

# noinspection PyUnresolvedReferences
from ipydex import IPS, ST, ip_syshook, dirsearch, sys, activate_ips_on_exception

# activate_ips_on_exception()


class DatabaseEmptyError(ValueError):
    pass


# This dict must contain only data which is consitent with urlpatterns from `urls.py`
# To prevent a circular import we cannot use `from django.urls import reverse`.
# Therefore we have to use duplicated data.
# There is a unit tests which ensures integrity.
duplicated_urls_data = {"contact-page": "/contact",
                        "about-page": "/about",
                        "new_poll": "/new",
                        }
duplicated_urls = defaultdict(lambda: "__invalid_url__", duplicated_urls_data)


appname = "moodpoll"


# noinspection PyPep8Naming
def get_project_READMEmd(marker_a=None, marker_b=None):
    """
    Return the content of README.md from the root directory of this project

    (optionally return only the text between the two marker-strings)
    :return:
    """

    basepath = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(basepath)
    fpath = os.path.join(project_root, "README.md")
    with open(fpath, "r") as txt_file:
        txt = txt_file.read()

    if marker_a is None:
        assert marker_b is None
        return txt
    else:
        assert marker_b is not None

    try:
        idx1 = txt.index(marker_a) + len(marker_a)
        idx2 = txt.index(marker_b)
    except ValueError:
        IPS()
        return txt

    return txt[idx1:idx2]


def get_poll_or_4xx(pk, key):
    """retrieve a poll from db iff correct params have been given; else: throw HTTP 404/403"""
    poll = get_object_or_404(models.Poll, pk=pk)

    #check auth
    if key != poll.key:
        raise PermissionDenied()

    return poll


def init_session_toasts(request):
    """init structure of session to hold toasts"""
    if not 'toasts' in request.session:
        request.session['toasts'] = {}

    if not 'error' in request.session['toasts']:
        request.session['toasts']['error'] = []
    if not 'warning' in request.session['toasts']:
        request.session['toasts']['warning'] = []
    if not 'info' in request.session['toasts']:
        request.session['toasts']['info'] = []
    if not 'success' in request.session['toasts']:
        request.session['toasts']['success'] = []

def init_session_reply_list(request):
    """init structure of session to hold replies"""
    if 'poll_replies' not in request.session:
        request.session['poll_replies'] = []

    cancelable = []

    for pk in request.session['poll_replies']:
        reply_list = models.PollReply.objects.filter(pk=pk)
        if len(reply_list) == 1 and reply_list[0].is_cancelable():
            cancelable.append(pk)

    request.session['poll_replies'] = cancelable

def get_number_and_unit(x, unit):
    final_s = 's'
    if 1 == x:
        final_s = ''
    return '{}  {}{}'.format(x, unit, final_s)

def get_time_until(future, now=timezone.now()):
    """return string describing how much time is left to the given time point"""
    if future < now:
        return 'passed'

    delta = future - now

    if delta.days > 7:
        return get_number_and_unit(int(delta.days / 7), 'week')
    if delta.days > 1:
        return get_number_and_unit(delta.days, 'day')
    if delta.seconds > 3600:
        return get_number_and_unit(int(delta.seconds / 3600), 'hour')
    if delta.seconds > 60:
        return '{} min'.format(int(delta.seconds / 60))

    return get_number_and_unit(delta.seconds, 'second')
