#!/bin/bash
set -e

echo "🐳 MEDLEY Production Docker Setup"
echo "================================="

# Stop and remove existing container
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true
docker stop medley-app 2>/dev/null || true
docker rm medley-app 2>/dev/null || true

# Build and run
echo "Building and starting MEDLEY..."
BUILD_VERSION=$(date +%Y%m%d-%H%M%S) docker-compose up --build -d

# Show status
echo ""
echo "✅ MEDLEY is running!"
echo ""
echo "🌐 Access: http://localhost:5000"
echo "📊 Logs:   docker-compose logs -f"
echo "🛑 Stop:   docker-compose down"
echo ""

# Wait for health check
echo "Waiting for health check..."
sleep 5
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check pending... Check logs with: docker-compose logs"
fi