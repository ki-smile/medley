# Multi-stage Docker build for MEDLEY Web Application
# Stage 1: Base image with Python
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 3: Application
FROM dependencies as application

# Create non-root user
RUN groupadd -r medley && \
    useradd -r -g medley -d /app -s /bin/bash medley

# Copy application code
COPY --chown=medley:medley . .

# Create necessary directories
RUN mkdir -p /app/cache/responses \
             /app/reports \
             /app/usecases \
             /app/logs \
             /app/static/css \
             /app/static/js \
             /app/templates/components && \
    chown -R medley:medley /app

# Switch to non-root user
USER medley

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["python", "web_app.py"]

# Stage 4: Production with Gunicorn
FROM application as production

# Install production server
USER root
RUN pip install gunicorn gevent

USER medley

# Production command with Gunicorn
CMD ["gunicorn", "--worker-class", "gevent", \
     "--workers", "4", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "120", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "web_app:app"]