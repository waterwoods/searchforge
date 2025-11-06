#!/bin/bash
# Quick test script for app_v2.py endpoints
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
TIMEOUT=3

echo "Testing app_v2.py endpoints at $BASE_URL"
echo "=========================================="
echo ""

# Test 1: Health check
echo "1. Testing /admin/health..."
response=$(curl -s --max-time "$TIMEOUT" "$BASE_URL/admin/health" || echo '{"ok": false, "error": "connection failed"}')
ok=$(echo "$response" | jq -r '.ok // false')
backend=$(echo "$response" | jq -r '.core_metrics_backend // "unknown"')
rows=$(echo "$response" | jq -r '.rows_60s // "N/A"')
window=$(echo "$response" | jq -r '.window_sec // "N/A"')

if [ "$ok" = "true" ]; then
    echo "   ✅ Health check OK"
    echo "      Backend: $backend"
    echo "      Rows (60s): $rows"
    echo "      Window: ${window}s"
else
    echo "   ❌ Health check failed: $(echo "$response" | jq -r '.error // "unknown error"')"
fi
echo ""

# Test 2: Window60s
echo "2. Testing /metrics/window60s..."
response=$(curl -s --max-time "$TIMEOUT" "$BASE_URL/metrics/window60s" || echo '{"ok": false}')
ok=$(echo "$response" | jq -r '.ok // false')
samples=$(echo "$response" | jq -r '.samples // "N/A"')
p95=$(echo "$response" | jq -r '.p95_ms // "null"')
tps=$(echo "$response" | jq -r '.tps // "null"')
recall=$(echo "$response" | jq -r '.recall_at_10 // "null"')

if [ "$ok" = "true" ]; then
    echo "   ✅ Window60s OK"
    echo "      Samples: $samples"
    echo "      P95: ${p95}ms"
    echo "      TPS: $tps"
    echo "      Recall@10: $recall"
else
    echo "   ❌ Window60s failed"
fi
echo ""

# Test 3: Series60s
echo "3. Testing /metrics/series60s..."
response=$(curl -s --max-time "$TIMEOUT" "$BASE_URL/metrics/series60s" || echo '{"ok": false}')
ok=$(echo "$response" | jq -r '.ok // false')
source=$(echo "$response" | jq -r '.source // "unknown"')
buckets=$(echo "$response" | jq -r '.buckets // 0')
p95_len=$(echo "$response" | jq '.p95 // [] | length')
tps_len=$(echo "$response" | jq '.tps // [] | length')
recall_len=$(echo "$response" | jq '.recall // [] | length')

if [ "$ok" = "true" ]; then
    echo "   ✅ Series60s OK"
    echo "      Source: $source"
    echo "      Buckets: $buckets"
    echo "      P95 array: $p95_len items"
    echo "      TPS array: $tps_len items"
    echo "      Recall array: $recall_len items"
    
    # Verify all arrays have same length
    if [ "$p95_len" = "$tps_len" ] && [ "$tps_len" = "$recall_len" ] && [ "$p95_len" = "$buckets" ]; then
        echo "   ✅ Array lengths match buckets count"
    else
        echo "   ⚠️  Array length mismatch: p95=$p95_len, tps=$tps_len, recall=$recall_len, buckets=$buckets"
    fi
    
    # Check bucket alignment (5s)
    first_ts=$(echo "$response" | jq -r '.p95[0][0] // 0')
    if [ "$first_ts" != "0" ]; then
        mod=$((first_ts % 5000))
        if [ "$mod" -eq 0 ]; then
            echo "   ✅ Time alignment OK (5s buckets)"
        else
            echo "   ❌ Time misalignment: $first_ts % 5000 = $mod"
        fi
    fi
else
    echo "   ❌ Series60s failed"
fi
echo ""

echo "=========================================="
echo "Test complete!"

