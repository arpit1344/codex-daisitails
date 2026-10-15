import io
from unittest.mock import patch
from email.message import Message

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.core.files.storage import InMemoryStorage

from .importer import process_next, validate_source
from .models import Tag, VideoImport, Video


class ImportTests(TestCase):
    def test_untrusted_and_private_sources_are_rejected(self):
        with self.assertRaises(ValidationError):
            validate_source('https://localhost/video.mp4')
        with patch.dict('os.environ', {'VIDEO_IMPORT_ALLOWED_HOSTS': 'source.example'}), patch('videos.importer.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaises(ValidationError):
                validate_source('https://source.example/video.mp4')

    def test_import_produces_private_editable_draft_and_tags(self):
        job = VideoImport.objects.create(title='Licensed clip', source_url='https://source.example/clip.mp4', rights_confirmed=True)
        tag = Tag.objects.create(name='Nature')
        job.tags.add(tag)
        response = io.BytesIO(b'\x00\x00\x00\x18ftypisom' + b'0' * 40)
        response.headers = Message()
        response.headers['Content-Type'] = 'video/mp4'
        storage = InMemoryStorage()
        with patch('videos.importer.validate_source', return_value='.mp4'), patch('videos.importer.build_opener') as opener, patch.object(Video._meta.get_field('file'), 'storage', storage):
            opener.return_value.open.return_value = response
            self.assertTrue(process_next())
        job.refresh_from_db()
        self.assertEqual(job.status, 'ready')
        self.assertFalse(job.video.is_published)
        self.assertEqual(list(job.video.tags.all()), [tag])
        self.assertEqual(self.client.get(job.video.get_absolute_url()).status_code, 404)
        user = get_user_model().objects.create_superuser('reviewer', password='test-only')
        self.client.force_login(user)
        preview = self.client.get(reverse('admin:videos_video_preview', args=[job.video_id]))
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview['X-Robots-Tag'], 'noindex, nofollow')

    def test_failure_has_no_public_video_and_can_be_retried(self):
        job = VideoImport.objects.create(title='Bad source', source_url='https://localhost/clip.mp4', rights_confirmed=True)
        self.assertTrue(process_next())
        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        self.assertFalse(Video.objects.exists())
