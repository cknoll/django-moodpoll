from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Q, F, Count
from django.db.models.functions import Coalesce
from django.conf import settings
from .. import models
from ..utils import get_poll_or_4xx


class PollResultView(View):
    def get(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)
        poll_options = models.PollOption.objects.filter(poll=poll)
        poll_replies = models.PollReply.objects.filter(poll=poll)

        context = {
            'poll': poll,
            'poll_options': poll_options,
            'poll_replies': poll_replies,
            'mood_bar_min': -10 * len(poll_replies),
            'mood_bar_max': +10 * len(poll_replies),
        }

        return render(request, "moodpoll/poll/poll_result.html", context)


def get_mood_sums(poll):
    # todo: this seems to be obsolete?
    # noinspection PyUnresolvedReferences
    mood_sums = models.PollOptionReply.objects. \
        filter(poll_option__poll=poll). \
        values('poll_option', 'poll_option__text'). \
        annotate(
            mood_sum=Coalesce(Sum('mood_value'), 0),
            mood_praise=Coalesce(Sum('mood_value', filter=Q(mood_value__gt=0)), 0),
            mood_blame=Coalesce(Sum('mood_value', filter=Q(mood_value__lt=0)), 0),
            mood_neutrals=Coalesce(Count('mood_value', filter=Q(mood_value=0)), 0),
            mood_vetos=Coalesce(Count('mood_value', filter=Q(mood_value=settings.MIN_MOOD_VALUE)), 0),
            mood_votes=Coalesce(Count('mood_value'), 0)
            )

    return mood_sums


def get_voters(poll):
    # noinspection PyUnresolvedReferences
    voters = models.PollReply.objects. \
        filter(poll=poll). \
        values('user_name', 'update_datetime')

    return voters


