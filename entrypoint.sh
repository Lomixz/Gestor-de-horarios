#!/bin/bash
set -e

# Fix ownership of mounted volumes (runs as root)
echo "Fixing volume permissions..."
chown -R appuser:appuser /app/instance /app/logs /app/backups /app/static/uploads /app/horarios 2>/dev/null || true

# Create necessary directories as appuser
gosu appuser mkdir -p instance logs static/uploads/perfiles static/uploads/firmas backups horarios

# Initialize configuration and database tables
echo "Running system initialization..."
gosu appuser python init_config.py

# Run pending migrations automatically
echo "Running migrations..."
gosu appuser python migrate_remove_password_temporal.py || echo "Migration skipped or already applied."

echo "Starting Gunicorn server on port 5001..."
# Drop privileges to appuser and start gunicorn
exec gosu appuser gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 600 app:app
