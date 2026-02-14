FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
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
    && chmod 750 instance logs backups \
    && chmod 755 static/uploads static/uploads/perfiles static/uploads/firmas horarios

# Expose the port the app runs on
EXPOSE 5001

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Volume mount points - ensure correct ownership at runtime
VOLUME ["/app/instance", "/app/logs", "/app/backups", "/app/static/uploads", "/app/horarios"]

# Run the entrypoint script
CMD ["./entrypoint.sh"]
