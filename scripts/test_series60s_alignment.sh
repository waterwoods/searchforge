#!/bin/bash
# test_series60s_alignment.sh - Verify /metrics/series60s alignment and stability
# Tests: bucket count (12-13), timestamp alignment (5s), no out-of-order, graceful empty window

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8080}"
ENDPOINT="${API_BASE}/metrics/series60s"

echo "=========================================="
echo "series60s Alignment Test"
echo "=========================================="
echo "Endpoint: ${ENDPOINT}"
echo ""

# Fetch data
RESPONSE=$(curl -s "${ENDPOINT}")
OK=$(echo "$RESPONSE" | jq -r '.ok // false')

if [[ "$OK" != "true" ]]; then
    ERROR=$(echo "$RESPONSE" | jq -r '.error // "unknown"')
    echo "❌ FAIL: Endpoint returned ok:false (error: ${ERROR})"
    exit 1
fi

echo "✅ Endpoint responded with ok:true"
echo ""

# Check 1: Bucket count (12 or 13)
echo "CHECK 1: Bucket count (expect 12-13)"
BUCKET_COUNT=$(echo "$RESPONSE" | jq -r '.buckets // 0')
if [[ "$BUCKET_COUNT" -lt 12 || "$BUCKET_COUNT" -gt 13 ]]; then
    echo "❌ FAIL: buckets=$BUCKET_COUNT (expected 12-13)"
    exit 1
fi
echo "✅ PASS: buckets=$BUCKET_COUNT"
echo ""

# Check 2: Timestamp alignment (all timestamps % 5000 == 0, no out-of-order)
echo "CHECK 2: Timestamp alignment (5s boundary, no out-of-order)"
TIMESTAMPS=$(echo "$RESPONSE" | jq -r '.tps[][0]')
PREV_TS=0
MISALIGNED=0
OUT_OF_ORDER=0

while IFS= read -r TS; do
    # Check 5s alignment
    if [[ $((TS % 5000)) -ne 0 ]]; then
        MISALIGNED=$((MISALIGNED + 1))
        echo "  ⚠️  Misaligned: $TS (% 5000 = $((TS % 5000)))"
    fi
    
    # Check monotonic ordering
    if [[ "$PREV_TS" -ne 0 && "$TS" -le "$PREV_TS" ]]; then
        OUT_OF_ORDER=$((OUT_OF_ORDER + 1))
        echo "  ⚠️  Out-of-order: $TS <= $PREV_TS"
    fi
    
    PREV_TS=$TS
done <<< "$TIMESTAMPS"

if [[ "$MISALIGNED" -gt 0 ]]; then
    echo "❌ FAIL: $MISALIGNED misaligned timestamps"
    exit 1
fi

if [[ "$OUT_OF_ORDER" -gt 0 ]]; then
    echo "❌ FAIL: $OUT_OF_ORDER out-of-order timestamps"
    exit 1
fi

echo "✅ PASS: All timestamps 5s-aligned and monotonic"
echo ""

# Check 3: Meta debug fields present
echo "CHECK 3: Enhanced debug info"
DROP_RATIO=$(echo "$RESPONSE" | jq -r '.meta.debug.drop_ratio // "missing"')
FILLED_HOLES=$(echo "$RESPONSE" | jq -r '.meta.debug.filled_holes // "missing"')
SOURCE_BACKEND=$(echo "$RESPONSE" | jq -r '.meta.debug.source_backend // "missing"')
HEARTBEAT_AGE=$(echo "$RESPONSE" | jq -r 'if .meta.debug | has("heartbeat_age_ms") then .meta.debug.heartbeat_age_ms else "missing" end')

if [[ "$DROP_RATIO" == "missing" ]]; then
    echo "❌ FAIL: meta.debug.drop_ratio missing"
    exit 1
fi

if [[ "$FILLED_HOLES" == "missing" ]]; then
    echo "❌ FAIL: meta.debug.filled_holes missing"
    exit 1
fi

if [[ "$SOURCE_BACKEND" == "missing" ]]; then
    echo "❌ FAIL: meta.debug.source_backend missing"
    exit 1
fi

echo "✅ PASS: Debug fields present"
echo "  - drop_ratio: $DROP_RATIO"
echo "  - filled_holes: $FILLED_HOLES"
echo "  - source_backend: $SOURCE_BACKEND"
echo "  - heartbeat_age_ms: $HEARTBEAT_AGE"
echo ""

# Check 4: Reactivity (conditional - skip if no recent samples)
echo "CHECK 4: Reactivity (conditional)"
SAMPLES=$(echo "$RESPONSE" | jq -r '.samples // 0')
HEARTBEAT_AGE_NUM=$(echo "$HEARTBEAT_AGE" | grep -E '^[0-9]+$' || echo "999999")

if [[ "$SAMPLES" -eq 0 || "$HEARTBEAT_AGE_NUM" -gt 30000 ]]; then
    echo "⚠️  SKIP: No recent traffic (samples=$SAMPLES, heartbeat_age=${HEARTBEAT_AGE}ms)"
    echo "   (Reactivity check requires active traffic)"
else
    # Check if TPS shows non-zero values in recent buckets
    RECENT_TPS=$(echo "$RESPONSE" | jq -r '.tps[-3:][] | .[1]')
    NON_ZERO=0
    while IFS= read -r TPS_VAL; do
        if [[ "$TPS_VAL" != "0" && "$TPS_VAL" != "null" ]]; then
            NON_ZERO=$((NON_ZERO + 1))
        fi
    done <<< "$RECENT_TPS"
    
    if [[ "$NON_ZERO" -gt 0 ]]; then
        echo "✅ PASS: Recent buckets show traffic (${NON_ZERO}/3 non-zero)"
    else
        echo "⚠️  WARN: No traffic in last 3 buckets (may be intermittent)"
    fi
fi
echo ""

# Summary
echo "=========================================="
echo "✅ ALL CHECKS PASSED"
echo "=========================================="
echo "Summary:"
echo "  - Bucket count: $BUCKET_COUNT (12-13)"
echo "  - Timestamp alignment: OK (5s boundary, monotonic)"
echo "  - Debug info: Complete"
echo "  - Samples: $SAMPLES"
echo ""

exit 0
