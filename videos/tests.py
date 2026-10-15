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
        self.video = Video.objects.create(title='Mountain journey', slug='mountain-journey', category=self.category, language='English', duration='4:30', file=SimpleUploadedFile('journey.webm', b'upload-test-fixture'), is_published=True)
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
        response = self.client.post(reverse('admin:videos_video_add'), {'title': 'Uploaded video', 'slug': 'uploaded-video', 'description': 'Uploaded through admin', 'category': self.category.pk, 'language': 'Hindi', 'file': SimpleUploadedFile('uploaded.mp4', b'upload-test-fixture', content_type='video/mp4'), 'duration': '1:00', 'is_published': 'on', 'editor_rating': '80', 'quality': 'HD', '_save': 'Save'})
        self.assertEqual(response.status_code, 302)
        uploaded = Video.objects.get(slug='uploaded-video')
        self.assertTrue(uploaded.file.storage.exists(uploaded.file.name))
        self.assertContains(self.client.get(uploaded.get_absolute_url()), 'Uploaded video')

    def test_admin_rejects_unsupported_file_extension(self):
        user = get_user_model().objects.create_superuser('manager', 'manager@example.com', 'test-password-only')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:videos_video_add'), {'title': 'Bad upload', 'slug': 'bad-upload', 'language': 'Hindi', 'editor_rating': '0', 'file': SimpleUploadedFile('script.html', b'<script></script>'), '_save': 'Save'})
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

    def test_language_and_duration_filters(self):
        self.assertContains(self.client.get(reverse('video_list'), {'language': 'English'}), self.video.title)
        self.assertNotContains(self.client.get(reverse('video_list'), {'language': 'Hindi'}), self.video.title)
        self.assertContains(self.client.get(reverse('video_list'), {'duration': 'short'}), self.video.title)
        self.assertNotContains(self.client.get(reverse('video_list'), {'duration': 'long'}), self.video.title)
        self.assertEqual(self.video.duration_seconds, 270)

    def test_cards_have_lazy_thumbnail_and_duration_badge(self):
        self.video.thumbnail = SimpleUploadedFile('poster.jpg', self._image_bytes(), content_type='image/jpeg')
        self.video.save()
        response = self.client.get(reverse('video_list'))
        self.assertContains(response, 'loading="lazy"')
        self.assertContains(response, 'class="duration-badge">4:30')
        self.assertTrue(self.video.thumbnail.name.endswith('.webp'))

    @staticmethod
    def _image_bytes():
        from io import BytesIO
        from PIL import Image
        output = BytesIO()
        Image.new('RGB', (1800, 1000), 'red').save(output, 'JPEG')
        return output.getvalue()

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

    def test_video_page_has_canonical_social_and_structured_metadata(self):
        self.video.description = 'A scenic mountain journey.'
        self.video.seo_title = 'Mountain Journey Video'
        self.video.save()
        response = self.client.get(self.video.get_absolute_url())
        self.assertContains(response, '<link rel="canonical" href="http://testserver/videos/mountain-journey/">')
        self.assertContains(response, '<meta property="og:type" content="video.other">')
        self.assertContains(response, '<meta property="og:title" content="Mountain Journey Video">')
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, 'VideoObject')

    def test_filtered_pages_are_noindex_with_catalog_canonical(self):
        response = self.client.get(reverse('video_list'), {'q': 'Mountain'})
        self.assertContains(response, '<meta name="robots" content="noindex,follow">')
        self.assertContains(response, '<link rel="canonical" href="http://testserver/videos/">')

    def test_sitemap_and_robots_only_advertise_public_content(self):
        sitemap = self.client.get('/sitemap.xml')
        self.assertContains(sitemap, 'http://testserver/videos/mountain-journey/')
        self.assertNotContains(sitemap, 'hidden-draft')
        robots = self.client.get('/robots.txt')
        self.assertContains(robots, 'Disallow: /admin/')
        self.assertContains(robots, 'Sitemap: http://testserver/sitemap.xml')

    def test_editor_rating_rejects_over_100(self):
        from django.core.exceptions import ValidationError
        self.video.editor_rating = 101
        with self.assertRaises(ValidationError):
            self.video.full_clean()

class HostingBootstrapTests(TestCase):
    def test_password_recovery_requires_active_window(self):
        import time
        from unittest.mock import patch
        from django.core.management import call_command
        user = get_user_model().objects.create_superuser('recovery-admin', password='old-test-password')
        password = 'New-test-password-recovery-248!'
        with patch.dict('os.environ', {'DJANGO_SUPERUSER_USERNAME': user.username, 'DJANGO_SUPERUSER_PASSWORD': password, 'DJANGO_ADMIN_RECOVERY_UNTIL': str(int(time.time()) - 10)}):
            call_command('bootstrap_admin', verbosity=0)
        user.refresh_from_db()
        self.assertTrue(user.check_password('old-test-password'))
        with patch.dict('os.environ', {'DJANGO_SUPERUSER_USERNAME': user.username, 'DJANGO_SUPERUSER_PASSWORD': password, 'DJANGO_ADMIN_RECOVERY_UNTIL': str(int(time.time()) + 600)}):
            call_command('bootstrap_admin', verbosity=0)
        user.refresh_from_db()
        self.assertTrue(user.check_password(password))

    def test_admin_creation_and_repeatability(self):
        from unittest.mock import patch
        from django.core.management import call_command
        import secrets
        password = secrets.token_urlsafe(24)
        with patch.dict('os.environ', {'DJANGO_SUPERUSER_USERNAME': 'host-admin', 'DJANGO_SUPERUSER_PASSWORD': password}):
            call_command('bootstrap_admin', verbosity=0)
            call_command('bootstrap_admin', verbosity=0)
        user = get_user_model().objects.get(username='host-admin')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(password))
        self.assertEqual(get_user_model().objects.filter(username='host-admin').count(), 1)

    def test_admin_missing_password_is_explicit_error(self):
        from unittest.mock import patch
        from django.core.management import call_command, CommandError
        with patch.dict('os.environ', {'DJANGO_SUPERUSER_USERNAME': 'host-admin', 'DJANGO_SUPERUSER_PASSWORD': ''}):
            with self.assertRaises(CommandError):
                call_command('bootstrap_admin')

    def test_demo_seed_is_repeatable_without_external_encoder(self):
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as storage, override_settings(MEDIA_ROOT=storage):
            call_command('seed_demo', verbosity=0)
            call_command('seed_demo', verbosity=0)
            self.assertEqual(Video.objects.count(), 6)
            self.assertTrue(all(v.file.storage.exists(v.file.name) for v in Video.objects.all()))
