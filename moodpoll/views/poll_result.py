from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Min, Max, Q, F
from django.db.models.functions import Coalesce
from .. import models
from ..utils import get_poll_or_4xx

class PollResultView(View):
    def get(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)

        # note that this will return an empty set if no one has responded yet
        mood_sums = models.PollOptionReply.objects. \
            filter(poll_option__poll=poll). \
            values('poll_option', 'poll_option__text'). \
            annotate(
                mood_sum=Coalesce(Sum('mood_value'), 0),
                mood_praise=Coalesce(Sum('mood_value', filter=Q(mood_value__gt=0)), 0),
                mood_blame=Coalesce(Sum('mood_value', filter=Q(mood_value__lt=0)), 0)
                )

        mood_sums_meta = mood_sums.aggregate(Min('mood_sum'), Max('mood_sum'))

        poll_options = models.PollOption.objects.filter(poll=poll)

        poll_replies = models.PollReply.objects.filter(poll=poll)
            
        context = {
            'poll': poll,
            'poll_replies': poll_replies,
            'mood_sums': mood_sums,
            'mood_sums_meta': mood_sums_meta,
        }

        return render(request, "moodpoll/poll/poll_result.html", context)
