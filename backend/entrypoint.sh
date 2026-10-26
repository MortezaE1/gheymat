#!/bin/sh
# Applies migrations (which also syncs the asset catalog) before starting the web server.
set -e
python manage.py migrate --noinput
python manage.py update_prices || echo "Initial price fetch failed; Celery will retry."
exec "$@"
