from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Q
from .. import models

class PollResultView(View):
    def get(self, request, pk, key):
        poll = get_object_or_404(models.Poll, pk=pk)

        #check auth
        if key != poll.key:
            raise PermissionDenied()

        mood_sums = models.PollOptionReply.objects.filter(poll_option__poll=poll).values('poll_option', 'poll_option__text').annotate(mood_sum=Sum('mood_value'))

        poll_options = models.PollOption.objects.filter(poll=poll)
            
        context = {
            'poll': poll,
            'mood_sums': mood_sums,
        }

        return render(request, "moodpoll/poll/poll_result.html", context)
