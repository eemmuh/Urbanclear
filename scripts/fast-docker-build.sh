#!/bin/bash
# Fast Docker Build Script

set -e

echo " Starting optimized Docker build..."

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1

# Method 1: Minimal build (fastest)
echo "Building minimal version..."
time docker build -f Dockerfile.minimal -t traffic-system:minimal . \
  --progress=plain

# Method 2: Cached build with core deps
echo "Building with dependency caching..."
time docker build -f Dockerfile.fast -t traffic-system:fast . \
  --progress=plain

echo " Fast builds completed!"

# Test the builds
echo " Testing builds..."
docker run --rm traffic-system:minimal python -c "import src.api.main; print(' Minimal build works!')"
docker run --rm traffic-system:fast python -c "import src.api.main; print(' Fast build works!')"

echo " All builds successful!"
echo ""
echo "Available images:"
docker images | grep traffic-system 