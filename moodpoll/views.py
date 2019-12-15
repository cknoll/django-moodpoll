# from django.http import HttpResponse
import re
import json

from django.shortcuts import render, get_object_or_404
from django.views import View

from . import models
from . import forms

# debugging helper
from ipydex import IPS, activate_ips_on_exception


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
            # error handling
            1/0
            return None
        else:
            new_poll = form.save()

        c = Container()
        c.msg = "Successfully created new poll:"

        return ViewPoll().get(request, new_poll.pk, c=c)


class ViewPoll(View):

    @staticmethod
    def get(request, pk, key=None, c=None):
        """
        :param request:
        :param pk:
        :param key:     if provided, the (current) result is shown
        :param c:       container (recieve data from elsewhere)
        :return:
        """

        if c is None:
            c = Container()

        c.action_url_name = "show_poll"
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
        """
        Process data from a voting act and show the results until now

        :param request:
        :param pk:
        :return:
        """

        data = request.POST.copy()
        # process numeric form data:

        cregex = re.compile(r"option_\d+_input")
        option_pairs = [(k, int(v[0])) for k, v in data.items() if cregex.match(k)]
        option_pairs.sort()

        # after ensuring correct order we can drop the keys and represent the list a one string
        mood_values = repr([v for k, v in option_pairs])

        c = Container()
        c.username = data.get("username")
        c.msg = data
        c.pk = pk

        c.action_url_name = "show_poll"
        c.min = -3
        c.max = 2

        the_poll = get_object_or_404(models.Poll, pk=pk)

        me = models.MoodExpression(username=c.username, poll=the_poll, mood_values=mood_values)
        me.save()

        # !! read the current user from session data and look if they already voted
        c.startval = 0

        # get all votes on the current poll
        me_list = models.MoodExpression.objects.filter(poll=pk)

        c.poll = get_object_or_404(models.Poll, pk=pk)
        c.option_list = parse_option_list(c.poll.optionlist)
        context = dict(c=c, )

        return ViewPollResult().get(request, pk, c=c)


class ViewPollResult(View):

    @staticmethod
    def get(request, pk, c=None):

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

            # !! introduce datetime
            c.user_voting_acts.append((me.username, "2019-12-15 13:52:41"))

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
        # a) how many people vote for that option
        # b) how strong is there opinion in average
        # c) how strong is there opinion in total score
        # -> for every option of the option_list, we store three triples (one for negative, neutral, positive)

        c.pos_res, c.neg_res, c.neu_res = [], [], []

        for p, n, nt, opt_cont in zip(pos, neg, neu, c.option_list):
            mean_p = map_normed_mean_to_09(p, 2)
            triple = (len(p), str(mean_p)[2:], sum(p))
            c.pos_res.append(triple)
            opt_cont.approvals = triple

            mean_n = map_normed_mean_to_09(n, -3)
            triple = (len(n), str(mean_n)[3:], sum(n))
            c.neg_res.append(triple)
            opt_cont.resistances = triple

            # for neutral votes no mean has to be calculated, because every value is 0
            triple = (len(nt), "0", len(nt))
            c.neu_res.append(triple)
            opt_cont.neutrals = triple

        context = dict(c=c, )

        return render(request, "{}/main_poll_result.html".format(appname), context)

    @staticmethod
    def post(request):
        pass


# ### Helper functions ####

def list_of_empty_lists(n):
    return [list() for i in range(n)]


def mean(seq):
    if len(seq) == 0:
        return 0.0
    return sum(seq, 0.0) / len(seq)


def map_normed_mean_to_09(seq, end_of_scale, round_result=1):
    """
    - calculate the mean of num,
    - normalize it with the "maximum" possible value (w.r.t. abs), -> somthing in [0, 1]
    - map this interval to [0, 0.9]

    Rationale: we want to compactly express how strong is approval and rejection - one number is needed.
    Highest number = 0 would be confusing

    :param seq:             sequence of numbers (assume all have the same sign)
    :param end_of_scale:    max possible value (min possible for negeative)
    :param round_result:    False or int (digits)
    :return:
    """
    res = mean(seq) / end_of_scale * 0.9
    if round_result is not False:
        return round(res, round_result)
    else:
        return res
