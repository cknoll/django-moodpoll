from django.test import TestCase

from . import models as m

from ipydex import IPS

# py3 manage.py test moodpoll


class TestApp1(TestCase):

    def test_interactive(self):
        option_list = ["Option 1",
                       "Option 2",
                       "Option 3",
                       "Option 4",
                       "Option 'A'",
                       'Option "B"',
                       "Option Ä",
                       ]
        IPS()