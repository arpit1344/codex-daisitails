# Django Video Library

A Django video website with a staff-only content management panel. The general-purpose layout uses a white theme, blue navigation, a category sidebar and a three-column video grid, with a responsive mobile layout and persistent dark-mode toggle.

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

In admin, create categories and upload videos with optional thumbnails, descriptions and durations. Videos are private drafts until **is published** is selected. Set **is featured** to promote a video in featured sorting. Optional quality badges support HD, 2K and 4K. Admin editors assign an editorial score (0–100); it is not a user vote. Top rated sorting uses this score. Most viewed sorting uses video detail page GET visits, including repeat visits; it does not measure completed playback or unique viewers. Search, category filtering and pagination work on published videos.

Supported upload extensions: MP4, WebM and OGV. For broad browser compatibility, upload MP4 encoded with H.264 video and AAC audio. There is no automatic transcoding or thumbnail generation. File extension validation does not inspect codecs or file content; upload access is restricted to trusted staff.

## Validation

```sh
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

Tests cover admin uploads and login restrictions, unsupported extensions, draft privacy, search/category filters, detail player markup, pagination, sorting, rating limits, category counts and view counting. Upload tests use synthetic bytes and do not prove browser codec playback.

## Deployment

This is a development setup, not a deployed production site. Set `DJANGO_DEBUG=0`, a private `DJANGO_SECRET_KEY`, and comma-separated `DJANGO_ALLOWED_HOSTS`. Use a production WSGI server, HTTPS, configured static/media serving and persistent storage with backups. Run `collectstatic` and deployment security checks. Large uploads need server limits and preferably object storage; they currently use Django's local media storage. Do not expose Django's development server as a production service.

## Continue on another computer

Commit and push source changes, then pull the same branch on the other machine. The virtual environment, SQLite database and uploaded media are ignored by Git. Use backups or shared storage to transfer admin users, records and videos. Never commit passwords, databases or uploaded private content.

## Demo collection and local admin

Run `.venv/bin/python manage.py seed_demo` to create six clearly labelled demo videos with original illustrated thumbnails and a playable three-second test-pattern clip. This optional command requires `ffmpeg` and skips existing demo slugs. The demo collection is for preview; replace it with your own media in admin. It does not change existing content.

A local admin account was created during development. Its generated password is in the ignored `.admin-credentials.txt` file; change it after first login. Credentials, media and SQLite records are not pushed to GitHub. On a new machine create your own account with `createsuperuser`.
