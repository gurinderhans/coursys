from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from settings import CAS_SERVER_URL
from advisornotes.models import NonStudent
from courselib.testing import basic_page_tests


class AdvistorNotestest(TestCase):
    fixtures = ['test_data']

    def test_new_nonstudent_not_advisor(self):
        client = Client()
        client.login(ticket="0ppp0", service=CAS_SERVER_URL)
        response = client.get(reverse('advisornotes.views.new_nonstudent'))
        self.assertEqual(response.status_code, 403, "Student shouldn't have access")

    def test_new_nonstudent_is_advisor(self):
        client = Client()
        client.login(ticket="dzhao", service=CAS_SERVER_URL)
        response = client.get(reverse('advisornotes.views.new_nonstudent'))
        self.assertEqual(response.status_code, 200)

    def test_new_nonstudent_post_failure(self):
        client = Client()
        client.login(ticket="dzhao", service=CAS_SERVER_URL)
        response = client.post(reverse('advisornotes.views.new_nonstudent'), {'first_name': 'test123'})
        self.assertEqual(response.status_code, 200, "Should be brought back to form")
        q = NonStudent.objects.filter(first_name='test123')
        self.assertEqual(len(q), 0, "Nonstudent should not have been created")

    def test_new_nonstudent_post_success(self):
        client = Client()
        client.login(ticket="dzhao", service=CAS_SERVER_URL)
        response = client.post(reverse('advisornotes.views.new_nonstudent'), {'first_name': 'test123', 'last_name': 'test_new_nonstudent_post'})
        self.assertEqual(response.status_code, 302, 'Should have been redirected')
        q = NonStudent.objects.filter(first_name='test123')
        self.assertEqual(len(q), 1, "There should only be one result")
        self.assertEqual(q[0].last_name, 'test_new_nonstudent_post')

    def test_artifact_notes_success(self):
        """
        Check overall pages for the grad module and make sure they all load
        """
        client = Client()
        client.login(ticket="dzhao", service=CAS_SERVER_URL)

        for view in ['new_nonstudent', 'new_artifact', 'view_artifacts',
                     'view_courses', 'view_course_offerings']:
            try:
                url = reverse('advisornotes.views.' + view, kwargs={})
                response = basic_page_tests(self, client, url)
                self.assertEqual(response.status_code, 200)
            except:
                print "with view==" + repr(view)
                raise
