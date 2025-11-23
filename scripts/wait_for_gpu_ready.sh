#!/bin/bash
# Wait for GPU worker to be ready
# Polls http://gpu-worker:8090/ready until it returns 200 or timeout

set -euo pipefail

# Detect if running from host or inside Docker network
# Try localhost first (host context), fallback to gpu-worker (container context)
if [ -z "${GPU_WORKER_URL:-}" ]; then
    if curl -sf --connect-timeout 1 "http://localhost:8090/ready" >/dev/null 2>&1; then
        GPU_WORKER_URL="http://localhost:8090"
    elif curl -sf --connect-timeout 1 "http://gpu-worker:8090/ready" >/dev/null 2>&1; then
        GPU_WORKER_URL="http://gpu-worker:8090"
    else
        # Default to localhost (most common case - running from host)
        GPU_WORKER_URL="http://localhost:8090"
    fi
fi

MAX_WAIT_SEC="${MAX_WAIT_SEC:-60}"
INTERVAL_SEC="${INTERVAL_SEC:-2}"

echo "Waiting for GPU worker at ${GPU_WORKER_URL}/ready..."
echo "Max wait time: ${MAX_WAIT_SEC}s, polling interval: ${INTERVAL_SEC}s"

elapsed=0
while [ $elapsed -lt $MAX_WAIT_SEC ]; do
    if curl -sf "${GPU_WORKER_URL}/ready" >/dev/null 2>&1; then
        echo "✅ GPU worker is ready"
        exit 0
    fi
    echo "⏳ GPU worker not ready yet (${elapsed}s/${MAX_WAIT_SEC}s)..."
    sleep $INTERVAL_SEC
    elapsed=$((elapsed + INTERVAL_SEC))
done

echo "❌ GPU worker did not become ready within ${MAX_WAIT_SEC}s"
echo "   Check GPU worker logs: docker compose logs gpu-worker"
echo "   Or check health: curl ${GPU_WORKER_URL}/healthz"
exit 1

