#!/usr/bin/env bash
# ============================================================================
# test_series60s.sh - Smoke test for /metrics/series60s endpoint
# ============================================================================
# Usage:
#   ./scripts/test_series60s.sh
#
# Prerequisites:
#   - Service running on localhost:8080
#   - CORE_METRICS_ENABLED=1
#   - Some traffic to generate samples
# ============================================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
ENDPOINT="$BASE_URL/metrics/series60s"

echo "============================================"
echo "  /metrics/series60s Smoke Test"
echo "============================================"
echo ""

# Test 1: Endpoint responds with 200
echo "[1/4] Testing endpoint availability..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT")
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Endpoint returns 200 OK"
else
    echo "❌ Endpoint returned HTTP $HTTP_CODE"
    exit 1
fi

# Test 2: Response is valid JSON
echo ""
echo "[2/4] Testing JSON validity..."
RESPONSE=$(curl -s "$ENDPOINT")
if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo "✅ Response is valid JSON"
else
    echo "❌ Response is not valid JSON"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 3: Check required fields
echo ""
echo "[3/4] Testing response structure..."
OK=$(echo "$RESPONSE" | jq -r '.ok')
WINDOW=$(echo "$RESPONSE" | jq -r '.window_sec')
STEP=$(echo "$RESPONSE" | jq -r '.step_sec')
SAMPLES=$(echo "$RESPONSE" | jq -r '.samples')

if [ "$OK" = "true" ] || [ "$OK" = "false" ]; then
    echo "✅ Field 'ok' present: $OK"
else
    echo "❌ Field 'ok' missing or invalid"
    exit 1
fi

if [ "$WINDOW" = "60" ]; then
    echo "✅ Field 'window_sec' = 60"
else
    echo "⚠️  Field 'window_sec' = $WINDOW (expected 60)"
fi

if [ "$STEP" = "5" ]; then
    echo "✅ Field 'step_sec' = 5"
else
    echo "⚠️  Field 'step_sec' = $STEP (expected 5)"
fi

echo "   Samples: $SAMPLES"

# Test 4: Validate series arrays
echo ""
echo "[4/4] Testing series data structure..."

P95_COUNT=$(echo "$RESPONSE" | jq '.p95 | length')
TPS_COUNT=$(echo "$RESPONSE" | jq '.tps | length')
RECALL_COUNT=$(echo "$RESPONSE" | jq '.recall | length')

echo "   P95 data points: $P95_COUNT"
echo "   TPS data points: $TPS_COUNT"
echo "   Recall data points: $RECALL_COUNT"

# Validate arrays are arrays
P95_IS_ARRAY=$(echo "$RESPONSE" | jq '.p95 | type')
TPS_IS_ARRAY=$(echo "$RESPONSE" | jq '.tps | type')
RECALL_IS_ARRAY=$(echo "$RESPONSE" | jq '.recall | type')

if [ "$P95_IS_ARRAY" = '"array"' ] && [ "$TPS_IS_ARRAY" = '"array"' ] && [ "$RECALL_IS_ARRAY" = '"array"' ]; then
    echo "✅ All series are arrays"
else
    echo "❌ One or more series are not arrays"
    exit 1
fi

# If we have data, validate structure of first element
if [ "$TPS_COUNT" -gt 0 ]; then
    FIRST_TPS=$(echo "$RESPONSE" | jq '.tps[0]')
    FIRST_TPS_LEN=$(echo "$FIRST_TPS" | jq 'length')
    
    if [ "$FIRST_TPS_LEN" = "2" ]; then
        TS=$(echo "$FIRST_TPS" | jq '.[0]')
        VAL=$(echo "$FIRST_TPS" | jq '.[1]')
        echo "✅ Data point format correct: [timestamp_ms, value]"
        echo "   Example: [$TS, $VAL]"
    else
        echo "❌ Data point format incorrect (expected 2-element array)"
        exit 1
    fi
fi

# Summary
echo ""
echo "============================================"
echo "  Summary"
echo "============================================"
echo "Status: ${OK}"
echo "Window: ${WINDOW}s"
echo "Step: ${STEP}s"
echo "Total samples: ${SAMPLES}"
echo "Data points: P95=${P95_COUNT}, TPS=${TPS_COUNT}, Recall=${RECALL_COUNT}"
echo ""

if [ "$OK" = "true" ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "Sample response:"
    echo "$RESPONSE" | jq '.'
    exit 0
elif [ "$OK" = "false" ]; then
    REASON=$(echo "$RESPONSE" | jq -r '.reason // "unknown"')
    echo "⚠️  Endpoint returned ok:false (reason: $REASON)"
    echo "This may be expected if CORE_METRICS_ENABLED=0 or no samples yet."
    exit 0
else
    echo "❌ Unexpected response"
    exit 1
fi

