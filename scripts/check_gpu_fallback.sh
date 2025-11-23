#!/bin/bash
# Check for GPU fallback patterns in rag-api logs
# Exit 1 if fallback detected, 0 otherwise

set -euo pipefail

# Check if rag-api container exists
if ! docker compose ps rag-api 2>/dev/null | grep -q rag-api; then
    echo "[CI] ⚠️  rag-api container not running, skipping GPU fallback check"
    exit 0
fi

# Check if docker compose is available
if ! command -v docker >/dev/null 2>&1; then
    echo "[CI] ⚠️  docker not available, skipping GPU fallback check"
    exit 0
fi

# Get recent rag-api logs (last 300 lines)
LOGS=$(docker compose logs --tail 300 rag-api 2>/dev/null || echo "")

# Patterns that indicate GPU fallback
FALLBACK_PATTERNS=(
    "GPU worker not ready, but continuing"
    "GPU worker client disabled"
    "falling back to CPU"
    "CPU fallback"
)

FOUND_FALLBACK=false
for pattern in "${FALLBACK_PATTERNS[@]}"; do
    if echo "$LOGS" | grep -qi "$pattern"; then
        echo "[CI] ❌ GPU fallback detected: '$pattern'"
        FOUND_FALLBACK=true
    fi
done

if [ "$FOUND_FALLBACK" = "true" ]; then
    echo "[CI] ❌ CI silently fell back to CPU. Fix GPU connectivity before continuing."
    echo "[CI] Check: docker compose logs rag-api | grep -i 'gpu\|worker'"
    exit 1
fi

echo "[CI] ✅ No GPU fallback detected in recent rag-api logs."
exit 0

