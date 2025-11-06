#!/bin/bash
# quick_ops_check.sh - Validate /ops/summary endpoint
# Exit codes: 0=PASS, 1=FAIL

set -e

# Load .env if available
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

BASE_URL="${BASE_URL:-${FIQA_API_URL:-http://localhost:8080}}"
ENDPOINT="$BASE_URL/ops/summary"

echo "🔍 Checking Ops Summary endpoint..."
echo "   Endpoint: $ENDPOINT"
echo ""

# Fetch the data
RESPONSE=$(curl -s "$ENDPOINT" || echo "{\"error\": \"fetch_failed\"}")

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo "❌ FAIL: Invalid JSON response"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Extract key fields
OK=$(echo "$RESPONSE" | jq -r '.ok // false')
BACKEND=$(echo "$RESPONSE" | jq -r '.backend // "unknown"')
WINDOW_SEC=$(echo "$RESPONSE" | jq -r '.window_sec // 0')
SAMPLES=$(echo "$RESPONSE" | jq -r '.window60s.samples // 0')
BUCKETS=$(echo "$RESPONSE" | jq -r '.series60s.buckets // 0')
STEP_SEC=$(echo "$RESPONSE" | jq -r '.series60s.step_sec // 0')
TPS=$(echo "$RESPONSE" | jq -r '.window60s.tps // 0')

# Validation checks
FAILED=0

echo "📊 Response Summary:"
echo "   ok: $OK"
echo "   backend: $BACKEND"
echo "   window_sec: $WINDOW_SEC"
echo "   samples: $SAMPLES"
echo "   buckets: $BUCKETS"
echo "   step_sec: $STEP_SEC"
echo "   tps: $TPS"
echo ""

# Check 1: ok should be true
if [ "$OK" != "true" ]; then
    echo "❌ FAIL: ok field is not true"
    FAILED=1
fi

# Check 2: backend should be redis or memory
if [[ "$BACKEND" != "redis" && "$BACKEND" != "memory" ]]; then
    echo "❌ FAIL: backend should be 'redis' or 'memory', got '$BACKEND'"
    FAILED=1
fi

# Check 3: window_sec should be 60
if [ "$WINDOW_SEC" -ne 60 ]; then
    echo "❌ FAIL: window_sec should be 60, got $WINDOW_SEC"
    FAILED=1
fi

# Check 4: buckets should be 12 or 13
if [[ "$BUCKETS" -ne 12 && "$BUCKETS" -ne 13 ]]; then
    echo "❌ FAIL: buckets should be 12 or 13, got $BUCKETS"
    FAILED=1
fi

# Check 5: step_sec should be 5
if [ "$STEP_SEC" -ne 5 ]; then
    echo "❌ FAIL: step_sec should be 5, got $STEP_SEC"
    FAILED=1
fi

# Check 6: If samples >= 3, TPS should be > 0
if [ "$SAMPLES" -ge 3 ]; then
    if (( $(echo "$TPS <= 0" | bc -l) )); then
        echo "⚠️  WARNING: samples >= 3 but TPS <= 0 (might be legitimate if no traffic)"
    fi
fi

# Final result
echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ PASS: All checks passed"
    exit 0
else
    echo "❌ FAIL: Some checks failed"
    echo ""
    echo "📝 Troubleshooting:"
    echo "   1. Check if backend is running: curl $BASE_URL/admin/health"
    echo "   2. Verify core.metrics is available"
    echo "   3. Check logs for errors"
    echo "   4. Try generating traffic: curl -X POST $BASE_URL/load/start?qps=10&duration=30"
    exit 1
fi


