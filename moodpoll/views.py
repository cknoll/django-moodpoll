# from django.http import HttpResponse
import re
import json
import math

from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from . import models
from . import utils
from . import forms
from .simple_pages_interface import get_sp

# debugging helper
from ipydex import IPS, activate_ips_on_exception


class DataIntegrityError(ValueError):
    pass


def index(request):
    # return HttpResponse("Hello world!")

    return view_test(request)


# empty object to store some attributes at runtime
class Container(object):
    pass


option_list = ["Option 1",
               "Option 2",
               "Option 3",
               "Option 4",
               "Option 'A'",
               'Option "B"',
               "Option Ä",
               ]

option_list_str = "\n".join(option_list)

appname = "moodpoll"


def populate_db():
    u = models.User(name="u1")
    u.save()

    p = models.Poll(optionlist=repr(option_list))
    p.save()

    values = [0]*len(option_list)

    me = models.MoodExpression(user=u, poll=p, mood_values=repr(values))
    me.save()


def parse_option_list(ol_str):

    ol = ol_str.strip().split("\n")
    res = []
    for idx, option_str in enumerate(ol):
        C = Container()
        C.content = option_str
        C.id = f"option_{idx}"

        res.append(C)

    return res


def view_test(request):

    pol = parse_option_list(option_list_str)

    context = {"option_list": pol}

    return render(request, "{}/main_form.html".format(appname), context)


# noinspection PyMethodMayBeStatic
class ViewCreatePoll(View):

    def get(self, request):
        form = forms.PollForm()

        context = dict(form=form)
        form.action_url_name = "new_poll"
        return render(request, "{}/main_new_poll.html".format(appname), context)

    def post(self, request):

        form = forms.PollForm(request.POST)
        if not form.is_valid():
            # !! error handling
            1/0
            return None
        else:
            new_poll = form.save()

        request.session["poll_created"] = new_poll.pk
        return redirect(reverse("show_poll", kwargs={"pk": new_poll.pk}))


class ViewPoll(View):

    @staticmethod
    def get(request, pk, key=None, c=None):
        """
        :param request:
        :param pk:
        :param key:     if provided, the (current) result is shown (not yet implemented)
        :param c:       container (recieve data from elsewhere)
        :return:
        """

        c = Container()

        if request.session.pop("poll_created", None) == pk:
            c.msg = "Successfully created new poll:"

            # add unit test comment
            c.utc_new_poll = "new_poll_{}".format(pk)

        c.action_url_name = "poll_eval"
        c.pk = pk
        c.min = -3
        c.max = 2

        # !! read the current user from session data and look if they already voted
        c.startval = 0

        c.poll = get_object_or_404(models.Poll, pk=pk)
        c.option_list = parse_option_list(c.poll.optionlist)
        context = dict(c=c, )

        return render(request, "{}/main_show_poll.html".format(appname), context)

    @staticmethod
    def post(request, pk):
        pass


class ViewPollResult(View):

    @staticmethod
    def get(request, pk, c=None):
        c = evaluate_poll_results(pk, c)
        context = dict(c=c, )

        return render(request, "{}/main_poll_result.html".format(appname), context)

    @staticmethod
    def post(request):
        pass


class ViewPollEvaluation(View):

    @staticmethod
    def get(request, pk):
        return view_simple_page(request, pagetype="general_error")

    def post(self, request, pk):
        """
        Process data from a voting act and show the results until now

        :param request:
        :param pk:
        :return:
        """

        data = request.POST.copy()
        # process numeric form data:

        cregex = re.compile(r"option_\d+_input")

        option_pairs = [(k, int(v)) for k, v in data.items() if cregex.match(k)]
        option_pairs.sort()

        # after ensuring correct order we can drop the keys and represent the list a one string
        mood_values = repr([v for k, v in option_pairs])

        c = Container()
        c.username = data.get("username")
        c.post_data = data

        the_poll = get_object_or_404(models.Poll, pk=pk)

        # try to find a MoodExpression with the same combination of poll and username

        # noinspection PyUnresolvedReferences
        old_me_list = models.MoodExpression.objects.filter(poll=1, username=c.username)
        if len(old_me_list) == 0:
            me = models.MoodExpression(username=c.username, poll=the_poll, mood_values=mood_values)
        elif len(old_me_list) == 1:
            # overwrite the old db-entry
            me = old_me_list[0]
            if data.get("__overwrite_flag") == "True":
                # update the values and the time
                me.mood_values = mood_values
                me.datetime = timezone.now()
            else:
                return self.handle_conflict(request, pk, me, c)
        else:
            msg = "Unexpected: multiple votes for username {} and poll {}".format(c.username, the_poll)
            raise DataIntegrityError(msg)
        me.save()


        return redirect(reverse("poll_result", kwargs={"pk": pk}))

    @staticmethod
    def handle_conflict(request, pk, old_me, c):
        """
        Called if a username is used the second time for one poll.

        -> Display a page where the user can decide whether to overwrite existing mood_values
        or to give a new name.

        :param request:
        :param pk:          pk of the poll
        :param old_me:      old mood_expression
        :param c:           container with preprocessed data from the caller
        :return:
        """

        dt_string = datetime_string_from_dt_object(old_me.datetime)

        action_url = reverse("poll_eval", kwargs={"pk": pk})

        # generate some hidden values including "overwrite_flag"

        hidden_fields = ['<input type="hidden" name="__overwrite_flag" value="True">']
        for key, value in c.post_data.items():
            if key == "csrfmiddlewaretoken":
                # maybe omit that entry or generate a new one?
                # continue
                pass
            hidden_fields.append('<input type="hidden" name="{}" value="{}">'.format(key, value))
        form_data = "\n".join(hidden_fields)

        c.format_dict = {"username": old_me.username, "action_url": action_url,
                         "dt_string": dt_string, "form_data": form_data}

        return view_simple_page(request, pagetype="overwrite_warning", base_container=c)


def view_simple_page(request, pagetype=None, base_container=None):
    """
    Render (almost) static page
    :param request:
    :param pagetype:
    :param base_container:
    :return:
    """

    # TODO: merge the base-object and the sp-object
    if base_container is None:
        base_container = Container()
    lang = None

    sp = get_sp(pagetype=pagetype, lang=lang)

    format_dict = getattr(base_container, "format_dict", None)
    if format_dict:
        sp.content = sp.content.format(**format_dict)

    context = {"pagetype": pagetype, "sp": sp, "base": base_container}
    return render(request, 'moodpoll/main_simple_page.html', context)


@login_required
def view_do_backup(request):
    """
    Write a json backup of the database to disk. Useful for development.
    :param request:
    :return:
    """
    c = Container()
    if request.user.is_superuser:
        fname = utils.save_stripped_fixtures(backup=True)
        c.format_dict = {"backup_path": fname}

        return view_simple_page(request, "backup", base_container=c)
    else:

        return view_simple_page(request, "backup_no_login", base_container=c)


# ### Helper functions ####


def datetime_string_from_dt_object(dt_object):
    return dt_object.strftime(r"%Y-%m-%d %H:%M:%S")


# this functionality is outsourced for better testability
def evaluate_poll_results(pk, c=None):
    """
    Return a Container-object which contains information about the results (positive, negative, neutral)
    for all options.

    :param pk:
    :param c:
    :return:
    """
    if c is None:
        c = Container()

    c.poll = get_object_or_404(models.Poll, pk=pk)

    # list of Container-objects
    c.option_list = parse_option_list(c.poll.optionlist)

    # !! introduce and use nbr_of_opts of model ??
    n_opts = len(c.option_list)

    me_list = models.MoodExpression.objects.filter(poll=pk)

    c.user_voting_acts = []
    mood_values = []
    # produce a list of lists of ints

    for me in me_list:
        mood_values.append(json.loads(me.mood_values))

        dt = datetime_string_from_dt_object(me.datetime)
        c.user_voting_acts.append((me.username, dt, me.datetime.timestamp()))

    # count positive, negative and neutral votes separately
    pos = list_of_empty_lists(n_opts)
    neg = list_of_empty_lists(n_opts)
    neu = list_of_empty_lists(n_opts)

    # iterate over all
    for mv_list in mood_values:
        assert len(mv_list) == n_opts
        for idx, mood_value in enumerate(mv_list):
            if mood_value < 0:
                neg[idx].append(mood_value)
            elif mood_value > 0:
                pos[idx].append(mood_value)
            else:
                neu[idx].append(mood_value)

    # Evaluation:
    # for negative and positive votes there are three important numbers:
    # a) how many people voted for that option
    # b) how strong is there opinion in average
    # c) how strong is there opinion in total score (sum)
    # -> for every option of the option_list, we store three triples (one for negative, neutral, positive)

    c.pos_res, c.neg_res, c.neu_res = [], [], []

    for p, n, nt, opt_cont in zip(pos, neg, neu, c.option_list):
        mean_p = map_normed_mean_to_09(p, 2)
        triple = (len(p), str(mean_p)[2:], sum(p))
        c.pos_res.append(triple)
        opt_cont.approvals = triple

        # we neglegt the sign for the mean (we already now that this value is counts negative)
        mean_n = abs(map_normed_mean_to_09(n, -3))
        # omit the "0." part of the str
        triple = (len(n), str(mean_n)[2:], sum(n))
        c.neg_res.append(triple)
        opt_cont.resistances = triple

        # for neutral votes no mean has to be calculated, because every value is 0
        triple = (len(nt), "0", len(nt))
        c.neu_res.append(triple)
        opt_cont.neutrals = triple

    # sort by timestamp (3rd argument) (descending)
    c.user_voting_acts.sort(key=lambda arg: arg[2], reverse=True)

    return c


def list_of_empty_lists(n):
    return [list() for i in range(n)]


def mean(seq):
    if len(seq) == 0:
        return 0.0
    return sum(seq, 0.0) / len(seq)


def map_normed_mean_to_09(seq, end_of_scale, round_result=1):
    """
    - calculate the mean of seq,
    - subtract the minimum possible value (assumed to be 1)
    - normalize it with the "maximum" possible value (w.r.t. abs), -> somthing in [0, 1]
    - map this interval to [0.1, 0.9]

    Rationale: we want to compactly express how strong is approval and rejection - one number is needed.
    Highest or lowest number == 0 would be confusing.

    :param seq:             sequence of numbers (assume all have the same sign)
    :param end_of_scale:    max possible value (min possible for negeative)
    :param round_result:    False or int (digits)
    :return:
    """
    m = mean(seq)

    if m == 0:
        return 0.0

    diff = math.copysign(1, m)
    assert abs(end_of_scale) > 1
    assert abs(m) >= 1

    # map the result to [0.1, 0.9]
    res = (m - diff) / (end_of_scale - diff) * 0.8 + .1
    if round_result is not False:
        return round(res, round_result)
    else:
        return res
