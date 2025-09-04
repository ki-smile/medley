#!/bin/bash

# Build script for MEDLEY Docker image with versioning

# Set version (increment this for each build)
VERSION="1.0.0-fixed-$(date +%Y%m%d-%H%M%S)"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

echo "================================"
echo "Building MEDLEY Docker Image"
echo "Version: $VERSION"
echo "Date: $BUILD_DATE"
echo "================================"

# Build the Docker image with build arguments
docker build \
    --build-arg BUILD_VERSION="$VERSION" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    -f deployment/Dockerfile.fixed \
    -t ghcr.io/ki-smile/medley:latest \
    -t ghcr.io/ki-smile/medley:$VERSION \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "To run the container:"
    echo "docker run -d --name medley-container -p 5000:5000 ghcr.io/ki-smile/medley:latest"
    echo ""
    echo "To check the version:"
    echo "docker run --rm ghcr.io/ki-smile/medley:latest sh -c 'cat /app/version.txt'"
else
    echo "❌ Build failed!"
    exit 1
fi