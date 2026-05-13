#!/bin/bash
set -e

echo "[startup] Downloading 3D models from S3 (if needed)..."
python scripts/ensure_models.py

echo "[startup] Applying database migrations..."
flask db upgrade

echo "[startup] Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    run:app
