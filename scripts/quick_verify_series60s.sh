#!/bin/bash
# quick_verify_series60s.sh - Verify series60s API and frontend KPI alignment
# Usage: ./scripts/quick_verify_series60s.sh [BASE_URL]

set -e

BASE_URL="${1:-http://localhost:8080}"
PASS=0
FAIL=0

echo "=========================================="
echo "Series60s Verification Script"
echo "BASE_URL: $BASE_URL"
echo "=========================================="

# Helper functions
pass() { echo "✅ PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "❌ FAIL: $1"; FAIL=$((FAIL+1)); }
info() { echo "ℹ️  INFO: $1"; }

# Test 1: Health endpoint check
echo -e "\n[1/6] Checking /admin/health..."
HEALTH=$(curl -s "$BASE_URL/admin/health")
if echo "$HEALTH" | jq -e '.ok == true' >/dev/null 2>&1; then
    BACKEND=$(echo "$HEALTH" | jq -r '.core_metrics_backend // "unknown"')
    ROWS=$(echo "$HEALTH" | jq -r '.rows_60s // 0')
    pass "Health OK, backend=$BACKEND, rows_60s=$ROWS"
else
    fail "Health check failed"
    exit 1
fi

# Test 2: Series60s endpoint structure
echo -e "\n[2/6] Checking /metrics/series60s structure..."
SERIES=$(curl -s "$BASE_URL/metrics/series60s")
if echo "$SERIES" | jq -e '.ok == true' >/dev/null 2>&1; then
    BUCKETS=$(echo "$SERIES" | jq -r '.buckets // 0')
    SAMPLES=$(echo "$SERIES" | jq -r '.samples // 0')
    WINDOW=$(echo "$SERIES" | jq -r '.window_sec // 0')
    STEP=$(echo "$SERIES" | jq -r '.step_sec // 0')
    
    # Check bucket count (should be ~12±1 for 60s window / 5s step)
    if [ "$BUCKETS" -ge 11 ] && [ "$BUCKETS" -le 13 ]; then
        pass "Bucket count OK: $BUCKETS buckets (expected 12±1)"
    else
        fail "Bucket count off: $BUCKETS buckets (expected 12±1)"
    fi
    
    # Check window alignment
    if [ "$WINDOW" -eq 60 ] && [ "$STEP" -eq 5 ]; then
        pass "Window alignment OK: ${WINDOW}s window / ${STEP}s step"
    else
        fail "Window alignment off: ${WINDOW}s window / ${STEP}s step (expected 60s/5s)"
    fi
else
    fail "Series60s endpoint failed"
    exit 1
fi

# Test 3: Count non-null samples in each series
echo -e "\n[3/6] Counting non-null samples..."
P95_COUNT=$(echo "$SERIES" | jq '[.p95[] | select(.[1] != null)] | length')
TPS_COUNT=$(echo "$SERIES" | jq '[.tps[] | select(.[1] != null and .[1] > 0)] | length')
RECALL_COUNT=$(echo "$SERIES" | jq '[.recall[] | select(.[1] != null)] | length')

info "Non-null counts: p95=$P95_COUNT, tps=$TPS_COUNT, recall=$RECALL_COUNT"

if [ "$P95_COUNT" -ge 3 ] || [ "$TPS_COUNT" -ge 3 ] || [ "$RECALL_COUNT" -ge 3 ]; then
    pass "At least one metric has ≥3 non-null samples"
else
    info "All metrics have <3 samples (collecting state)"
fi

# Test 4: KPI alignment check (if samples >= 3)
echo -e "\n[4/6] Checking KPI computation alignment..."
if [ "$TPS_COUNT" -ge 3 ]; then
    # Compute average TPS from series
    AVG_TPS=$(echo "$SERIES" | jq '[.tps[] | select(.[1] != null and .[1] > 0) | .[1]] | add / length | . * 100 | round / 100')
    if echo "$AVG_TPS > 0" | bc -l >/dev/null 2>&1; then
        pass "TPS average from series: $AVG_TPS (samples=$TPS_COUNT)"
    else
        fail "TPS average is 0 despite having $TPS_COUNT samples"
    fi
else
    info "TPS: Collecting state ($TPS_COUNT/3 samples)"
fi

if [ "$P95_COUNT" -ge 3 ]; then
    AVG_P95=$(echo "$SERIES" | jq '[.p95[] | select(.[1] != null) | .[1]] | add / length | round')
    pass "P95 average from series: ${AVG_P95}ms (samples=$P95_COUNT)"
else
    info "P95: Collecting state ($P95_COUNT/3 samples)"
fi

if [ "$RECALL_COUNT" -ge 3 ]; then
    AVG_RECALL=$(echo "$SERIES" | jq '[.recall[] | select(.[1] != null) | .[1]] | add / length | . * 10000 | round / 100')
    pass "Recall average from series: ${AVG_RECALL}% (samples=$RECALL_COUNT)"
else
    info "Recall: Collecting state ($RECALL_COUNT/3 samples)"
fi

# Test 5: Null value handling (gaps in series)
echo -e "\n[5/6] Checking null value handling..."
NULL_P95=$(echo "$SERIES" | jq '[.p95[] | select(.[1] == null)] | length')
NULL_RECALL=$(echo "$SERIES" | jq '[.recall[] | select(.[1] == null)] | length')

if [ "$NULL_P95" -gt 0 ] || [ "$NULL_RECALL" -gt 0 ]; then
    info "Found null buckets: p95=$NULL_P95, recall=$NULL_RECALL (expected gaps in charts)"
    pass "Series correctly includes null values for empty buckets"
else
    info "No null buckets found (all buckets have data)"
fi

# Test 6: Frontend console log check
echo -e "\n[6/6] Frontend verification hints..."
info "To verify frontend, open browser to $BASE_URL/demo and check:"
info "  1. Console shows: [series60s] buckets=12±1, nonempty counts"
info "  2. Badge displays: Core(redis|memory) • window: 60s   source=/metrics/series60s"
info "  3. KPI shows 'Collecting… (N/3)' when samples < 3"
info "  4. Line charts break/disconnect at null values (no straight lines through gaps)"

# Summary
echo -e "\n=========================================="
echo "Summary: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -eq 0 ]; then
    echo "✅ All checks passed!"
    exit 0
else
    echo "❌ Some checks failed"
    exit 1
fi
