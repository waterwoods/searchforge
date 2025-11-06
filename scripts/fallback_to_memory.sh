#!/bin/bash
# fallback_to_memory.sh - One-click fallback to Memory metrics backend
# Usage: ./scripts/fallback_to_memory.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_ROOT"

echo "=================================================="
echo "🔄 Switching to Memory Metrics Backend"
echo "=================================================="
echo ""

# Step 1: Update environment
echo "[1/3] Configuring environment..."

ENV_FILE="$WORKSPACE_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    # Backup existing .env
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"
    # Remove Redis-related config
    grep -v "^CORE_METRICS_BACKEND=" "$ENV_FILE" | \
    grep -v "^REDIS_HOST=" | \
    grep -v "^REDIS_PORT=" | \
    grep -v "^REDIS_DB=" | \
    grep -v "^REDIS_METRICS_PREFIX=" | \
    grep -v "^REDIS_METRICS_TTL=" > "$ENV_FILE.tmp" || true
    mv "$ENV_FILE.tmp" "$ENV_FILE"
fi

# Set Memory backend
echo "CORE_METRICS_BACKEND=memory" >> "$ENV_FILE"

echo "   ✅ Environment configured (.env updated)"
echo "      - CORE_METRICS_BACKEND=memory"

# Step 2: Restart uvicorn
echo ""
echo "[2/3] Restarting uvicorn..."

# Kill existing uvicorn processes for app_v2
pkill -f "uvicorn services.fiqa_api" || true
sleep 1

# Export environment variables and start uvicorn in background
cd "$WORKSPACE_ROOT/services/fiqa_api"
export CORE_METRICS_BACKEND=memory
unset REDIS_HOST REDIS_PORT REDIS_DB REDIS_METRICS_PREFIX REDIS_METRICS_TTL

nohup uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8080 > /dev/null 2>&1 &
UVICORN_PID=$!

echo "   ✅ Uvicorn started (PID: $UVICORN_PID)"
sleep 3

# Step 3: Self-check
echo ""
echo "[3/3] Running self-check..."

MAX_RETRIES=10
RETRY_COUNT=0
HEALTH_OK=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080/admin/health > /dev/null 2>&1; then
        HEALTH_RESPONSE=$(curl -s http://localhost:8080/admin/health)
        BACKEND=$(echo "$HEALTH_RESPONSE" | grep -o '"core_metrics_backend":"[^"]*"' | cut -d'"' -f4)
        REDIS_CONNECTED=$(echo "$HEALTH_RESPONSE" | grep -o '"redis_connected":[^,}]*' | cut -d':' -f2)
        ROWS=$(echo "$HEALTH_RESPONSE" | grep -o '"rows_60s":[0-9]*' | cut -d':' -f2)
        
        if [ "$BACKEND" = "memory" ] && [ "$REDIS_CONNECTED" = "false" ]; then
            HEALTH_OK=true
            break
        fi
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ "$HEALTH_OK" = true ]; then
    echo "   ✅ Health check passed"
    echo "      - Backend: $BACKEND"
    echo "      - Redis Connected: $REDIS_CONNECTED"
    echo "      - Rows in 60s window: $ROWS"
    echo ""
    echo "=================================================="
    echo "✅ PASS - Memory backend active"
    echo "=================================================="
    echo ""
    echo "💡 Next steps:"
    echo "   - Check status: ./scripts/check_metrics_backend.sh"
    echo "   - View metrics: curl localhost:8080/metrics/window60s | jq"
    echo "   - Switch back: ./scripts/switch_to_redis.sh"
    exit 0
else
    echo "   ❌ Health check failed after $MAX_RETRIES retries"
    echo "   Backend: ${BACKEND:-unknown}"
    echo "   Redis Connected: ${REDIS_CONNECTED:-false}"
    echo ""
    echo "=================================================="
    echo "❌ FAIL - Check logs for details"
    echo "=================================================="
    exit 1
fi
