from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.exceptions import PermissionDenied
from .. import models

class PollReplyCancelView(View):
    def post(self, request, pk, key):
        poll_reply = get_object_or_404(models.PollReply, pk=pk)
        poll = poll_reply.poll

        # check key
        if key != poll_reply.key:
            raise PermissionDenied()

        # check if can be cancelled
        if not poll_reply.is_cancelable():
            raise PermissionDenied()

        # cancel
        poll_reply.cancel()

        return redirect(reverse("show_poll", kwargs={"pk": poll.pk, "key": poll.key}))

