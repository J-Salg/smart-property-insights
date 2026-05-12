#!/bin/bash
set -e

echo "[startup] Applying database migrations..."
flask db upgrade

echo "[startup] Starting Gunicorn (1 worker, 120s timeout)..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    run:app
