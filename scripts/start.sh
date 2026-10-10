#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python manage.py check_cloud
python manage.py migrate --noinput
python manage.py bootstrap_admin
if [ "${SEED_DEMO:-0}" = "1" ]; then python manage.py seed_demo; fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 2 --timeout 120 --no-control-socket
