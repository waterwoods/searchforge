#!/usr/bin/env bash
set -euo pipefail
BASE=${1:-http://localhost:8001}

echo "=== Qdrant Status Self-Check Script ==="
echo "Target: $BASE"
echo ""

echo "[1] Testing /ops/qdrant/config endpoint..."
echo "    → Checking response shape and required fields"
curl -s $BASE/ops/qdrant/config | jq -e '
  .ok==true and
  (.concurrency|type=="number") and
  (.batch_size|type=="number") and
  (.override|type=="boolean") and
  (.source|type=="string") and
  (.defaults|type=="object") and
  (.defaults.concurrency|type=="number") and
  (.defaults.batch_size|type=="number")
' > /dev/null

if [ $? -eq 0 ]; then
    echo "    ✅ Config endpoint: PASS"
    echo "    Response preview:"
    curl -s $BASE/ops/qdrant/config | jq '{ok, override, concurrency, batch_size, source}'
else
    echo "    ❌ Config endpoint: FAIL"
    exit 1
fi

echo ""
echo "[2] Testing /ops/qdrant/stats endpoint..."
echo "    → Checking response shape and required fields"
curl -s $BASE/ops/qdrant/stats | jq -e '
  (.ok==true or .ok==false) and
  (has("hits_60s")) and
  (has("avg_query_ms_60s")) and
  (has("p95_query_ms_60s")) and
  (has("remote_pct_60s")) and
  (has("cache_pct_60s")) and
  (.window_sec==60 or .window_sec==null)
' > /dev/null

if [ $? -eq 0 ]; then
    echo "    ✅ Stats endpoint: PASS"
    echo "    Response preview:"
    curl -s $BASE/ops/qdrant/stats | jq '{ok, hits_60s, avg_query_ms_60s, p95_query_ms_60s, window_sec}'
else
    echo "    ❌ Stats endpoint: FAIL"
    exit 1
fi

echo ""
echo "[3] Testing endpoint availability (no 5xx errors)..."
CONFIG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE/ops/qdrant/config)
STATS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE/ops/qdrant/stats)

if [ "$CONFIG_STATUS" -ge 200 ] && [ "$CONFIG_STATUS" -lt 500 ]; then
    echo "    ✅ Config endpoint HTTP status: $CONFIG_STATUS (OK)"
else
    echo "    ❌ Config endpoint HTTP status: $CONFIG_STATUS (ERROR)"
    exit 1
fi

if [ "$STATS_STATUS" -ge 200 ] && [ "$STATS_STATUS" -lt 500 ]; then
    echo "    ✅ Stats endpoint HTTP status: $STATS_STATUS (OK)"
else
    echo "    ❌ Stats endpoint HTTP status: $STATS_STATUS (ERROR)"
    exit 1
fi

echo ""
echo "[4] Testing override mode detection..."
export BS_QDRANT_OVERRIDE=1
export BS_QDRANT_MAX_CONCURRENCY=8
export BS_QDRANT_BATCH_SIZE=2

echo "    → Set BS_QDRANT_OVERRIDE=1, BS_QDRANT_MAX_CONCURRENCY=8, BS_QDRANT_BATCH_SIZE=2"
echo "    → Note: You'll need to restart the backend for this to take effect"
echo "    → Skipping live test (requires backend restart)"

echo ""
echo "=== ✅ All Qdrant status endpoints look good ==="
echo ""
echo "Next steps:"
echo "  1. Start backend: cd services/fiqa_api && MAIN_PORT=8001 bash start_server.sh"
echo "  2. Open frontend: http://localhost:3000"
echo "  3. Check the Qdrant Status Card in the SLA Dashboard"
echo "  4. To test override mode:"
echo "     - Set BS_QDRANT_OVERRIDE=1 and BS_QDRANT_MAX_CONCURRENCY=8 in .env"
echo "     - Restart backend"
echo "     - Card should show concurrency=8 with 'throttled' badge"
echo ""


