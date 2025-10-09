#!/bin/bash
# CPU stress test for Qdrant container
# Usage: ./cpu_stress_test.sh [duration_seconds]

DURATION=${1:-60}
CONTAINER_NAME="searchforge-qdrant-1"

echo "🔥 Starting CPU stress test on Qdrant container..."
echo "Container: $CONTAINER_NAME"
echo "Duration: ${DURATION}s"

# Check if container exists and is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

# Install stress-ng if not available
echo "📦 Installing stress-ng in container..."
docker exec $CONTAINER_NAME sh -c "
    if ! command -v stress-ng &> /dev/null; then
        apk add --no-cache stress-ng || {
            echo 'Failed to install stress-ng via apk, trying apt...'
            apt-get update && apt-get install -y stress-ng
        }
    fi
"

# Run stress test
echo "🚀 Running CPU stress test..."
docker exec $CONTAINER_NAME stress-ng --cpu 2 --timeout ${DURATION}s --metrics-brief

echo "✅ CPU stress test completed"
