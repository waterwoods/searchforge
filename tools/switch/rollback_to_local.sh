#!/usr/bin/env bash
# Rollback to local SearchForge target

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

PROJECT=${PROJECT:-searchforge}

echo "=================================================="
echo "🔄 Rolling back to Local Target"
echo "=================================================="
echo ""

# Step 1: Copy .env.local -> .env.current
echo "[1/3] Setting up .env.current from local template..."
if [ ! -f ".env.local" ]; then
    echo "❌ Error: .env.local not found"
    exit 1
fi
cp .env.local .env.current
echo "✅ .env.current created from .env.local"
echo ""

# Step 2: Start local services
echo "[2/3] Starting local services..."
docker compose --env-file .env.current -p "$PROJECT" up -d
echo "✅ Local services started"
echo ""

# Step 3: Health check
echo "[3/3] Performing health check..."
MAX_RETRIES=30
RETRY_COUNT=0
HEALTH_OK=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
        HEALTH_OK=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ "$HEALTH_OK" = true ]; then
    echo "✅ Health check passed: http://localhost:8000/health"
    curl -fsS http://localhost:8000/health | head -c 200 && echo ""
else
    echo "❌ Error: Health check failed after $MAX_RETRIES retries"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Rollback to local complete!"
echo "=================================================="
