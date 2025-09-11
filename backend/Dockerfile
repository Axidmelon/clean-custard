# Production Dockerfile for Custard Backend
# Optimized for Railway deployment with automatic SSL and reverse proxy
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production \
    DEBUG=false \
    ENABLE_DOCS=false \
    LOG_LEVEL=INFO

# Create non-root user
RUN groupadd -r custard && useradd -r -g custard custard

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with production optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Copy application code
COPY . .

# Create logs directory and set permissions
RUN mkdir -p /app/logs && \
    chown -R custard:custard /app && \
    chmod -R 755 /app

# Switch to non-root user
USER custard

# Expose port
EXPOSE 8000

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start command with production optimizations
# Railway will use the PORT environment variable
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class uvicorn.workers.UvicornWorker --access-logfile - --log-level info --timeout-keep-alive 5 --limit-max-requests 1000 --limit-concurrency 1000"]
