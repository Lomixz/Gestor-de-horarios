#!/bin/bash
set -e

# Fix ownership of mounted volumes (runs as root)
echo "Fixing volume permissions..."
chown -R appuser:appuser /app/instance /app/logs /app/backups /app/static/uploads /app/horarios 2>/dev/null || true

# Create necessary directories as appuser
gosu appuser mkdir -p instance logs static/uploads/perfiles static/uploads/firmas backups horarios

# Run database migrations (Alembic via Flask-Migrate)
echo "Running database migrations..."
gosu appuser flask db upgrade || echo "Migrations: already up to date or no migrations found"

# Initialize configuration and default data (idempotent, non-fatal)
echo "Running system initialization..."
gosu appuser python init_config.py || echo "init_config: already initialized or non-fatal error, continuing..."

echo "Starting Gunicorn server on port 5001..."
# Drop privileges to appuser and start gunicorn
exec gosu appuser gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 600 --access-logfile - --error-logfile - --log-level info app:app
