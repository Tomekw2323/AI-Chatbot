#!/bin/sh
# Public free demo only. Production keeps the image CMD (gunicorn + Postgres).
# One worker: the free instance has 512 MB, and SQLite does not like concurrent writers.
set -eu
python manage.py prepare_demo
exec gunicorn config.wsgi --bind "0.0.0.0:${PORT:-8000}" --workers 1 --access-logfile -
