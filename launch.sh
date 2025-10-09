#!/bin/sh
# Minimal FIQA API Launcher - POSIX-compatible
set -e

echo "🚀 SearchForge FIQA API Launcher"
echo "=================================="

# Export stable environment defaults (can be overridden externally)
export RATE_LIMIT_MAX="${RATE_LIMIT_MAX:-3}"
export RATE_LIMIT_WINDOW_SEC="${RATE_LIMIT_WINDOW_SEC:-1.0}"
export API_VERSION="${API_VERSION:-v1.0.0-fiqa}"
export DISABLE_AUTOTUNER="${DISABLE_AUTOTUNER:-1}"

# Legacy flags for backward compatibility
export DISABLE_TUNER=0 USE_QDRANT=1

# Check if docker is available
if command -v docker >/dev/null 2>&1; then
    echo "✓ Docker detected - starting Qdrant..."
    docker-compose up -d qdrant 2>/dev/null || echo "⚠ Qdrant already running"
    sleep 2
else
    echo "⚠ Docker not found - using mock vectorstore"
    export USE_QDRANT=0
fi

# Start FastAPI server in background
echo "✓ Starting FastAPI server on port 8080..."
cd services/fiqa_api && uvicorn app:app --host 0.0.0.0 --port 8080 --reload &
API_PID=$!
cd - >/dev/null
sleep 3

# Health check loop
echo "✓ Monitoring health status (Ctrl+C to stop)..."
trap "echo '\n🛑 Shutting down...'; kill $API_PID 2>/dev/null; exit" INT TERM

while true; do
    STATUS=$(curl -s http://localhost:8080/health 2>/dev/null || echo '{"status":"down"}')
    echo "[$(date +%T)] Health: $STATUS"
    sleep 5
done

