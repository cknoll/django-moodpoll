from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .. import models
from ..helpers import toasts as t
from datetime import datetime as dt


def tidy_options(text):
    '''split given multiline string on newline, remove leading/trailing spaces, remove empty lines'''
    options_tidied = []
    for line in text.splitlines():
        stripped = line.strip()
        if '' != stripped:
            options_tidied.append(stripped)

    return options_tidied


def fill_poll_from_post(post):
    '''fill a new poll object from post data'''
    new_poll = models.Poll()

    if 'title' in post and post['title'] != '':
        new_poll.title = post['title']
    if 'description' in post and post['description'] != '':
        new_poll.description = post['description']
    # http will transmit a field only if the checkbox is checked
    new_poll.replies_hidden = 'replies_hidden' in post

    if 'deadline_time' in post and post['deadline_time'] != '' and 'deadline_date' in post and post['deadline_date'] != '':
        full_date_str = '{} {}'.format(post['deadline_date'], post['deadline_time'])
        try:
            print('parsing date: {}'.format(full_date_str))
            parsed_deadline = timezone.make_aware(dt.strptime(full_date_str, "%Y-%m-%d %H:%M"))

            # only allow deadline if in future
            if parsed_deadline > timezone.now():
                new_poll.deadline = parsed_deadline

        except ValueError:
            pass

    try:
        if 'mood_value_min' in post and int(post['mood_value_min']) <= 0:
            new_poll.mood_value_min = int(post['mood_value_min'])
    except ValueError:
        pass

    try:
        if 'mood_value_max' in post and int(post['mood_value_max']) >= 0:
            new_poll.mood_value_max = int(post['mood_value_max'])
    except ValueError:
        pass

    return new_poll


def save_poll_and_create_options(poll, options_array):
    '''save poll object and create options from given array'''
    poll.save()

    for option_text in options_array:
        poll_option = models.PollOption(
            text=option_text,
            poll=poll,
            )
        poll_option.save()


def process_special_options(poll, option_list):
    """
    Some options might not be poll options, but contain other information (such as the title).
    They are handled here.

    :param poll:
    :param option_list:
    :return: None (Note: the option list might be altered (special options are removed))
    """

    # if the first option starts with `#` and poll has no title yet, then the first option
    # is interpreted as the title

    if option_list[0].startswith("#") and not poll.title:

        title_candidate = option_list[0][1:].strip()
        if len(title_candidate) > 0:
            poll.title = title_candidate
            option_list.pop(0)


class NewPollView(View):
    def get(self, request):
        context = {
            'settings_mood_value_min': settings.MOOD_VALUE_MIN,
            'settings_mood_value_max': settings.MOOD_VALUE_MAX,
            'now': timezone.now(),
        }

        return render(request, "moodpoll/poll/new_poll.html", context)

    def post(self, request):
        new_poll = fill_poll_from_post(request.POST)

        options_tidy = []
        if 'options' in request.POST:
            options_tidy = tidy_options(request.POST['options'])
        if 0 == len(options_tidy):
            msg = "Empty option list received. This is unexpected due to `required` attribute of respective form field"
            raise ValueError(msg)

        process_special_options(new_poll, options_tidy)

        if 0 == len(options_tidy):
            # this might be the case if the first line started with # (interpreted as title)
            t.error(request, 'no valid poll option found <!--utc_toast_error: empty_poll_option_list-->')
            return redirect(reverse("new_poll"))

        # all params checked, create
        with transaction.atomic():
            save_poll_and_create_options(new_poll, options_tidy)

        t.success(request, 'poll has been created <!--utc_toast_success-->')

        return redirect(reverse("show_poll", kwargs={"pk": new_poll.pk, "key": new_poll.key}))

