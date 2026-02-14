#!/bin/bash
set -e

# Generate .env with defaults if it doesn't exist
if [ ! -f .env ]; then
    echo "Generating .env with secure defaults..."
    SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
    cat > .env <<EOF
SECRET_KEY=${SECRET}
DATABASE_URL=sqlite:///sistema_academico.db
FLASK_DEBUG=0
BACKUP_ENCRYPTION_KEY=
EOF
    echo ".env created successfully."
fi

# Create necessary directories with proper permissions
echo "Ensuring directories exist..."
mkdir -p instance logs static/uploads/perfiles static/uploads/firmas backups horarios

# Initialize configuration and database tables
echo "Running system initialization..."
python init_config.py

# Run pending migrations automatically
echo "Running migrations..."
python migrate_remove_password_temporal.py || echo "Migration skipped or already applied."

echo "Starting Gunicorn server on port 5001..."
# using 4 workers, customize as needed
exec gunicorn --bind 0.0.0.0:5001 --timeout 600 app:app
