#!/bin/bash
set -e

echo "🐳 MEDLEY Quick Production Build"
echo "================================"

# Stop existing
docker stop medley-app 2>/dev/null || true
docker rm medley-app 2>/dev/null || true

# Build
echo "Building image..."
VERSION=$(date +%Y%m%d-%H%M%S)
docker build --build-arg BUILD_VERSION="prod-$VERSION" -t medley:$VERSION -t medley:latest .

# Run
echo "Starting container..."
docker run -d \
  --name medley-app \
  -p 5000:5000 \
  --dns=8.8.8.8 --dns=1.1.1.1 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/usecases:/app/usecases \
  medley:latest

echo ""
echo "✅ MEDLEY is running!"
echo "🌐 Access: http://localhost:5000"
echo "📋 Logs:   docker logs -f medley-app"
echo "🛑 Stop:   docker stop medley-app"
echo ""

# Quick health check
sleep 3
echo "Testing connection..."