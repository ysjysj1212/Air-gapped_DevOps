#!/bin/bash
# Docker Build and Test Script for CI/CD Pipeline Generator

echo "=== Docker Build & Test Script ==="

# Check if Docker is running
echo "Checking Docker daemon..."
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Docker daemon is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✓ Docker daemon is running"

# Build image
echo ""
echo "Building Docker image: ci-pipeline-generator:1.0"
docker build -t ci-pipeline-generator:1.0 -f Dockerfile .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "✓ Docker image built successfully"

# List images
echo ""
echo "Docker images:"
docker images | grep ci-pipeline-generator

# Test run container
echo ""
echo "Starting test container..."
CONTAINER_ID=$(docker run -d -p 5000:5000 ci-pipeline-generator:1.0)

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start container"
    exit 1
fi

echo "✓ Container started: $CONTAINER_ID"

# Wait for app to be ready
echo "Waiting for app to start..."
sleep 5

# Test health endpoint
echo ""
echo "Testing health endpoint..."
HEALTH=$(curl -s http://localhost:5000/health)
echo "Response: $HEALTH"

if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ Health check passed"
else
    echo "ERROR: Health check failed"
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# Test API endpoint
echo ""
echo "Testing API endpoint..."
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "build, test, deploy",
    "language": "python",
    "ci_type": "github_actions"
  }'

echo ""
echo "✓ API test completed"

# Cleanup
echo ""
echo "Cleaning up test container..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "✓ Docker build and test completed successfully"
