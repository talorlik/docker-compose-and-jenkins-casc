#!/bin/bash

# Script to build Jenkins image for multiple architectures
# Supports both ARM64 and AMD64

set -e

echo "Building Jenkins image for multiple architectures..."

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo "Error: Docker Buildx is not available. Please install Docker Desktop or update Docker Engine."
    exit 1
fi

# Create or use existing builder
if ! docker buildx inspect multiarch &> /dev/null; then
    echo "Creating new buildx builder: multiarch"
    docker buildx create --name multiarch --use
else
    echo "Using existing buildx builder: multiarch"
    docker buildx use multiarch
fi

# Bootstrap the builder
docker buildx inspect --bootstrap

# Build for multiple platforms
echo "Building for linux/amd64 and linux/arm64..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t jenkins-casc:latest \
    --load \
    .

echo "Build complete! You can now start Jenkins with: docker-compose up -d"
