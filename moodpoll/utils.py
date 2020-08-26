
"""
crearted: 2019-12-04 00:29:45 (copied from sober)
author: ck
"""

import os
from collections import defaultdict

from django.shortcuts import get_object_or_404
from . import models
from django.core.exceptions import PermissionDenied

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
