# from django.http import HttpResponse
from django.shortcuts import render
from . import models

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

appname = "syskontool"


def populate_db():
    u = models.User(name="u1")
    u.save()

    p = models.Poll(optionlist=repr(option_list))
    p.save()

    values = [0]*len(option_list)

    me = models.MoodExpression(user=u, poll=p, mood_values=repr(values))
    me.save()


def process_ol(ol):
    res = []
    for idx, option_str in enumerate(ol):
        C = Container()
        C.content = option_str
        C.id = f"option_{idx}"

        res.append(C)

    return res


def view_test(request):

    pol = process_ol(option_list)

    context = {"option_list": pol}

    return render(request, f'{appname}/main_form.html', context)
