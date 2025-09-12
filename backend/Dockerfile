# Production Dockerfile for Custard Backend
# Optimized for Railway deployment with automatic SSL and reverse proxy
FROM python:3.13-slim

# Set metadata labels
LABEL maintainer="Custard Backend Team"
LABEL description="Custard Backend - AI Data Agent Platform"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONHASHSEED=random \
    ENVIRONMENT=production \
    DEBUG=false \
    ENABLE_DOCS=false \
    LOG_LEVEL=INFO \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user with specific UID/GID for security
RUN groupadd -r custard -g 1000 && \
    useradd -r -g custard -u 1000 -d /app -s /bin/bash custard

# Set work directory
WORKDIR /app

# Install system dependencies in a single layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with production optimizations
RUN pip install --no-cache-dir --upgrade pip==24.0.0 setuptools==69.0.0 wheel==0.42.0 && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy application code
COPY . .

# Create logs directory and set proper permissions
RUN mkdir -p /app/logs && \
    chown -R custard:custard /app && \
    chmod -R 755 /app && \
    chmod 755 /app/logs

# Switch to non-root user
USER custard

# Expose port
EXPOSE 8000

# Health check for production with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/ready || exit 1

# Start command with production optimizations
# Railway will use the PORT environment variable
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class uvicorn.workers.UvicornWorker --access-logfile - --log-level info --timeout 30 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --worker-connections 1000 --preload"]
