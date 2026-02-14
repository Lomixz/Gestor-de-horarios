FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Install gunicorn for production serving
RUN pip install --no-cache-dir gunicorn

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy the rest of the application
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p instance logs static/uploads/perfiles backups static/uploads/firmas horarios \
    && chown -R appuser:appuser /app \
    && chmod +x entrypoint.sh

# Expose the port the app runs on
EXPOSE 5001

# Volume mount points
VOLUME ["/app/instance", "/app/logs", "/app/backups", "/app/static/uploads", "/app/horarios"]

# Run the entrypoint script as root (it will fix permissions then drop to appuser)
CMD ["./entrypoint.sh"]
