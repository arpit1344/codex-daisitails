"""Persistent hosting configuration. Never log database URLs or storage keys."""
import os
import ssl
from pathlib import Path
from urllib.parse import urlsplit
import dj_database_url
from botocore.config import Config
from django.core.exceptions import ImproperlyConfigured

def database_config(base_dir, debug):
    url = os.environ.get('DATABASE_URL', '').strip()
    required = os.environ.get('DJANGO_PERSISTENT_MODE', '0') == '1'
    if not url:
        if required:
            raise ImproperlyConfigured('DATABASE_URL is required for persistent hosting.')
        return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': Path(os.environ.get('DJANGO_DATABASE_PATH', str(base_dir / 'db.sqlite3')))}
    try:
        config = dj_database_url.parse(url, conn_max_age=0, conn_health_checks=True)
    except Exception:
        raise ImproperlyConfigured('DATABASE_URL must be a valid PostgreSQL connection URL.') from None
    if config['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured('Cloud DATABASE_URL must use PostgreSQL.')
    # Neon uses a public CA. Verify both the certificate chain and hostname.
    ca_candidates = [ssl.get_default_verify_paths().cafile, '/etc/ssl/certs/ca-certificates.crt', '/etc/pki/tls/certs/ca-bundle.crt']
    ca_file = next((path for path in ca_candidates if path and Path(path).is_file()), None)
    if not ca_file:
        raise ImproperlyConfigured('A system CA bundle is required for PostgreSQL TLS.')
    config.setdefault('OPTIONS', {}).update(sslmode='verify-full', sslrootcert=ca_file, connect_timeout=10)
    config['DISABLE_SERVER_SIDE_CURSORS'] = True
    return config

def media_storage_config():
    required = os.environ.get('DJANGO_PERSISTENT_MODE', '0') == '1'
    names = ['R2_ENDPOINT_URL', 'R2_BUCKET_NAME', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY']
    present = [bool(os.environ.get(name)) for name in names]
    if not any(present) and not required:
        return {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
    if not all(present):
        raise ImproperlyConfigured('Set all four R2 storage variables: endpoint, bucket, access key and secret key.')
    endpoint = os.environ['R2_ENDPOINT_URL'].rstrip('/')
    try:
        parsed = urlsplit(endpoint)
        valid = (parsed.scheme == 'https' and parsed.hostname and parsed.hostname.endswith('.r2.cloudflarestorage.com') and not parsed.username and not parsed.password and not parsed.port and parsed.path in ('', '/') and not parsed.query and not parsed.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise ImproperlyConfigured('R2_ENDPOINT_URL must be the HTTPS S3 endpoint supplied by Cloudflare.')
    return {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': {
        'access_key': os.environ['R2_ACCESS_KEY_ID'],
        'secret_key': os.environ['R2_SECRET_ACCESS_KEY'],
        'bucket_name': os.environ['R2_BUCKET_NAME'],
        'endpoint_url': endpoint,
        'region_name': 'auto',
        'default_acl': None,
        'file_overwrite': False,
        'location': 'video-tales',
        'querystring_auth': True,
        'querystring_expire': 3600,
        'max_memory_size': 10 * 1024 * 1024,
        'client_config': Config(signature_version='s3v4', s3={'addressing_style': 'path'}, request_checksum_calculation='when_required', response_checksum_validation='when_required'),
    }}
