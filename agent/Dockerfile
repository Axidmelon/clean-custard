# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set metadata labels
LABEL maintainer="Custard Agent Team"
LABEL description="Custard Agent - Database Schema Discovery and Query Service"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2 and other requirements
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd -m -u 1000 custard

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Copy application code
COPY . .

# Set proper ownership
RUN chown -R custard:custard /app

# Switch to non-root user
USER custard

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random

# Create logs directory
RUN mkdir -p /app/logs

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; import websockets; import psycopg2; print('Agent is healthy')" || exit 1

# Use exec form for better signal handling
CMD ["python", "main.py"]
