from collections import Counter
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Q, F, Count
from django.db.models.functions import Coalesce
from django.conf import settings
from .. import models
from ..utils import get_poll_or_4xx, init_session_reply_list
from ..helpers import toasts as t


class PollResultView(View):
    def get(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)
        poll_options = models.PollOption.objects.filter(poll=poll)
        poll_replies = models.PollReply.objects.filter(poll=poll)

        init_session_reply_list(request)

        if poll.expose_veto_names:
            poll_veto_users = get_veto_users(poll)
        else:
            poll_veto_users = None

        context = {
            'poll': poll,
            'poll_options': poll_options,
            'poll_replies': poll_replies,
            'poll_veto_users': poll_veto_users,
            'mood_bar_min': poll.mood_value_min * len(poll_replies),
            'mood_bar_max': poll.mood_value_max * len(poll_replies),
        }

        # note: result will be hidden by view if not yet visible
        return render(request, "moodpoll/poll/poll_result.html", context)


def get_mood_sums(poll):
    # todo: this seems to be obsolete?
    mood_sums = models.PollOptionReply.objects. \
        filter(poll_option__poll=poll). \
        values('poll_option', 'poll_option__text'). \
        annotate(
            mood_sum=Coalesce(Sum('mood_value'), 0),
            mood_praise=Coalesce(Sum('mood_value', filter=Q(mood_value__gt=0)), 0),
            mood_blame=Coalesce(Sum('mood_value', filter=Q(mood_value__lt=0)), 0),
            mood_neutrals=Coalesce(Count('mood_value', filter=Q(mood_value=0)), 0),
            mood_vetos=Coalesce(Count('mood_value', filter=Q(mood_value=settings.MOOD_VALUE_MIN)), 0),
            mood_votes=Coalesce(Count('mood_value'), 0)
            )

    return mood_sums


def get_voters(poll):
    voters = models.PollReply.objects. \
        filter(poll=poll). \
        values('user_name', 'update_datetime')

    return voters


def get_veto_users(poll):
    qs = models.PollOptionReply.objects. \
        filter(poll_reply__poll=poll, mood_value=poll.mood_value_min). \
        values("poll_reply__user_name")

    # in general contains every user_name multiple times:
    veto_user_list = [elt["poll_reply__user_name"] for elt in qs]
    poll_veto_users = [f"{item[0]} ({item[1]})" for item in Counter(veto_user_list).items()]

    return poll_veto_users

