#!/bin/bash

# Docker entrypoint script for Medley
# Starts cleanup daemon and the web application

echo "🚀 Starting Medley Docker Container..."

# Ensure log directory exists
mkdir -p /app/logs
touch /app/logs/cleanup_daemon.log

# Set default environment variables if not provided
export FLASK_ENV=${FLASK_ENV:-production}
export FLASK_DEBUG=${FLASK_DEBUG:-0}
export USE_FREE_MODELS=${USE_FREE_MODELS:-true}
export CLEANUP_DAYS=${CLEANUP_DAYS:-2}
export CLEANUP_INTERVAL_HOURS=${CLEANUP_INTERVAL_HOURS:-24}

echo "📋 Configuration:"
echo "   CLEANUP_DAYS: $CLEANUP_DAYS"
echo "   CLEANUP_INTERVAL_HOURS: $CLEANUP_INTERVAL_HOURS"

# Start cleanup daemon in background
echo "🧹 Starting cleanup daemon..."
python3 /app/scripts/cleanup_daemon.py &
CLEANUP_PID=$!
echo "✅ Cleanup daemon started with PID: $CLEANUP_PID"

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$CLEANUP_PID" ]; then
        kill $CLEANUP_PID 2>/dev/null || true
        echo "✅ Cleanup daemon stopped"
    fi
    exit 0
}

# Trap signals to cleanup background processes
trap cleanup SIGTERM SIGINT

# Start the web application with gunicorn
echo "🌐 Starting Medley Web Application..."
exec gunicorn \
    --bind "0.0.0.0:5000" \
    --workers 1 \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile "-" \
    --error-logfile "-" \
    --log-level info \
    web_app:app