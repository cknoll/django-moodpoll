from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Min, Max, Count, Q, F
from django.db.models.functions import Coalesce
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
