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
# noinspection PyUnresolvedReferences
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


def parse_option_list(ol_str, start_values=None):

    """

    :param ol_str:          option_list_string (options separated by newline)
    :param start_values:    None or sequence of default voting values (e.g. from a previous vote)
    :return:
    """

    ol = ol_str.strip().split("\n")
    if start_values is None:
        start_values = [0]*len(ol)

    # IPS()
    assert len(start_values) == len(ol)

    res = []
    for idx, option_str in enumerate(ol):
        data_c = Container()
        data_c.content = option_str
        data_c.id = f"option_{idx}"
        data_c.start_value = start_values[idx]

        res.append(data_c)

    return res


def view_test(request):

    pol = parse_option_list(option_list_str)

    context = {"option_list": pol}

    return render(request, "{}/main_form.html".format(appname), context)


# noinspection PyMethodMayBeStatic
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

        if c is None:
            c = Container()
            c.start_values = None
            c.name_conflict_mode = False

        c.full_url = request.get_raw_uri()
        url_c = get_segmented_urls(request, pk)
        # noinspection PyUnresolvedReferences
        c.poll_url = url_c.full_show_poll

        if request.session.pop("poll_created", None) == pk:
            # This poll was just created by this user. This should be mentioned
            c.msg = "Successfully created new poll:"

            # add unit test comment
            c.utc_new_poll = "new_poll_{}".format(pk)

        c.action_url_name = "poll_eval"
        c.pk = pk
        c.min = -3
        c.max = 2

        c.poll = get_object_or_404(models.Poll, pk=pk)
        c.option_list = parse_option_list(c.poll.optionlist, c.start_values)
        context = dict(c=c, )

        return render(request, "{}/main_show_poll.html".format(appname), context)

    @staticmethod
    def post(request, pk):
        pass


class ViewPollResult(View):

    @staticmethod
    def get(request, pk, c=None):

        c = evaluate_poll_results(pk, c)

        url_c = get_segmented_urls(request, pk)
        # noinspection PyUnresolvedReferences
        c.poll_url = url_c.full_show_poll
        context = dict(c=c, )

        return render(request, "{}/main_poll_result.html".format(appname), context)

    @staticmethod
    def post(request):
        pass


class ViewPollEvaluation(View):

    # noinspection PyUnusedLocal
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
        c = Container()
        # process numeric form data:

        # the field_names are like "option_0_input", "option_1_input", ...
        # we finde them via regular expressions
        cregex = re.compile(r"option_\d+_input")

        option_pairs = [(k, int(v)) for k, v in data.items() if cregex.match(k)]
        option_pairs.sort()

        # after ensuring correct order we can drop the keys and save only one list of integers
        c.mood_values = [v for k, v in option_pairs]
        # save list as string (to store it in the db)
        c.mood_values_str = repr(c.mood_values)

        c.username = data.get("username")
        c.post_data = data

        # if the checkbox is not checked, the key is not in data
        overwrite_flag = data.get("overwrite_flag", False)

        the_poll = get_object_or_404(models.Poll, pk=pk)

        # try to find a MoodExpression with the same combination of poll and username

        # noinspection PyUnresolvedReferences
        old_me_list = models.MoodExpression.objects.filter(poll=pk, username=c.username)

        if len(old_me_list) == 0:
            # there is no name conflict
            if c.username == "":
                c.err_msg = f"An empty name is not allowed."
                c.err_comment = "utc_invalid_data_warning:empty_name"
                # noinspection PyTypeChecker
                return self.handle_invalid_data(request, pk, c)

            if overwrite_flag in ("True", True):
                c.err_msg = f'The submitted data was inconsistent: Overwrite-mode=True, but user "{c.username}"' \
                            f"has not voted before. So, nothing to overwrite. Please double-check your name."
                c.err_comment = "utc_invalid_data_warning:flag_inconsistency"
                # noinspection PyTypeChecker
                return self.handle_invalid_data(request, pk, c)

            # create new mood expression
            me = models.MoodExpression(username=c.username, poll=the_poll, mood_values=c.mood_values_str)
        elif len(old_me_list) == 1:
            # overwrite the old db-entry or handle name-conflict
            me = old_me_list[0]
            if overwrite_flag == "True":
                # update the values and the time
                me.mood_values = c.mood_values_str
                me.datetime = timezone.now()
            else:
                # noinspection PyTypeChecker
                return self.handle_name_conflict(request, pk, me, c)
        else:
            # this should not happen
            msg = "Unexpected: multiple votes for username {} and poll {}".format(c.username, the_poll)
            raise DataIntegrityError(msg)
        me.save()

        return redirect(reverse("poll_result", kwargs={"pk": pk}))

    @staticmethod
    def handle_name_conflict(request, pk, old_me, c):
        """
        Called if a username is re-used for one poll.

        -> Gather data which should be displayed on the polling view

        :param request:
        :param pk:          pk of the poll
        :param old_me:      old mood_expression
        :param c:           container with preprocessed data from the caller
        :return:
        """

        c.old_dt_string = datetime_string_from_dt_object(old_me.datetime)
        c.start_values = c.mood_values
        c.name_conflict_mode = True
        c.old_username = old_me.username

        return ViewPoll.get(request, pk, c=c)

    @staticmethod
    def handle_invalid_data(request, pk, c):
        """
        Called in case of data inconsitencies

        -> Gather data which should be displayed on the polling view

        :param request:
        :param pk:          pk of the poll
        :param c:           container with preprocessed data from the caller
        :return:
        """

        c.start_values = c.mood_values
        c.err_mode = True
        assert len(c.err_msg) > 0

        return ViewPoll.get(request, pk, c=c)


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


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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
    c.n_opts = len(c.option_list)

    # noinspection PyUnresolvedReferences
    me_list = models.MoodExpression.objects.filter(poll=pk)

    c.user_voting_acts = []
    c.mood_values = []
    # produce a list of lists of ints

    for me in me_list:
        c.mood_values.append(json.loads(me.mood_values))

        dt = datetime_string_from_dt_object(me.datetime)
        c.user_voting_acts.append((me.username, dt, me.datetime.timestamp()))

    # count positive, negative and neutral votes separately
    pos = list_of_empty_lists(c.n_opts)
    neg = list_of_empty_lists(c.n_opts)
    neu = list_of_empty_lists(c.n_opts)

    # now, mood_values now looks like [[0, 0, 1, 1, 2, 2, 1], [-2, -3, 0, 0, 1, 2, 1]]
    # (two mood expressions for 7 options)

    # iterate over all
    for mv_list in c.mood_values:
        assert len(mv_list) == c.n_opts
        for idx, mood_value in enumerate(mv_list):
            if mood_value < 0:
                neg[idx].append(mood_value)
            elif mood_value > 0:
                pos[idx].append(mood_value)
            else:
                neu[idx].append(mood_value)

    # example values:
    # In [1]: pos
    # Out[1]: [[], [], [1], [1], [2, 1], [2, 2], [1, 1]]
    #
    # In [2]: neg
    # Out[2]: [[-2], [-3], [], [], [], [], []]
    #
    # In [3]: neu
    # Out[3]: [[0], [0], [0], [0], [], [], []]

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

        # we neglect the sign for the mean (we already now that this value is negative)
        mean_n = abs(map_normed_mean_to_09(n, -3))
        # omit the "0." part of the str
        triple = (len(n), str(mean_n)[2:], sum(n))
        c.neg_res.append(triple)
        opt_cont.resistances = triple

        # for neutral votes no mean has to be calculated, because every value is 0
        triple = (len(nt), "0", len(nt))
        c.neu_res.append(triple)
        opt_cont.neutrals = triple

    # Examples:

    # In[1]: c.pos_res
    # Out[1]:
    # [(0, '0', 0),
    #  (0, '0', 0),
    #  (1, '1', 1),
    #  (1, '1', 1),
    #  (2, '5', 3),
    #  (2, '9', 4),
    #  (2, '1', 2)]
    #
    # In[2]: c.neg_res
    # Out[2]:
    # [(1, '5', -2),
    #  (1, '9', -3),
    #  (0, '0', 0),
    #  (0, '0', 0),
    #  (0, '0', 0),
    #  (0, '0', 0),
    #  (0, '0', 0)]
    #
    # In[3]: c.neu_res
    # Out[3]:
    # [(1, '0', 1),
    #  (1, '0', 1),
    #  (1, '0', 1),
    #  (1, '0', 1),
    #  (0, '0', 0),
    #  (0, '0', 0),
    #  (0, '0', 0)]

    sort_poll_results(c)

    # sort user_voting_acts by timestamp (3rd argument) (descending)
    c.user_voting_acts.sort(key=lambda arg: arg[2], reverse=True)

    return c


def sort_poll_results(c):
    """

    Sorting orders: signed_rejection_average (dec), rejection_people (inc), acceptance_average (dec),
    acceptance_people (dec).


    :param c:  data container with the (unsorted results)
    """

    def key_func(i):
        """
        for each index generate a numeric tuple. Such tuples can be easily compared: if first entries are equal,
        compeare the second entries, etc.
        For those values which should be sorted in decreasing order we use negation.

        :param i:   index
        :return:
        """
        # noinspection PyRedundantParentheses
        return (-c.neg_res[i][2], c.neg_res[i][0], -c.pos_res[i][2], -c.pos_res[i][0],)
        
    c.sorted_index_list = list(range(c.n_opts))
    c.key_tuples = [key_func(i) for i in range(c.n_opts)]

    c.sorted_index_list.sort(key=key_func)

    resort_list_in_place(c.neg_res, new_order=c.sorted_index_list)
    resort_list_in_place(c.pos_res, new_order=c.sorted_index_list)
    resort_list_in_place(c.neu_res, new_order=c.sorted_index_list)
    resort_list_in_place(c.option_list, new_order=c.sorted_index_list)


def resort_list_in_place(original_list, new_order):
    """

    :param original_list:
    :param new_order:       sequence of ints (a permutation of range(len(original_list)))

    :return: None
    """

    # note this temporarily creates a new list
    # taken from: https://stackoverflow.com/a/6098306/333403

    original_list[:] = [original_list[i] for i in new_order]



def list_of_empty_lists(n):
    # noinspection PyUnusedLocal
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


def get_segmented_urls(request, pk):
    """

    :param request:
    :param pk:
    :return:            Container
    """

    data_c = Container()
    data_c.raw_url = request.get_raw_uri()
    data_c.protocol = "https://" if request.is_secure() else "http://"
    data_c.host = request.get_host()
    data_c.show_poll = reverse("show_poll", kwargs={"pk": pk})
    data_c.res_poll = reverse("poll_result", kwargs={"pk": pk})
    data_c.full_show_poll = f"{data_c.protocol}{data_c.host}{data_c.show_poll}"
    data_c.full_res_poll = f"{data_c.protocol}{data_c.host}{data_c.res_poll}"

    return data_c
