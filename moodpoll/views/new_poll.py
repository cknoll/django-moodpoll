from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.db import transaction
from .. import models

class NewPollView(View):
    def get(self, request):
        context = {}
        return render(request, "moodpoll/poll/new_poll.html", context)

    def post(self, request):
        new_poll = models.Poll()

        if 'title' in request.POST and request.POST['title'] != '':
            new_poll.title = request.POST['title']
        if 'description' in request.POST and request.POST['description'] != '':
            new_poll.description = request.POST['description']
        # http will transmit a field only if the checkbox is checked
        new_poll.replies_hidden = 'replies_hidden' in request.POST

        options_tidy = []

        if 'options' in request.POST:
            for line in request.POST['options'].splitlines():
                stripped = line.strip()
                if '' != stripped:
                    options_tidy.append(stripped)

        if 0 == len(options_tidy):
            raise NotImplementedError

        new_poll.key = 17

        # all params checked, create
        with transaction.atomic():
            new_poll.save()

            for option_text in options_tidy:
                poll_option = models.PollOption(
                    text=option_text,
                    poll=new_poll,
                    )
                poll_option.save()

        return redirect(reverse("show_poll", kwargs={"pk": new_poll.pk}))

