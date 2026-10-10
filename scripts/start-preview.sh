#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python manage.py migrate --noinput
python manage.py bootstrap_admin
python manage.py seed_demo
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 2 --timeout 120 --no-control-socket
