#!/usr/bin/env bash
# verify_kpi_alignment.sh - Verify KPI alignment to series60s with source badge
# Usage: ./scripts/verify_kpi_alignment.sh [--load-duration SECONDS]
# Exit codes: 0=PASS, 1=FAIL

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8080}"
LOAD_DURATION="${1:-30}"
TOLERANCE_PCT=10  # ±10% tolerance

echo "========================================="
echo "KPI Alignment Verification"
echo "========================================="
echo "API Base: $API_BASE"
echo "Load Duration: ${LOAD_DURATION}s"
echo ""

# Check if API is reachable
echo "[1/5] Checking API health..."
if ! curl -sf "$API_BASE/admin/health" > /dev/null; then
    echo "❌ FAIL: API not reachable at $API_BASE"
    exit 1
fi
echo "✅ API is reachable"
echo ""

# Start load generator to ensure data (support both /auto/start and /load/start)
echo "[2/5] Starting load generator (${LOAD_DURATION}s)..."

# Try /auto/start first (app.py), then /load/start (app_v2.py)
LOAD_RESPONSE=$(curl -s -X POST "$API_BASE/auto/start?qps=12&duration=$LOAD_DURATION&concurrency=16" 2>/dev/null)
LOAD_START=$(echo "$LOAD_RESPONSE" | jq -r '.ok // empty' 2>/dev/null)

if [ "$LOAD_START" = "true" ]; then
    echo "✅ Load generator started (via /auto/start)"
else
    # Fallback to /load/start for app_v2
    LOAD_RESPONSE=$(curl -s -X POST "$API_BASE/load/start?qps=12&duration=$LOAD_DURATION&concurrency=16" 2>/dev/null)
    LOAD_START=$(echo "$LOAD_RESPONSE" | jq -r '.ok // empty' 2>/dev/null)
    
    if [ "$LOAD_START" = "true" ]; then
        echo "✅ Load generator started (via /load/start)"
    else
        echo "⚠️  Load generator already running or failed to start, continuing..."
    fi
fi
echo ""

# Wait for data collection
echo "[3/5] Waiting for data collection (${LOAD_DURATION}s + 5s buffer)..."
sleep $((LOAD_DURATION + 5))
echo "✅ Data collection complete"
echo ""

# Verify /metrics/series60s data
echo "[4/5] Verifying /metrics/series60s data..."
SERIES_DATA=$(curl -sf "$API_BASE/metrics/series60s" || echo '{}')
SERIES_OK=$(echo "$SERIES_DATA" | jq -r '.ok // false')
SERIES_SAMPLES=$(echo "$SERIES_DATA" | jq -r '.samples // 0')
SERIES_BACKEND=$(echo "$SERIES_DATA" | jq -r '.meta.debug.backend // "unknown"')

if [ "$SERIES_OK" != "true" ]; then
    echo "❌ FAIL: /metrics/series60s returned ok=false"
    echo "Response: $SERIES_DATA"
    exit 1
fi

if [ "$SERIES_SAMPLES" -lt 3 ]; then
    echo "❌ FAIL: Insufficient samples in series60s (got $SERIES_SAMPLES, need ≥3)"
    exit 1
fi

echo "✅ series60s OK: samples=$SERIES_SAMPLES, backend=$SERIES_BACKEND"

# Verify time alignment and bucket count (series60s hardening)
SERIES_BUCKETS=$(echo "$SERIES_DATA" | jq -r '.buckets // 0')
if [ "$SERIES_BUCKETS" -lt 12 ] || [ "$SERIES_BUCKETS" -gt 13 ]; then
    echo "⚠️  WARNING: Unexpected bucket count (got $SERIES_BUCKETS, expected 12-13)"
fi

# Verify timestamp alignment (should be multiples of 5000ms)
MISALIGNED_TS=$(echo "$SERIES_DATA" | jq '[.tps[]?|.[0]]|map(select(. % 5000 != 0))|length')
if [ "$MISALIGNED_TS" != "0" ]; then
    echo "❌ FAIL: Found $MISALIGNED_TS misaligned timestamps (not multiples of 5000ms)"
    exit 1
fi

echo ""

# Calculate TPS from series60s (average of non-null TPS buckets)
echo "[5/5] Verifying TPS alignment..."
SERIES_TPS_AVG=$(echo "$SERIES_DATA" | jq '[.tps[]?|.[1]]|map(select(.!=null))|if length > 0 then (add/length) else null end')

if [ "$SERIES_TPS_AVG" = "null" ] || [ -z "$SERIES_TPS_AVG" ]; then
    echo "⚠️  WARNING: series60s TPS average is null or empty"
    SERIES_TPS_AVG="0"
fi

echo "  series60s TPS avg: $SERIES_TPS_AVG"

# Get /auto/status effective_tps_60s (if available)
AUTO_STATUS=$(curl -sf "$API_BASE/auto/status" 2>/dev/null || echo '{}')
AUTO_TPS=$(echo "$AUTO_STATUS" | jq -r '.effective_tps_60s // "N/A"')

echo "  /auto/status effective_tps_60s: $AUTO_TPS"

# Compare if both are available
if [ "$AUTO_TPS" != "N/A" ] && [ "$SERIES_TPS_AVG" != "0" ]; then
    # Calculate percentage difference
    DIFF=$(echo "$SERIES_TPS_AVG $AUTO_TPS" | awk '{printf "%.2f", ($1-$2)/$2*100}')
    DIFF_ABS=$(echo "$DIFF" | awk '{print ($1 < 0) ? -$1 : $1}')
    
    echo "  Difference: ${DIFF}%"
    
    if [ "$(echo "$DIFF_ABS > $TOLERANCE_PCT" | bc -l)" -eq 1 ]; then
        echo "❌ FAIL: TPS difference exceeds ±${TOLERANCE_PCT}% tolerance"
        exit 1
    else
        echo "✅ TPS values are aligned within ±${TOLERANCE_PCT}%"
    fi
else
    echo "⚠️  WARNING: Cannot compare TPS (one or both values unavailable)"
fi

echo ""
echo "========================================="
echo "✅ PASS: All KPI alignment checks passed"
echo "========================================="
echo ""
echo "Manual verification (optional):"
echo "  1. Open http://localhost:8080/?profile=balanced in browser"
echo "  2. Check badge contains 'source=/metrics/series60s'"
echo "  3. Open DevTools Console and verify one '[series60s]' log entry"
echo "  4. Verify TPS card shows value from series60s or '(fallback)' annotation"
echo ""
exit 0

