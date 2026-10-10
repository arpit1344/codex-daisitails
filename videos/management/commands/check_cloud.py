"""Check configured database and private media storage without disclosing secrets."""
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = 'Verify database connectivity and a temporary storage write/read/delete cycle.'

    def handle(self, *args, **options):
        stored_name = None
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                if cursor.fetchone()[0] != 1:
                    raise RuntimeError('Unexpected database response')
            if settings.STORAGES['default']['BACKEND'] != 'django.core.files.storage.FileSystemStorage':
                stored_name = default_storage.save(f'healthchecks/{uuid.uuid4().hex}.txt', ContentFile(b'video-tales-storage-check'))
                with default_storage.open(stored_name, 'rb') as file:
                    if file.read() != b'video-tales-storage-check':
                        raise RuntimeError('Storage integrity check failed')
                default_storage.delete(stored_name)
                stored_name = None
        except Exception:
            if stored_name:
                try:
                    default_storage.delete(stored_name)
                except Exception:
                    pass
            raise CommandError('Cloud connectivity check failed. Verify database access/TLS and Neon bucket permissions in hosting settings.') from None
        self.stdout.write(self.style.SUCCESS('Database and configured media storage checks passed.'))
