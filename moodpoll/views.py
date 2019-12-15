# from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
import re
from . import models
from . import forms

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

appname = "moodpoll"


def populate_db():
    u = models.User(name="u1")
    u.save()

    p = models.Poll(optionlist=repr(option_list))
    p.save()

    values = [0]*len(option_list)

    me = models.MoodExpression(user=u, poll=p, mood_values=repr(values))
    me.save()


def parse_option_list(ol):
    res = []
    for idx, option_str in enumerate(ol):
        C = Container()
        C.content = option_str
        C.id = f"option_{idx}"

        res.append(C)

    return res


def view_test(request):

    pol = parse_option_list(option_list)

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
        c.option_list = parse_option_list(c.poll.optionlist.split("\n"))
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

        me = models.MoodExpression(username=c.username, poll=pk, mood_values=mood_values)
        me.save()

        # !! read the current user from session data and look if they already voted
        c.startval = 0

        # get all votes on the current poll
        me_list = models.MoodExpression.objects.filter(poll=pk)

        c.poll = get_object_or_404(models.Poll, pk=pk)
        c.option_list = parse_option_list(c.poll.optionlist.split("\n"))
        context = dict(c=c, )

        return ViewPollResult().get(request, pk, c=c)


class ViewPollResult(View):

    @staticmethod
    def get(request, pk, c=None):

        if c is None:
            c = Container()

        me_list = models.MoodExpression.objects.filter(poll=pk)
        c.poll = get_object_or_404(models.Poll, pk=pk)
        context = dict(c=c, )

        from ipydex import IPS
        IPS()
        return render(request, "{}/main_poll_result.html".format(appname), context)

    @staticmethod
    def post(request):
        pass