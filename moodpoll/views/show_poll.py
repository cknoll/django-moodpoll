from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest
from .. import models
from ..utils import get_poll_or_4xx


class ShowPollView(View):
    def get(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)
        poll_options = models.PollOption.objects.filter(poll=poll)

        context = {
            'poll': poll,
            'options': poll_options,
            'request': request,
        }

        return render(request, "moodpoll/poll/show_poll.html", context)

    def post(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)
        poll_options = models.PollOption.objects.filter(poll=poll)

        # TODO randomize key
        poll_reply = models.PollReply(
            user_name='Anonymous',
            poll=poll,
        )

        if 'user_name' in request.POST and request.POST['user_name'] != '':
            poll_reply.user_name = request.POST['user_name']

        with transaction.atomic():
            poll_reply.save()
            
            # note: iterate over poll options, as only submission for these options have been authenticated
            for option in poll_options:
                htmlname = 'option_{}'.format(option.pk)
                if htmlname not in request.POST:
                    break
                
                mood_value = int(request.POST[htmlname])
                # invalid mood values are not counted at all
                if mood_value < option.poll.mood_value_min or mood_value > option.poll.mood_value_max:
                    break
                
                option_reply = models.PollOptionReply(
                    poll_option=option,
                    poll_reply=poll_reply,
                    mood_value=mood_value,
                )
                option_reply.save()

        return redirect(reverse("poll_result", kwargs={"pk": poll.pk, "key": poll.key}))

