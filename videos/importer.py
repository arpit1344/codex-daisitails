"""Bounded downloads from explicitly trusted source domains; imports stay drafts."""
import ipaddress
import os
import socket
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from .models import Video, VideoImport


def validate_source(url):
    parsed = urlsplit(url)
    allowed = {h.strip().lower() for h in os.environ.get('VIDEO_IMPORT_ALLOWED_HOSTS', '').split(',') if h.strip()}
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValidationError('Use an HTTPS URL without embedded credentials or a custom port.')
    if not parsed.hostname or parsed.hostname.lower() not in allowed:
        raise ValidationError('Source domain is not enabled. Add its exact hostname to VIDEO_IMPORT_ALLOWED_HOSTS in Render settings.')
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except OSError:
        raise ValidationError('Source domain could not be resolved.')
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValidationError('Source must resolve to a public Internet address.')
    extension = Path(parsed.path).suffix.lower()
    if extension not in {'.mp4', '.webm', '.ogv'}:
        raise ValidationError('Use a direct MP4, WebM or OGV URL, rather than a webpage.')
    return extension


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirects are not supported. Use the final direct media URL.')


def process_next():
    job = VideoImport.objects.filter(status='queued').order_by('pk').first()
    if not job or not VideoImport.objects.filter(pk=job.pk, status='queued').update(status='processing', started_at=timezone.now()):
        return False
    saved_video = None
    try:
        if not job.rights_confirmed:
            raise ValueError('Confirm ownership or licensing before importing.')
        extension = validate_source(job.source_url)
        limit = int(os.environ.get('VIDEO_IMPORT_MAX_BYTES', 250 * 1024 * 1024))
        request = Request(job.source_url, headers={'User-Agent': 'VideoTalesImporter/1.0', 'Accept-Encoding': 'identity'})
        with build_opener(NoRedirect).open(request, timeout=30) as response, tempfile.TemporaryFile() as output:
            if response.headers.get_content_type() not in {'video/mp4', 'video/webm', 'video/ogg', 'application/octet-stream'}:
                raise ValueError('Source did not return a supported video content type.')
            if int(response.headers.get('Content-Length', 0)) > limit:
                raise ValueError('Video exceeds the configured import size limit.')
            size = 0
            deadline = time.monotonic() + 600
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit or time.monotonic() > deadline:
                    raise ValueError('Import size or time limit exceeded.')
                output.write(chunk)
            output.seek(0)
            header = output.read(64)
            valid = (extension == '.mp4' and header[4:8] == b'ftyp') or (extension == '.webm' and header.startswith(b'\x1aE\xdf\xa3')) or (extension == '.ogv' and header.startswith(b'OggS'))
            if not valid:
                raise ValueError('Downloaded file is not the expected video format.')
            output.seek(0)
            video = Video(title=job.title, slug=f'{slugify(job.title)[:170] or "video"}-{uuid.uuid4().hex[:12]}', description=job.description, category=job.category, is_published=False)
            video.file.save(f'import-{uuid.uuid4().hex}{extension}', File(output), save=False)
            saved_video = video
            if job.thumbnail:
                with job.thumbnail.open('rb') as thumbnail:
                    video.thumbnail.save(Path(job.thumbnail.name).name, File(thumbnail), save=False)
            video.save()
            video.tags.set(job.tags.all())
        job.video = video
        job.status = 'ready'
        job.error = ''
    except Exception as exc:
        if saved_video:
            saved_video.file.delete(save=False)
            if saved_video.thumbnail:
                saved_video.thumbnail.delete(save=False)
            if saved_video.pk:
                saved_video.delete()
        job.status = 'failed'
        job.error = exc.messages[0] if isinstance(exc, ValidationError) else 'Import failed. Check the direct URL, file format, size limit and source permissions, then retry.'
    job.finished_at = timezone.now()
    job.save(update_fields=['status', 'error', 'video', 'finished_at'])
    return True
