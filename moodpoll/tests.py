from django.test import TestCase
from django.urls import reverse

from . import utils

from ipydex import IPS

# py3 manage.py test moodpoll


class TestApp1(TestCase):

    def _test_interactive(self):
        option_list = ["Option 1",
                       "Option 2",
                       "Option 3",
                       "Option 4",
                       "Option 'A'",
                       'Option "B"',
                       "Option Ä",
                       ]
        IPS()


class TestSimplePages(TestCase):

    def test_simple_pages_url_data_integrity(self):

        # test that we do not provoke an error with invalid keys
        invalid_url_response = utils.duplicated_urls["asdfgthzjuk"]

        for k, v in utils.duplicated_urls.items():
            if v == invalid_url_response:
                continue
            with self.subTest(k=k):
                expected = reverse(k)
                self.assertEqual(v, expected)


class TestViews(TestCase):

    def test_index(self):
        response = self.client.get(reverse('landing-page'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "__invalid_url__")
