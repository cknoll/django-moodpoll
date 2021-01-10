from django.shortcuts import get_object_or_404, redirect, reverse
from django.views import View
from django.core.exceptions import PermissionDenied
from .. import models
from ..helpers import toasts as t


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
        t.info(request, 'vote has been cancelled')

        return redirect(reverse("show_poll", kwargs={"pk": poll.pk, "key": poll.key}))
