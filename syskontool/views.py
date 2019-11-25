# from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    # return HttpResponse("Hello world!")

    return view_test(request)


# empty object to store some attributes at runtime
class Container(object):
    pass


option_list = [ "Even Mondays",
                "Uneven Mondays",
                "Uneven Tuesdays",
                "Uneven Wednesdays",
                ]

appname = "syskontool"


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
