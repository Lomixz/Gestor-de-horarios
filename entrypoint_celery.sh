#!/bin/bash
set -e

echo "Fixing volume permissions for Celery worker..."
chown -R appuser:appuser /app/instance /app/logs /app/backups /app/static/uploads /app/horarios 2>/dev/null || true

echo "Starting Celery worker as appuser..."
exec gosu appuser celery -A celery_app worker --loglevel=info --concurrency=2
