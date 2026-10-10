import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Category, Video

class VideoWorkflowTests(TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.storage.cleanup)
        settings = override_settings(MEDIA_ROOT=self.storage.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.category = Category.objects.create(name='Travel', slug='travel')
        self.video = Video.objects.create(title='Mountain journey', slug='mountain-journey', category=self.category, file=SimpleUploadedFile('journey.webm', b'upload-test-fixture'), is_published=True)
        self.draft = Video.objects.create(title='Hidden draft', slug='hidden-draft', file=SimpleUploadedFile('draft.webm', b'upload-test-fixture'))

    def test_public_listing_search_and_categories(self):
        response = self.client.get(reverse('video_list'))
        self.assertContains(response, self.video.title)
        self.assertNotContains(response, self.draft.title)
        self.assertContains(self.client.get(reverse('video_list'), {'q': 'Mountain', 'category': 'travel'}), self.video.title)
        self.assertNotContains(self.client.get(reverse('video_list'), {'q': 'unmatched'}), self.video.title)
        self.assertNotContains(self.client.get(reverse('video_list'), {'category': 'other'}), self.video.title)

    def test_published_detail_has_player_and_draft_is_private(self):
        response = self.client.get(self.video.get_absolute_url())
        self.assertContains(response, '<video controls')
        self.assertContains(response, self.video.file.url)
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)

    def test_admin_requires_login(self):
        self.assertRedirects(self.client.get(reverse('admin:videos_video_add')), '/admin/login/?next=/admin/videos/video/add/')

    def test_admin_upload_and_publish(self):
        user = get_user_model().objects.create_superuser('manager', 'manager@example.com', 'test-password-only')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:videos_video_add'), {'title': 'Uploaded video', 'slug': 'uploaded-video', 'description': 'Uploaded through admin', 'category': self.category.pk, 'file': SimpleUploadedFile('uploaded.mp4', b'upload-test-fixture', content_type='video/mp4'), 'duration': '1:00', 'is_published': 'on', 'editor_rating': '80', 'quality': 'HD', '_save': 'Save'})
        self.assertEqual(response.status_code, 302)
        uploaded = Video.objects.get(slug='uploaded-video')
        self.assertTrue(uploaded.file.storage.exists(uploaded.file.name))
        self.assertContains(self.client.get(uploaded.get_absolute_url()), 'Uploaded video')

    def test_admin_rejects_unsupported_file_extension(self):
        user = get_user_model().objects.create_superuser('manager', 'manager@example.com', 'test-password-only')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:videos_video_add'), {'title': 'Bad upload', 'slug': 'bad-upload', 'editor_rating': '0', 'file': SimpleUploadedFile('script.html', b'<script></script>'), '_save': 'Save'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Video.objects.filter(slug='bad-upload').exists())

    def test_pagination_keeps_filters(self):
        for i in range(12):
            Video.objects.create(title=f'Mountain {i}', slug=f'mountain-{i}', category=self.category, file='videos/example.webm', is_published=True)
        response = self.client.get(reverse('video_list'), {'q': 'Mountain', 'category': 'travel'})
        self.assertContains(response, 'q=Mountain&amp;category=travel&amp;page=2')
        self.assertEqual(len(self.client.get(reverse('video_list'), {'q': 'Mountain', 'category': 'travel', 'page': 2}).context['page']), 1)

    def test_sorting_by_editor_rating_and_views(self):
        second = Video.objects.create(title='Another video', slug='another', file='videos/example.mp4', is_published=True, editor_rating=90, views=100)
        self.assertEqual(self.client.get(reverse('video_list'), {'sort': 'top'}).context['page'][0], second)
        self.assertEqual(self.client.get(reverse('video_list'), {'sort': 'views'}).context['page'][0], second)

    def test_views_only_increment_on_published_get(self):
        self.client.head(self.video.get_absolute_url())
        self.video.refresh_from_db()
        self.assertEqual(self.video.views, 0)
        self.client.get(self.video.get_absolute_url())
        self.video.refresh_from_db()
        self.assertEqual(self.video.views, 1)
        self.client.get(self.draft.get_absolute_url())
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.views, 0)

    def test_category_counts_exclude_drafts(self):
        self.draft.category = self.category
        self.draft.save()
        response = self.client.get(reverse('video_list'))
        self.assertEqual(response.context['categories'][0].published_count, 1)

    def test_editor_rating_rejects_over_100(self):
        from django.core.exceptions import ValidationError
        self.video.editor_rating = 101
        with self.assertRaises(ValidationError):
            self.video.full_clean()
