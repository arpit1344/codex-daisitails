# Django Video Library

## Import licensed videos

In Render environment settings, set `VIDEO_IMPORT_ALLOWED_HOSTS` to a comma-separated list of exact trusted media hostnames you control or are licensed to download from. It starts empty. In Django admin, open **Video imports**, add a direct HTTPS MP4/WebM/OGV URL, title, description, category, tags and optional thumbnail, then confirm rights. The background worker downloads up to 250 MB (override with `VIDEO_IMPORT_MAX_BYTES`), checks the container signature, and creates a private draft. Redirects and private network sources are rejected. Open **Edit draft, preview and publish** when status is ready. Add language, duration and SEO details, preview, then publish explicitly. Failed imports can be retried with the admin action. This imports direct files; webpage extraction and transcoding are not included.

Production starts the worker alongside the web process; on the free Render plan both pause while the service sleeps. Open the site to wake it. For local development run `python manage.py import_worker` alongside Django, or `python manage.py import_worker --once` to process one job.

A Django video website with a staff-only content management panel. The responsive catalog includes search, category/language/duration filters, latest/popular/top-rated sorting, pagination and a persistent dark-mode toggle.

## Local setup

```sh
cd /workspace/codex-daisitails
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

Public routes: `/videos/` and `/videos/<slug>/`. Administration: `/admin/`.

SEO endpoints: `/sitemap.xml` and `/robots.txt`. Public video pages include canonical URLs, Open Graph/Twitter preview metadata and Schema.org `VideoObject` JSON-LD. Filtered/search result URLs are marked `noindex,follow` to avoid duplicate search pages. Editors can override each video's search title and description in the admin panel.

In admin, create categories and upload videos with a language, optional thumbnail, description and duration. Videos are private drafts until **is published** is selected. Set **is featured** to promote a video in featured sorting. Optional quality badges support HD, 2K and 4K. Admin editors assign an editorial score (0–100); it is not a user vote. Top rated sorting uses this score. Most viewed sorting uses video detail page GET visits, including repeat visits; it does not measure completed playback or unique viewers. Filters and pagination only expose published videos.

Supported upload extensions: MP4, WebM and OGV. For broad browser compatibility, upload MP4 encoded with H.264 video and AAC audio. Uploaded thumbnails are resized within 1280×720 and compressed to WebP. Videos are not automatically transcoded and thumbnails are not extracted from video files. File extension validation does not inspect codecs or file content; upload access is restricted to trusted staff.

## Validation

```sh
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

Tests cover admin uploads and login restrictions, unsupported extensions, draft privacy, search/category filters, detail player markup, pagination, sorting, rating limits, category counts and view counting. Upload tests use synthetic bytes. The bundled MP4 demo playback was separately verified in Chromium, including the Render-style DEBUG=0 Gunicorn runtime.

## Deployment

This is a development setup, not a deployed production site. Set `DJANGO_DEBUG=0`, a private `DJANGO_SECRET_KEY`, and comma-separated `DJANGO_ALLOWED_HOSTS`. Use a production WSGI server, HTTPS, configured static/media serving and persistent storage with backups. Run `collectstatic` and deployment security checks. Cloud media uses R2 when configured; local development uses filesystem storage. Large uploads still pass through Django and need appropriate hosting limits. Do not expose Django's development server as a production service.

## Continue on another computer

Commit and push source changes, then pull the same branch on the other machine. The virtual environment, SQLite database and uploaded media are ignored by Git. Use backups or shared storage to transfer admin users, records and videos. Never commit passwords, databases or uploaded private content.

## Demo collection and local admin

Run `.venv/bin/python manage.py seed_demo` to create six clearly labelled demo videos with original illustrated thumbnails and a playable three-second test-pattern clip. This optional command uses a bundled demo clip and skips existing demo slugs. The demo collection is for preview; replace it with your own media in admin. It does not change existing content.

A local admin account was created during development. Its generated password is in the ignored `.admin-credentials.txt` file; change it after first login. Credentials, media and SQLite records are not pushed to GitHub. On a new machine create your own account with `createsuperuser`.

## Persistent hosting

The default Render Blueprint uses **Neon PostgreSQL** for records and **Neon Object Storage** for private videos/thumbnails. Render runs Django with Gunicorn and WhiteNoise. See [the complete account and deployment guide](docs/HOSTING.md).

Deploy entry: https://render.com/deploy?repo=https://github.com/arpit1344/codex-daisitails

Set `DATABASE_URL`, Neon’s `AWS_*` object-storage variables and a new admin password in Render's secure environment settings. Do not share credentials in chat. Persistent mode refuses to start if database/storage settings are missing. It verifies PostgreSQL TLS certificates and hostnames and uses expiring signed media URLs.

`bash scripts/start.sh` checks database connectivity and a temporary media write/read/delete before running migrations and bootstrapping the admin. Demo data is optional through `SEED_DEMO=1`; no local content is migrated automatically. `scripts/start-preview.sh` remains available for a disposable SQLite/local-media demo, with the limitations described in the hosting guide.

External accounts have not yet been created: live Neon/R2 access, persistent uploads across a Render restart and a public URL remain unverified. Local development still works with SQLite and filesystem storage when persistent mode is not selected.
