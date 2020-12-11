from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .. import models
from ..helpers import toasts as t

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

    from ipydex import IPS
    if option_list[0].startswith("#") and \
       len(option_list) > 1 and not poll.title:

        title_candidate = option_list[0][1:].strip()
        if len(title_candidate) > 0:
            poll.title = title_candidate
            option_list.pop(0)


class NewPollView(View):
    def get(self, request):
        context = {
            'settings_mood_value_min': settings.MOOD_VALUE_MIN,
            'settings_mood_value_max': settings.MOOD_VALUE_MAX,
        }

        return render(request, "moodpoll/poll/new_poll.html", context)

    def post(self, request):
        new_poll = fill_poll_from_post(request.POST)

        options_tidy = []
        if 'options' in request.POST:
            options_tidy = tidy_options(request.POST['options'])
        if 0 == len(options_tidy):
            raise NotImplementedError

        process_special_options(new_poll, options_tidy)

        if 0 == len(options_tidy):
            raise NotImplementedError

        # all params checked, create
        with transaction.atomic():
            save_poll_and_create_options(new_poll, options_tidy)

        t.success(request, 'poll has been created')

        return redirect(reverse("show_poll", kwargs={"pk": new_poll.pk, "key": new_poll.key}))

