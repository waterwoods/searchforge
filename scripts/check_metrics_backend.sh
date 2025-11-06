#!/bin/bash
# check_metrics_backend.sh - Display current metrics backend status
# Usage: ./scripts/check_metrics_backend.sh

set -e

echo "=================================================="
echo "📊 Metrics Backend Status"
echo "=================================================="
echo ""

# Check if API is running
if ! curl -s http://localhost:8080/admin/health > /dev/null 2>&1; then
    echo "❌ API not responding at http://localhost:8080"
    echo ""
    echo "💡 Start the API first:"
    echo "   cd services/fiqa_api"
    echo "   uvicorn app_v2:app --port 8080"
    exit 1
fi

# Fetch health data
HEALTH_RESPONSE=$(curl -s http://localhost:8080/admin/health)

# Parse JSON fields (using grep for portability)
OK=$(echo "$HEALTH_RESPONSE" | grep -o '"ok":[^,}]*' | cut -d':' -f2)
BACKEND=$(echo "$HEALTH_RESPONSE" | grep -o '"core_metrics_backend":"[^"]*"' | cut -d'"' -f4)
REDIS_CONNECTED=$(echo "$HEALTH_RESPONSE" | grep -o '"redis_connected":[^,}]*' | cut -d':' -f2)
ROWS=$(echo "$HEALTH_RESPONSE" | grep -o '"rows_60s":[0-9]*' | cut -d':' -f2)
WINDOW=$(echo "$HEALTH_RESPONSE" | grep -o '"window_sec":[0-9]*' | cut -d':' -f2)
TIMESTAMP=$(echo "$HEALTH_RESPONSE" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)

# Determine status icon
if [ "$OK" = "true" ]; then
    STATUS_ICON="✅"
else
    STATUS_ICON="❌"
fi

# Display status
echo "$STATUS_ICON API Health: $OK"
echo ""
echo "Backend Configuration:"
echo "  • Type:            $BACKEND"
echo "  • Redis Connected: $REDIS_CONNECTED"
echo ""
echo "Metrics Window:"
echo "  • Window:          ${WINDOW}s"
echo "  • Samples:         $ROWS rows"
echo "  • Last Update:     $TIMESTAMP"
echo ""

# Show recommendation based on backend
if [ "$BACKEND" = "redis" ]; then
    if [ "$REDIS_CONNECTED" = "true" ]; then
        echo "=================================================="
        echo "✅ PASS - Redis backend operational"
        echo "=================================================="
        echo ""
        echo "💡 Commands:"
        echo "   - Switch to memory: ./scripts/fallback_to_memory.sh"
        echo "   - View metrics:     curl localhost:8080/metrics/series60s | jq"
    else
        echo "=================================================="
        echo "⚠️  WARNING - Redis backend configured but not connected"
        echo "=================================================="
        echo ""
        echo "💡 Troubleshooting:"
        echo "   - Check Redis:      redis-cli ping"
        echo "   - Restart Redis:    redis-server --daemonize yes"
        echo "   - Switch to memory: ./scripts/fallback_to_memory.sh"
    fi
elif [ "$BACKEND" = "memory" ]; then
    echo "=================================================="
    echo "✅ PASS - Memory backend operational"
    echo "=================================================="
    echo ""
    echo "💡 Commands:"
    echo "   - Switch to Redis: ./scripts/switch_to_redis.sh"
    echo "   - View metrics:    curl localhost:8080/metrics/series60s | jq"
else
    echo "=================================================="
    echo "⚠️  WARNING - Unknown backend: $BACKEND"
    echo "=================================================="
fi

exit 0
