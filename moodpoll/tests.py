from django.test import TestCase
from django.urls import reverse
from bs4 import BeautifulSoup

from . import utils
from . import models
from . import views

from ipydex import IPS

# py3 manage.py test moodpoll

global_fixtures = ['for_unit_tests/data.json']

# admin account only for unit tests
global_login_data_admin = dict(username="admin", password="ahfahHe8")


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


class TestHelperFuncs(TestCase):

    def test_map_mean(self):
        m09 = views.map_normed_mean_to_09
        self.assertEqual(m09([2, 2], 2), 0.9)
        self.assertEqual(m09([1, 2], 2), 0.5)
        self.assertEqual(m09([1, 1], 2), 0.1)
        self.assertEqual(m09([0], 2), 0.0)
        self.assertEqual(m09([], 2), 0.0)

        self.assertEqual(m09([-3, -3], -3), 0.9)
        self.assertEqual(m09([-1, -1], -3), 0.1)
        self.assertEqual(m09([-1, -1, -1, -1, -3], -3), 0.3)
        self.assertEqual(m09([-1, -1, -1, -1, -2], -3), 0.2)


class TestLoginMechanics(TestCase):
    fixtures = global_fixtures

    def test_login_as_admin(self):
        logged_in = self.client.login(**global_login_data_admin)
        self.assertTrue(logged_in)
        response = self.client.get(reverse('landing-page'))

        self.assertTrue(response.wsgi_request.user.is_superuser)

    def test_no_backup_without_login(self):
        response = self.client.get(reverse('do_backup'))

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.status_code, 302)

        response = self.client.get(response.url)
        self.assertEqual(response.url, "/admin/login/")


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
    fixtures = global_fixtures

    def test_index(self):
        response = self.client.get(reverse('landing-page'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "__invalid_url__")

    def test_new_poll(self):
        response1 = self.client.get(reverse('new_poll'))
        self.assertEqual(response1.status_code, 200)

        form, action_url = get_form_by_action_url(response1, "new_poll")
        self.assertIsNotNone(form)

        form_values = {"title": "unittest_poll", "description": "", "optionlist": "a\nb\nc"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)

        # this causes a redirect (status-code 302)
        response2 = self.client.post(action_url, post_data)
        self.assertEqual(response2.status_code, 302)
        response3 = self.client.get(response2.url)
        self.assertContains(response3, "utc_new_poll")
        self.assertContains(response3, "utc_show_poll")

    def test_show_poll(self):
        url = reverse('show_poll', kwargs={"pk": 1})

        # noinspection PyUnresolvedReferences
        self.assertEqual(len(models.MoodExpression.objects.all()), 2)
        response = self.client.get(url)
        self.assertContains(response, "utc_show_poll")
        form, action_url = get_form_by_action_url(response, "show_poll", pk=1)

        c0 = views.evaluate_poll_results(pk=1)

        vote_data1 = {
            'option_0_range': '0',
            'option_0_input': '0',
            'option_1_range': '1',
            'option_1_input': '1',
            'option_2_range': '2',
            'option_2_input': '2',
            'option_3_range': '-1',
            'option_3_input': '-1',
            'option_4_range': '-2',
            'option_4_input': '-2',
            'option_5_range': '-3',
            'option_5_input': '-3',
            'option_6_range': '0',
            'option_6_input': '0',
            'username': 'testuser1'
        }
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(action_url, post_data)

        # noinspection PyUnresolvedReferences
        self.assertEqual(len(models.MoodExpression.objects.all()), 3)

        c1 = views.evaluate_poll_results(pk=1)

        # results for the negative votes for option 0
        self.assertEqual(c0.neg_res[0], (1, "5", -2))

        self.assertEqual(c0.neu_res[0], (1, "0", 1))
        self.assertEqual(c1.neu_res[0], (2, "0", 2))

        self.assertEqual(c1.neg_res[1], (1, "9", -3))
        self.assertEqual(c1.neu_res[1], (1, "0", 1))
        self.assertEqual(c0.pos_res[1], (0, "0", 0))
        self.assertEqual(c1.pos_res[1], (1, "1", 1))

# ------------------------------------------------------------------------
# below lives auxiliary code which is related to testing but does not contain tests
# ------------------------------------------------------------------------


def get_form_by_action_url(response, url_name, **url_name_kwargs):
    """
    Auxiliary function that returns a bs-object of the form which is specifies by action-url.

    Also return action_url

    :param response:
    :param url_name:
    :param url_name_kwargs:
    :return:
    """
    bs = BeautifulSoup(response.content, 'html.parser')
    forms = bs.find_all("form")
    if url_name is None:
        # this accounts for the case where no action is specified (by some generic views)
        action_url = None
    else:
        action_url = reverse(url_name, kwargs=url_name_kwargs)

    for form in forms:
        action = form.attrs.get("action")
        if action == action_url:
            return form, action_url

    return None, action_url


def get_all_forms_of_class(response, theclass):
    """
    Return a list of form-objects which belong to the given class.

    This is the usecase for 'nocss_...'-classes.

    Note, this function also creates an attribute .action_url

    :param response:
    :param theclass:
    :return:
    """

    bs = BeautifulSoup(response.content, 'html.parser')
    forms = bs.find_all("form")

    res = []
    for form in forms:
        classes = form.attrs.get("class")
        if theclass in classes:
            res.append(form)

        form.action_url = form.attrs.get("action")
    return res


def get_form_fields_to_submit(form):
    """
    Return two lists: fields and hidden_fields.

    :param form:
    :return:
    """

    inputs = form.find_all("input")
    textareas = form.find_all("textarea")

    post_fields = inputs + textareas

    types_to_omit = ["submit", "cancel"]

    fields = []
    hidden_fields = []
    for field in post_fields:
        ftype = field.attrs.get("type")
        if ftype in types_to_omit:
            continue

        if ftype == "hidden":
            hidden_fields.append(field)
        else:
            fields.append(field)

    return fields, hidden_fields


def generate_post_data_for_form(form, default_value="xyz", spec_values=None):
    """
    Return a dict containing all dummy-data for the form

    :param form:
    :param default_value:   str; use this value for all not specified fields
    :param spec_values:     dict; use these values to override default value

    :return:                dict of post_data
    """

    if spec_values is None:
        spec_values = {}

    fields, hidden_fields = get_form_fields_to_submit(form)

    post_data = {}
    for f in hidden_fields:
        post_data[f.attrs['name']] = f.attrs['value']

    for f in fields:
        name = f.attrs['name']
        if name.startswith("captcha"):
            # special case for captcha fields (assume CAPTCHA_TEST_MODE=True)
            post_data[name] = "passed"
        else:
            post_data[name] = default_value

    post_data.update(spec_values)

    return post_data

