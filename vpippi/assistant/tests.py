from django.test import TestCase, override_settings

from cv.models import CVVariant
from jobs.models import JobApplication

from .models import PendingAction

TOKEN = 'x' * 40
AUTH = {'HTTP_AUTHORIZATION': f'Bearer {TOKEN}'}


@override_settings(ASSISTANT_API_TOKEN=TOKEN)
class ToolApiTests(TestCase):
    def call(self, name, args=None, **extra):
        return self.client.post(
            f'/api/tools/{name}/', data=args or {}, content_type='application/json', **{**AUTH, **extra},
        )

    def test_missing_or_wrong_token_is_404(self):
        self.assertEqual(self.client.get('/api/tools/').status_code, 404)
        self.assertEqual(self.client.get('/api/tools/', HTTP_AUTHORIZATION='Bearer nope').status_code, 404)
        self.assertEqual(self.client.post('/api/tools/list_cv_variants/', content_type='application/json').status_code, 404)

    @override_settings(ASSISTANT_API_TOKEN='short')
    def test_short_token_disables_api(self):
        self.assertEqual(self.client.get('/api/tools/', HTTP_AUTHORIZATION='Bearer short').status_code, 404)

    def test_list_tools_marks_confirmation(self):
        data = self.client.get('/api/tools/', **AUTH).json()
        flags = {t['name']: t['requires_confirmation'] for t in data['tools']}
        self.assertTrue(flags['delete_cv_variant'])
        self.assertFalse(flags['edit_cv_content'])

    def test_write_applies_immediately_and_edit_works(self):
        r = self.call('create_cv_variant', {'slug': 'apple', 'label': 'Apple', 'page_title': 'A'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['output']['status'], 'applied')
        self.call('write_cv_content', {'slug': 'apple', 'source_content': '<p>hello world</p>'})
        r = self.call('edit_cv_content', {'slug': 'apple', 'old_text': 'world', 'new_text': 'there'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(CVVariant.objects.get(slug='apple').source_content, '<p>hello there</p>')
        got = self.call('get_cv_variant', {'slug': 'apple'}).json()['output']
        self.assertEqual(got['source_content'], '<p>hello there</p>')

    def test_delete_is_staged_until_confirmed(self):
        CVVariant.objects.create(slug='old', label='Old')
        out = self.call('delete_cv_variant', {'slug': 'old'}).json()['output']
        self.assertEqual(out['status'], 'pending_confirmation')
        self.assertTrue(CVVariant.objects.filter(slug='old').exists())

        pending = self.client.get('/api/actions/', **AUTH).json()['pending_actions']
        self.assertEqual([p['id'] for p in pending], [out['action_id']])

        r = self.client.post(f"/api/actions/{out['action_id']}/confirm/", **AUTH)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertFalse(CVVariant.objects.filter(slug='old').exists())
        self.assertEqual(PendingAction.objects.get().status, PendingAction.STATUS_CONFIRMED)

    def test_cancel_keeps_data(self):
        JobApplication.objects.create(title='Eng', company='Acme')
        job = JobApplication.objects.get()
        out = self.call('delete_job_application', {'id': job.id}).json()['output']
        r = self.client.post(f"/api/actions/{out['action_id']}/cancel/", **AUTH)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(JobApplication.objects.filter(pk=job.pk).exists())

    def test_locked_variant_refuses_writes(self):
        CVVariant.objects.create(slug='final', label='Final', is_locked=True)
        r = self.call('write_cv_content', {'slug': 'final', 'source_content': 'x'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())

    def test_bad_input_returns_400_not_500(self):
        self.assertEqual(self.call('nope').status_code, 400)
        self.assertEqual(self.call('get_cv_variant', {'unexpected': 1}).status_code, 400)
        r = self.client.post('/api/tools/list_cv_variants/', data='[1]', content_type='application/json', **AUTH)
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/tools/list_cv_variants/', data='{bad', content_type='application/json', **AUTH)
        self.assertEqual(r.status_code, 400)
