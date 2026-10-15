import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from videos.importer import process_next
from videos.models import VideoImport


class Command(BaseCommand):
    help = 'Process durable video import jobs. Run with --once for a single queue pass.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            VideoImport.objects.filter(status='processing', started_at__lt=timezone.now() - timedelta(hours=1)).update(status='failed', error='Worker stopped during import. Retry this job from admin.', finished_at=timezone.now())
            processed = process_next()
            if options['once']:
                return
            if not processed:
                time.sleep(5)
