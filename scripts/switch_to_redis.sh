#!/bin/bash
# switch_to_redis.sh - One-click switch to Redis metrics backend
# Usage: ./scripts/switch_to_redis.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_ROOT"

echo "=================================================="
echo "🔄 Switching to Redis Metrics Backend"
echo "=================================================="
echo ""

# Step 1: Check/Install Redis
echo "[1/5] Checking Redis installation..."
if ! command -v redis-server &> /dev/null; then
    echo "   ⚠️  Redis not found. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "   ❌ Homebrew not found. Please install Redis manually:"
        echo "      macOS: brew install redis"
        echo "      Linux: sudo apt-get install redis-server"
        exit 1
    fi
    brew install redis
    echo "   ✅ Redis installed"
else
    echo "   ✅ Redis already installed"
fi

# Step 2: Start Redis
echo ""
echo "[2/5] Starting Redis server..."

# Check if Redis is responding
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis already running and responding"
else
    # Try to start Redis in background
    echo "   Starting Redis..."
    redis-server --daemonize yes --port 6379 2>/dev/null || true
    sleep 2
    
    # Verify Redis is now responding
    if redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis started on port 6379"
    else
        echo "   ❌ Failed to start Redis"
        echo "   💡 Try manually: redis-server --daemonize yes"
        exit 1
    fi
fi

echo "   ✅ Redis connection verified"

# Step 3: Set environment variables
echo ""
echo "[3/5] Configuring environment..."

# Create or update .env file
ENV_FILE="$WORKSPACE_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    # Backup existing .env
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"
    # Remove old CORE_METRICS_BACKEND if present
    grep -v "^CORE_METRICS_BACKEND=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
    mv "$ENV_FILE.tmp" "$ENV_FILE"
fi

# Append Redis configuration
cat >> "$ENV_FILE" <<EOF
CORE_METRICS_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_METRICS_PREFIX=searchforge
REDIS_METRICS_TTL=120
EOF

echo "   ✅ Environment configured (.env updated)"
echo "      - CORE_METRICS_BACKEND=redis"
echo "      - REDIS_HOST=localhost:6379"

# Step 4: Restart uvicorn
echo ""
echo "[4/5] Restarting uvicorn..."

# Kill existing uvicorn processes for app_v2
pkill -f "uvicorn services.fiqa_api" || true
sleep 1

# Export environment variables and start uvicorn in background
cd "$WORKSPACE_ROOT/services/fiqa_api"
export CORE_METRICS_BACKEND=redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_METRICS_PREFIX=searchforge
export REDIS_METRICS_TTL=120

nohup uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8080 > /dev/null 2>&1 &
UVICORN_PID=$!

echo "   ✅ Uvicorn started (PID: $UVICORN_PID)"
sleep 3

# Step 5: Self-check
echo ""
echo "[5/5] Running self-check..."

MAX_RETRIES=10
RETRY_COUNT=0
HEALTH_OK=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080/admin/health > /dev/null 2>&1; then
        HEALTH_RESPONSE=$(curl -s http://localhost:8080/admin/health)
        BACKEND=$(echo "$HEALTH_RESPONSE" | grep -o '"core_metrics_backend":"[^"]*"' | cut -d'"' -f4)
        REDIS_CONNECTED=$(echo "$HEALTH_RESPONSE" | grep -o '"redis_connected":[^,}]*' | cut -d':' -f2)
        ROWS=$(echo "$HEALTH_RESPONSE" | grep -o '"rows_60s":[0-9]*' | cut -d':' -f2)
        
        if [ "$BACKEND" = "redis" ] && [ "$REDIS_CONNECTED" = "true" ]; then
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
    echo "✅ PASS - Redis backend active"
    echo "=================================================="
    echo ""
    echo "💡 Next steps:"
    echo "   - Check status: ./scripts/check_metrics_backend.sh"
    echo "   - View metrics: curl localhost:8080/metrics/window60s | jq"
    echo "   - Fallback: ./scripts/fallback_to_memory.sh"
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
