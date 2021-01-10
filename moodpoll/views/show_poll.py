from django.shortcuts import render, redirect, reverse
from django.views import View
from django.db import transaction
from .. import models
from ..utils import get_poll_or_4xx, init_session_reply_list
from ..helpers import toasts as t
from ..release import __version__


class ShowPollView(View):
    def get(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)
        poll_options = models.PollOption.objects.filter(poll=poll)

        if not poll.is_vote_possible():
            return redirect(reverse("poll_result", kwargs={"pk": poll.pk, "key": poll.key}))

        context = {
            'poll': poll,
            'options': poll_options,
            'app_version': __version__,
        }

        if poll.expose_veto_names:
            # show a note to the user that result anonymity will be partially broken
            utc = "<!--utc_toast_info:anonymous_vetos_disabled-->"
            t.info(request, f"<b>Note</b>: Anonymous vetos are disabled for this poll. {utc}")

        return render(request, "moodpoll/poll/show_poll.html", context)

    def post(self, request, pk, key):
        poll = get_poll_or_4xx(pk, key)
        poll_options = models.PollOption.objects.filter(poll=poll)

        if not poll.is_vote_possible():
            return redirect(reverse("poll_result", kwargs={"pk": poll.pk, "key": poll.key}))

        # TODO randomize key
        poll_reply = models.PollReply(
            user_name='Anonymous',
            poll=poll,
        )

        if 'user_name' in request.POST and request.POST['user_name'] != '':
            poll_reply.user_name = request.POST['user_name']
        else:

            if poll.require_name:
                # in this case empty name should have been prevented by the require attribute of the input field
                # nevertheless it does not harm
                utc = "<!--utc_toast_error:empty_user_name-->"
                msg = f'Empty name not allowed for this poll! {utc}'
                t.error(request, msg)
                return redirect(reverse("show_poll", kwargs={"pk": poll.pk, "key": poll.key}))

            # if not poll.require_name: add counter behind name for non-user-entered names
            old_name = poll_reply.user_name
            counter = 1
            while models.PollReply.objects.filter(poll=poll, user_name='{} #{}'.format(old_name, counter)).count() > 0:
                counter += 1

            poll_reply.user_name = '{} #{}'.format(old_name, counter)

        with transaction.atomic():
            poll_reply.save()

            # note: iterate over poll options, as only submission for these options have been authenticated
            for option in poll_options:
                htmlname = 'option_{}'.format(option.pk)
                if htmlname not in request.POST:
                    continue

                mood_value = int(request.POST[htmlname])
                # invalid mood values are not counted at all
                if mood_value < option.poll.mood_value_min or mood_value > option.poll.mood_value_max:
                    continue

                option_reply = models.PollOptionReply(
                    poll_option=option,
                    poll_reply=poll_reply,
                    mood_value=mood_value,
                )
                option_reply.save()

            init_session_reply_list(request)
            request.session['poll_replies'].append(poll_reply.pk)

        t.success(request, 'vote submitted')

        return redirect(reverse("poll_result", kwargs={"pk": poll.pk, "key": poll.key}))
