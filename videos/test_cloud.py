import io
import os
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase
from botocore.response import StreamingBody
from botocore.stub import Stubber, ANY
from storages.backends.s3 import S3Storage
from config.cloud import database_config, media_storage_config

class CloudConfigurationTests(SimpleTestCase):
    def test_local_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(database_config(Path('/tmp'), True)['ENGINE'], 'django.db.backends.sqlite3')
            self.assertEqual(media_storage_config()['BACKEND'], 'django.core.files.storage.FileSystemStorage')

    def test_persistent_mode_does_not_fall_back_to_ephemeral_storage(self):
        with patch.dict(os.environ, {'DJANGO_PERSISTENT_MODE': '1'}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                database_config(Path('/tmp'), False)
            with self.assertRaises(ImproperlyConfigured):
                media_storage_config()

    def test_postgres_certificate_and_hostname_verification(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://testuser:test-only@ep-demo.neon.tech/library?sslmode=require'}, clear=True):
            config = database_config(Path('/tmp'), False)
            self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(config['OPTIONS']['sslmode'], 'verify-full')
            self.assertTrue(Path(config['OPTIONS']['sslrootcert']).is_file())
            self.assertEqual(config['CONN_MAX_AGE'], 0)
            self.assertTrue(config['DISABLE_SERVER_SIDE_CURSORS'])

    def test_bad_database_url_does_not_reveal_credentials(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'unsupported://private-test-value'}, clear=True):
            with self.assertRaises(ImproperlyConfigured) as error:
                database_config(Path('/tmp'), False)
            self.assertNotIn('private-test-value', str(error.exception))

    def test_partial_r2_config_fails(self):
        with patch.dict(os.environ, {'R2_BUCKET_NAME': 'test-only'}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                media_storage_config()

    def r2_environment(self):
        return {'R2_ENDPOINT_URL': 'https://test-account.r2.cloudflarestorage.com', 'R2_BUCKET_NAME': 'test-only', 'R2_ACCESS_KEY_ID': 'test-only', 'R2_SECRET_ACCESS_KEY': 'test-only'}

    def test_r2_requires_https_endpoint(self):
        env = self.r2_environment()
        env['R2_ENDPOINT_URL'] = 'http://test-account.r2.cloudflarestorage.com'
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                media_storage_config()

    def test_private_signed_r2_upload_read_delete_contract(self):
        with patch.dict(os.environ, self.r2_environment(), clear=True):
            storage = S3Storage(**media_storage_config()['OPTIONS'])
            client = storage.connection.meta.client
            data = b'cloud-media-check'
            with Stubber(client) as stub:
                stub.add_client_error('head_object', service_error_code='404', http_status_code=404, expected_params={'Bucket':'test-only','Key':'video-tales/probe.txt'})
                stub.add_response('put_object', {}, {'Bucket':'test-only','Key':'video-tales/probe.txt','Body':ANY,'ContentType':'text/plain'})
                name = storage.save('probe.txt', ContentFile(data))
                url = storage.url(name)
                self.assertTrue(url.startswith('https://test-account.r2.cloudflarestorage.com/'))
                self.assertIn('X-Amz-Signature=', url)
                self.assertIn('X-Amz-Expires=3600', url)
                stub.add_response('head_object', {'ContentLength':len(data)}, {'Bucket':'test-only','Key':'video-tales/probe.txt'})
                stub.add_response('get_object', {'Body':StreamingBody(io.BytesIO(data), len(data)), 'ContentLength':len(data)}, {'Bucket':'test-only','Key':'video-tales/probe.txt','Range':ANY})
                with storage.open(name, 'rb') as file:
                    self.assertEqual(file.read(), data)
                stub.add_response('delete_object', {}, {'Bucket':'test-only','Key':'video-tales/probe.txt'})
                storage.delete(name)
                stub.assert_no_pending_responses()

class CloudReadinessTests(TestCase):
    def test_database_readiness_command(self):
        from django.core.management import call_command
        output=io.StringIO()
        call_command('check_cloud', stdout=output)
        self.assertIn('checks passed', output.getvalue())

    def test_storage_error_does_not_reveal_keys(self):
        from django.core.management import call_command, CommandError
        from django.test import override_settings
        with override_settings(STORAGES={'default': {'BACKEND':'storages.backends.s3.S3Storage'}, 'staticfiles': {'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}), patch('videos.management.commands.check_cloud.default_storage') as storage:
            storage.save.side_effect = RuntimeError('private-test-token')
            with self.assertRaises(CommandError) as error:
                call_command('check_cloud')
            self.assertNotIn('private-test-token', str(error.exception))
