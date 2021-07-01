from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command

from . import utils
from . import models
from .views import poll_result

# noinspection PyUnresolvedReferences
from ipydex import IPS

"""
This file is assumed to be used with the following commands
python3 manage.py test moodpoll
python3 manage.py test moodpoll --nocapture --ips

# one single test
python3 manage.py test --nocapture --rednose --ips moodpoll.tests:TestViews.test_show_poll

# with alias:
pmrn moodpoll.tests:TestViews.test_show_poll


this assumes these settings

INSTALLED_APPS = (
    ...
    'django_nose',
    ...
)

and 

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

"""

global_fixtures = ['for_unit_tests/data.json']

# admin account only for unit tests
global_login_data_admin = dict(username="admin", password="ahfahHe8")


class TestLoginMechanics(TestCase):
    fixtures = global_fixtures

    def test_login_as_admin(self):
        logged_in = self.client.login(**global_login_data_admin)
        self.assertTrue(logged_in)
        response = self.client.get(reverse('landing-page'))

        self.assertTrue(response.wsgi_request.user.is_superuser)


class TestModels(TestCase):
    fixtures = global_fixtures

    def testPollConfiguration(self):

        # noinspection PyUnresolvedReferences
        poll = models.Poll.objects.first()

        self.assertEqual(poll.mood_value_min, settings.MOOD_VALUE_MIN)


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

    @classmethod
    def setUpTestData(cls):
        cls.vote_data1 = {
            'option_1': '1',
            'option_2': '2',
            'option_3': '-1',
            'option_4': '-2',
            'option_5': '-3',
            'option_6': '0',
            'option_7': '0',
            'user_name': 'testuser2',
        }
        cls.poll_key1 = 1102838733

    def test_index(self):
        response = self.client.get(reverse('landing-page'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "__invalid_url__")

    def test_new_poll(self):
        new_poll_url = reverse('new_poll')
        response1 = self.client.get(new_poll_url)
        self.assertEqual(response1.status_code, 200)
        form = get_first_form(response1)

        form_values = {"title": "unittest_poll", "description": "", "options": "a\nb\nc"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)

        # this causes a redirect (status-code 302)
        response2 = self.client.post(new_poll_url, post_data)
        self.assertEqual(response2.status_code, 302)
        response3 = self.client.get(response2.url)
        self.assertContains(response3, "utc_show_poll")
        # noinspection PyUnresolvedReferences
        poll = models.Poll.objects.last()
        self.assertFalse(poll.require_name)
        self.assertFalse(poll.expose_veto_names)

    def test_new_poll2(self):
        new_poll_url = reverse('new_poll')
        response1 = self.client.get(new_poll_url)
        form = get_first_form(response1)

        # test with require_name
        form_values = {"title": "unittest_poll", "options": "a\nb\nc", "require_name": "True"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)

        response2 = self.client.post(new_poll_url, post_data)
        response3 = self.client.get(response2.url)
        self.assertContains(response3, "utc_show_poll")
        # noinspection PyUnresolvedReferences
        poll = models.Poll.objects.last()
        self.assertTrue(poll.require_name)
        self.assertFalse(poll.expose_veto_names)

        # test with only expose_veto_names
        form_values = {"title": "unittest_poll", "options": "a\nb\nc", "expose_veto_names": "True"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)

        response2 = self.client.post(new_poll_url, post_data)
        response3 = self.client.get(response2.url)
        self.assertContains(response3, "utc_show_poll")
        # noinspection PyUnresolvedReferences
        poll = models.Poll.objects.last()
        self.assertTrue(poll.require_name)
        self.assertTrue(poll.expose_veto_names)
        self.assertContains(response3, "utc_toast_info:anonymous_vetos_disabled")

    def test_new_poll_with_inline_title(self):
        new_poll_url = reverse('new_poll')
        response1 = self.client.get(new_poll_url)
        self.assertEqual(response1.status_code, 200)

        # form, action_url = get_form_by_action_url(response1, "new_poll")
        form = get_first_form(response1)

        # specify the title as a special option
        form_values = {"title": "", "options": "# test-title_ABC\na\nb\nc"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)

        # this causes a redirect (status-code 302)
        response2 = self.client.post(new_poll_url, post_data)

        self.assertEqual(response2.status_code, 302)
        response3 = self.client.get(response2.url)
        self.assertContains(response3, "utc_show_poll")
        self.assertContains(response3, "utc_toast_success")

        # noinspection PyUnresolvedReferences
        poll = models.Poll.objects.last()
        self.assertEquals(poll.title, "test-title_ABC")

        # noinspection PyUnresolvedReferences
        poll_options = models.PollOption.objects.filter(poll=poll)
        for po, title in zip(poll_options, ["a", "b", "c"]):
            self.assertEqual(po.text, title)

        # try again but now with only the title

        response1 = self.client.get(new_poll_url)
        form = get_first_form(response1)

        # specify the title as a special option (but nothing more)
        form_values = {"title": "", "options": "# test-title_ABC2\n"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)
        response2 = self.client.post(new_poll_url, post_data)

        # ensure redirect
        self.assertEqual(response2.status_code, 302)
        response3 = self.client.get(response2.url)
        self.assertContains(response3, "utc_new_poll")
        self.assertContains(response3, "utc_toast_error: empty_poll_option_list")

    def test_new_poll_with_md_description(self):
        new_poll_url = reverse('new_poll')
        response1 = self.client.get(new_poll_url)
        self.assertEqual(response1.status_code, 200)

        form = get_first_form(response1)
        self.assertIsNotNone(form)

        md_description = "*test123* see: <https://example.com>"
        form_values = {"title": "unittest_poll", "description": md_description, "options": "a\nb\nc"}
        post_data = generate_post_data_for_form(form, spec_values=form_values)

        # this causes a redirect (status-code 302)
        response2 = self.client.post(new_poll_url, post_data)
        self.assertEqual(response2.status_code, 302)
        response3 = self.client.get(response2.url)

        self.assertContains(response3, "<em>test123</em>")
        self.assertContains(response3, '<a href="https://example.com">')

    def test_show_poll(self):
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})

        # noinspection PyUnresolvedReferences
        self.assertEqual(len(models.PollReply.objects.all()), 1)
        response = self.client.get(url)
        self.assertContains(response, "utc_show_poll")
        form = get_first_form(response)
        self.assertNotEqual(form, None)

        # c0 = views_monolith.evaluate_poll_results(pk=1)
        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)
        mood_sums = poll_result.get_mood_sums(poll)

        # in the fixtures only one person had voted so far
        self.assertEqual(len(mood_sums), poll.polloption_set.count())
        self.assertEqual(mood_sums[0]["mood_votes"], 1)

        voters = poll_result.get_voters(poll)
        self.assertEqual(voters[0]["user_name"], "testuser1")

        # now perform voting
        vote_data1 = self.vote_data1
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(url, post_data)

        # this should be a redirect to poll_results
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("poll_result", kwargs={"pk": 1, "key": self.poll_key1}))

        # now a second voting act has taken place
        mood_sums = poll_result.get_mood_sums(poll)
        self.assertEqual(mood_sums[0]["mood_votes"], 2)

        voters = poll_result.get_voters(poll)
        self.assertEqual(voters[1]["user_name"], "testuser2")

        ts1 = voters[0]["update_datetime"].timestamp()
        ts2 = voters[1]["update_datetime"].timestamp()
        self.assertTrue(ts1 < ts2)

    def test_polling_act_name_conflict1(self):
        """
        Handle a name conflict: allow multiple usages of same name
        """
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})

        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)
        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 1)

        # evaluate lazy object (because db will change soon)
        mood_sums1 = list(poll_result.get_mood_sums(poll))

        response = self.client.get(url)
        self.assertContains(response, "utc_show_poll")
        form = get_first_form(response)
        self.assertNotEqual(form, None)

        vote_data1 = self.vote_data1
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)

        # perform another vote for testuser1 (conflicting name)
        # new behaviour: allow multiple usages of the same name
        # this is related to https://codeberg.org/cknoll/django-moodpoll/issues/16
        self.assertEqual(voters[0]["user_name"], "testuser1")
        post_data.update(user_name="testuser1")

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)

        # noinspection PyUnusedLocal
        response = self.client.get(response.url)
        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 2)

        # assert that the values have changed:
        mood_sums2 = poll_result.get_mood_sums(poll)
        self.assertNotEqual(mood_sums1[0], mood_sums2[0])

    def test_polling_act_name_conflict2(self):
        """
        Handle a name conflict with poll.require_name
        """
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})

        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)
        poll.require_name = True
        poll.save()
        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 1)

        # evaluate lazy object (because db will change soon)
        mood_sums1 = list(poll_result.get_mood_sums(poll))

        response = self.client.get(url)
        self.assertContains(response, "utc_show_poll")
        form = get_first_form(response)
        self.assertNotEqual(form, None)

        vote_data1 = self.vote_data1
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)

        # perform another vote for testuser1 (conflicting name)
        # new behaviour: allow multiple usages of the same name
        # this is related to https://codeberg.org/cknoll/django-moodpoll/issues/16
        self.assertEqual(voters[0]["user_name"], "testuser1")
        post_data.update(user_name="testuser1")

        response = self.client.post(url, post_data)
        response = self.client.get(response.url)

        self.assertContains(response, "utc_toast_error:user_name_collision")

        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 1)

        # assert that the values have NOT changed:
        mood_sums2 = poll_result.get_mood_sums(poll)
        self.assertEqual(mood_sums1[0], mood_sums2[0])

    def test_polling_act_empty_name_default(self):
        """
        default case for empty name: "Anonymous #1" etc
        """
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})

        # noinspection PyUnresolvedReferences
        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)
        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 1)

        response = self.client.get(url)
        self.assertContains(response, "utc_show_poll")
        form = get_first_form(response)
        self.assertNotEqual(form, None)

        # now try empty username
        vote_data1 = {**self.vote_data1, "user_name": ""}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(url, post_data)

        # new behaviour: post is accepted, user_name is 'Anonymous'
        self.assertEqual(response.status_code, 302)

        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 2)
        self.assertEqual(voters.last()["user_name"], "Anonymous #1")

    def test_polling_act_empty_name_with_require_name(self):
        """
        if poll.require_name: reject empty name for polling
        """
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})

        # noinspection PyUnresolvedReferences
        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)
        poll.require_name = True
        poll.save()
        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 1)

        response = self.client.get(url)
        self.assertContains(response, "utc_show_poll")
        form = get_first_form(response)
        self.assertNotEqual(form, None)

        # now try empty username
        vote_data1 = {**self.vote_data1, "user_name": ""}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(url, post_data)

        # should redirect to show_poll again with error message
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, "utc_show_poll")
        self.assertContains(response, "utc_toast_error:empty_user_name")

        voters = poll_result.get_voters(poll)
        self.assertEqual(len(voters), 1)

    def test_anonymous_veto(self):
        """
        test special handling of minimum vote-value (-> veto)
        """
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})
        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)

        # no vetos up to now
        # noinspection PyUnresolvedReferences
        for po in models.PollOption.objects.filter(poll=poll):
            self.assertEqual(po.get_minimum_vote_cnt(), 0)

        response = self.client.get(url)
        form = get_first_form(response)

        vote_data1 = {**self.vote_data1, "option_5": poll.mood_value_min}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        # noinspection PyUnusedLocal
        response = self.client.post(url, post_data)

        # expect exactly one veto
        # noinspection PyUnresolvedReferences
        for po in models.PollOption.objects.filter(poll=poll):

            if po.id == 5:
                # corresponds to option_5 above
                self.assertEqual(po.get_minimum_vote_cnt(), 1)
            else:
                self.assertEqual(po.get_minimum_vote_cnt(), 0)

        # ensure that no names are listed
        response = self.client.get(response.url)
        self.assertNotContains(response, "utc_exposed_veto_name")

        # two people voted (testuser1 is in the fixtures)
        self.assertContains(response, "utc_number_of_participants:2")

    def test_expose_veto_names(self):
        """
        if poll.expose_veto_names: all veto users should be listed on result_view
        """
        url = reverse('show_poll', kwargs={"pk": 1, "key": self.poll_key1})
        poll = utils.get_poll_or_4xx(pk=1, key=self.poll_key1)
        poll.expose_veto_names = True
        poll.require_name = True  # this would be enforced during creation
        poll.save()

        response = self.client.get(url)
        form = get_first_form(response)

        veto = poll.mood_value_min
        # ensure that empty name provokes an error
        # (for real users this is prevented by the `require` attribute of the input field)
        vote_data1 = {**self.vote_data1, "user_name": "", "option_5": veto}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(url, post_data)
        response = self.client.get(response.url)
        self.assertContains(response, "utc_toast_error:empty_user_name")

        # ensure that the names are listed
        vote_data1 = {**self.vote_data1, "option_5": veto}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(url, post_data)
        response = self.client.get(response.url)
        self.assertContains(response, "utc_exposed_veto_name:testuser2 (1)")

        vote_data1 = {**self.vote_data1, "user_name": "neysayer", "option_1": veto, "option_2": veto, "option_5": veto}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        self.client.post(url, post_data)
        vote_data1 = {**self.vote_data1, "user_name": "ayesayer", "option_5": 1}
        post_data = generate_post_data_for_form(form, spec_values=vote_data1)
        response = self.client.post(url, post_data)
        response = self.client.get(response.url)
        self.assertContains(response, "utc_exposed_veto_name:testuser2 (1)")
        self.assertContains(response, "utc_exposed_veto_name:neysayer (3)")
        self.assertNotContains(response, "utc_exposed_veto_name:ayesayer")

        # four people voted (testuser1 is in the fixtures)
        self.assertContains(response, "utc_number_of_participants:4")


class TestCommands(TestCase):
    fixtures = global_fixtures

    def test_removespam(self):
        poll_number1 = models.Poll.objects.all().count()
        p = models.Poll(creation_datetime=timezone.now() - timezone.timedelta(hours=3))
        p.save()

        poll_number2 = models.Poll.objects.all().count()
        self.assertEqual(poll_number2, poll_number1 + 1)
        call_command("removespam")
        poll_number3 = models.Poll.objects.all().count()
        self.assertEqual(poll_number3, poll_number1)


# ------------------------------------------------------------------------
# below lives auxiliary code which is related to testing but does not contain tests
# ------------------------------------------------------------------------


def get_first_form(response):
    """
    Auxiliary function that returns a bs-object of the first form which is specifies by action-url.

    :param response:
    :return:
    """
    bs = BeautifulSoup(response.content, 'html.parser')
    forms = bs.find_all("form")

    return forms[0]


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
        name = f.attrs.get('name')

        if name is None:
            # ignore fields without a name (relevant for dropdown checkbox)
            continue

        if name.startswith("captcha"):
            # special case for captcha fields (assume CAPTCHA_TEST_MODE=True)
            post_data[name] = "passed"
        else:
            post_data[name] = default_value

    post_data.update(spec_values)

    return post_data
