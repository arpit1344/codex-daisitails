#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python manage.py check_cloud
python manage.py migrate --noinput
python manage.py bootstrap_admin
if [ "${SEED_DEMO:-0}" = "1" ]; then python manage.py seed_demo; fi
python manage.py import_worker &
import_pid=$!
gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 2 --timeout 120 --no-control-socket &
web_pid=$!
trap 'kill "$import_pid" "$web_pid" 2>/dev/null || true' EXIT
trap 'exit 0' TERM INT
wait -n "$import_pid" "$web_pid"
