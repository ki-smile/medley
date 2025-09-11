# ============================================================================
# MEDLEY - Production Docker Image (2025)
# Medical AI Ensemble Application 
# SMAILE @ Karolinska Institutet
# ============================================================================

FROM python:3.11-slim

# Build metadata
ARG BUILD_VERSION="prod-$(date +%Y%m%d_%H%M%S)"
LABEL maintainer="SMAILE @ Karolinska Institutet"
LABEL version=${BUILD_VERSION}
LABEL description="Medley Medical AI Ensemble Application"

# Environment setup for production
ENV MEDLEY_VERSION=${BUILD_VERSION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
    USE_FREE_MODELS=true \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies including cron for cleanup jobs
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    wget \
    ca-certificates \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Create non-root user for security and setup cron
RUN groupadd -r medley && \
    useradd -r -g medley -d /app -s /bin/bash medley && \
    mkdir -p /app/logs /app/reports /app/cache/responses /app/cache/orchestrator /app/flask_session /var/log && \
    chown -R medley:medley /app && \
    chmod 666 /var/log && \
    touch /var/log/cron.log && \
    chmod 666 /var/log/cron.log

# Copy and install Python dependencies (leverage Docker layer caching)
COPY requirements.txt requirements_web_minimal.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_web_minimal.txt

# Copy application code
COPY --chown=medley:medley . .

# Set proper permissions
RUN chmod -R 755 /app && \
    chmod +x /app/web_app.py && \
    chmod +x /app/scripts/cleanup_custom_cases.sh && \
    chmod +x /app/scripts/setup_cron.sh && \
    chmod +x /app/scripts/cleanup_daemon.py && \
    chmod +x /app/scripts/docker-entrypoint.sh && \
    chmod -R 755 /app/cache /app/reports /app/flask_session && \
    chown -R medley:medley /app/cache /app/reports /app/flask_session

# Switch to non-root user
USER medley

# Expose port
EXPOSE 5000

# Health check with improved DNS resolution
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Production startup with entrypoint script (includes cleanup daemon)
CMD ["/app/scripts/docker-entrypoint.sh"]