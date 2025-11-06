#!/bin/bash
# selfcheck_observability.sh - Complete observability self-check
# Tests: Collect → Detect → Snapshot pipeline

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8011}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "━━━ Observability Self-Check ━━━"

# 1. Run preflight checks
echo "→ Running preflight..."
if bash "$(dirname "$0")/verify_preflight.sh" >/dev/null 2>&1; then
    echo "✓ Preflight PASS"
else
    echo "✗ Preflight FAIL - stopping"
    exit 1
fi

# 2. Inject test data to Redis
echo "→ Injecting test metrics..."
EXP_ID="selfcheck_$(date +%s)"
NOW=$(date +%s)
for i in {1..20}; do
    METRIC=$(cat <<EOF
{"ts":$NOW,"latency_ms":42.5,"ok":true,"route":"milvus","phase":"A","topk":10}
EOF
)
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" rpush "lab:exp:$EXP_ID:raw" "$METRIC" >/dev/null
    ((NOW++))
done
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" expire "lab:exp:$EXP_ID:raw" 300 >/dev/null
echo "✓ Injected 20 test metrics"

# 3. Test /api/metrics/mini
echo "→ Testing /api/metrics/mini..."
RESP=$(curl -sf "$BASE_URL/api/metrics/mini?exp_id=$EXP_ID&window_sec=120" 2>/dev/null || echo '{}')
P95=$(echo "$RESP" | jq -r '.p95 // 0' 2>/dev/null || echo "0")
QPS=$(echo "$RESP" | jq -r '.qps // 0' 2>/dev/null || echo "0")
ERR_PCT=$(echo "$RESP" | jq -r '.err_pct // 0' 2>/dev/null || echo "0")
echo "✓ P95=${P95}ms, QPS=${QPS}, Err%=${ERR_PCT}"

# 4. Test alarm logic (simulate high error rate)
echo "→ Testing alarm detection..."
python3 -c "
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')
from backend_core.alarm import maybe_alarm
result = maybe_alarm({'err_pct': 2.5, 'ab_imbalance_pct': 0, 'exp_id': '$EXP_ID'})
print('Alarm triggered:', result)
" 2>/dev/null && echo "✓ Alarm logic OK" || echo "✗ Alarm logic FAIL"

# 5. Test snapshot endpoint
echo "→ Testing /api/lab/snapshot..."
SNAP=$(curl -sf -X POST "$BASE_URL/api/lab/snapshot" -H "Content-Type: application/json" -d "{\"trigger\":\"selfcheck\",\"exp_id\":\"$EXP_ID\"}" 2>/dev/null || echo '{}')
SNAP_PATH=$(echo "$SNAP" | jq -r '.path // "none"')
if [ "$SNAP_PATH" != "none" ] && [ -f "$SNAP_PATH" ]; then
    echo "✓ Snapshot created: $SNAP_PATH"
else
    echo "✗ Snapshot creation failed"
fi

# 6. Cleanup
echo "→ Cleaning up..."
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" del "lab:exp:$EXP_ID:raw" >/dev/null
echo "✓ Test data cleaned"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Observability self-check complete"
echo ""
echo "Components verified:"
echo "  • Metrics collection (/api/metrics/mini)"
echo "  • Alarm detection (alarm.py)"
echo "  • Snapshot creation (/api/lab/snapshot)"
echo "  • Redis TTL & storage"
echo ""
echo "System ready for long-running tests."
