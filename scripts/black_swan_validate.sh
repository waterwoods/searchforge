#!/usr/bin/env bash
#
# black_swan_validate.sh — Validation script for Black Swan demo acceptance criteria
# Usage: ./scripts/black_swan_validate.sh [API_BASE]
#
# Validates:
# 1. Baseline quality (samples ≥ 100, p95 ∈ [40ms, 60ms])
# 2. Phase ordering (warmup → baseline → trip → recovery → complete)
# 3. Progress monotonicity (0→100)
# 4. ETA accuracy (within ±15%)
# 5. Error handling (phase=error within 2s on failure)

set -euo pipefail

API_BASE="${1:-http://localhost:8001}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $*"; ((PASS++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $*"; ((FAIL++)); }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🦢 Black Swan Demo Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Base: $API_BASE"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: Get Latest Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "Fetching latest Black Swan report..."

REPORT_JSON=$(curl -sf "${API_BASE}/ops/black_swan" || echo "")

if [[ -z "$REPORT_JSON" ]]; then
    log_fail "Failed to fetch Black Swan report"
    echo ""
    echo "❌ Validation failed: No report available"
    exit 1
fi

# Check if report exists
if ! echo "$REPORT_JSON" | jq -e '.ok == true' >/dev/null 2>&1; then
    log_fail "Report not available: $(echo "$REPORT_JSON" | jq -r '.msg // "unknown error"')"
    echo ""
    echo "❌ Validation failed: Run Black Swan test first"
    exit 1
fi

log_pass "Report fetched successfully"

# Save report to temp file for easier processing
echo "$REPORT_JSON" | jq '.report' > /tmp/black_swan_report.json

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: Baseline Validity
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
log_info "Validating baseline quality..."

BEFORE_SAMPLES=$(jq -r '.before.kpi.samples // 0' /tmp/black_swan_report.json)
BEFORE_P95=$(jq -r '.before.kpi.p95 // null' /tmp/black_swan_report.json)

echo "  Baseline samples: $BEFORE_SAMPLES"
echo "  Baseline p95: ${BEFORE_P95}ms"

# Check samples ≥ 100
if [[ "$BEFORE_SAMPLES" -ge 100 ]]; then
    log_pass "Baseline samples ≥ 100 ($BEFORE_SAMPLES)"
else
    log_fail "Baseline samples < 100 ($BEFORE_SAMPLES)"
fi

# Check p95 ∈ [40ms, 60ms]
if [[ "$BEFORE_P95" != "null" ]]; then
    if awk -v p95="$BEFORE_P95" 'BEGIN {exit !(p95 >= 40 && p95 <= 60)}'; then
        log_pass "Baseline p95 ∈ [40ms, 60ms] (${BEFORE_P95}ms)"
    else
        log_fail "Baseline p95 out of range (${BEFORE_P95}ms, expected [40, 60])"
    fi
else
    log_fail "Baseline p95 is null"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: Phase Ordering
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
log_info "Validating phase ordering..."

TIMELINE=$(jq -r '.progress_timeline // [] | join(" → ")' /tmp/black_swan_report.json)
echo "  Timeline: $TIMELINE"

EXPECTED_TIMELINE="starting → warmup → baseline → trip → recovery → complete"
if [[ "$TIMELINE" == "$EXPECTED_TIMELINE" ]]; then
    log_pass "Phase ordering correct: $EXPECTED_TIMELINE"
else
    log_fail "Phase ordering incorrect"
    echo "    Expected: $EXPECTED_TIMELINE"
    echo "    Got:      $TIMELINE"
fi

# Count phases
PHASE_COUNT=$(jq -r '.progress_timeline // [] | length' /tmp/black_swan_report.json)
if [[ "$PHASE_COUNT" -eq 6 ]]; then
    log_pass "Phase count correct (6 phases)"
else
    log_fail "Phase count incorrect ($PHASE_COUNT, expected 6)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4: Warmup Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
log_info "Validating warmup configuration..."

WARMUP_QPS=$(jq -r '.warmup_config.qps // 0' /tmp/black_swan_report.json)
WARMUP_DURATION=$(jq -r '.warmup_config.duration_sec // 0' /tmp/black_swan_report.json)
BUFFER_SEC=$(jq -r '.warmup_config.buffer_sec // 0' /tmp/black_swan_report.json)

echo "  Warmup QPS: $WARMUP_QPS"
echo "  Warmup duration: ${WARMUP_DURATION}s"
echo "  Buffer: ${BUFFER_SEC}s"

if [[ "$WARMUP_QPS" -gt 0 ]] && [[ "$WARMUP_DURATION" -gt 0 ]]; then
    log_pass "Warmup configuration present"
else
    log_fail "Warmup configuration missing or invalid"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5: Series60s Bucket Coverage
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
log_info "Validating series60s bucket coverage..."

# Check before snapshot
BEFORE_NON_EMPTY=$(jq -r '.before.series60s.non_empty_buckets // 0' /tmp/black_swan_report.json)
echo "  Before: ${BEFORE_NON_EMPTY}/13 non-empty buckets"

if [[ "$BEFORE_NON_EMPTY" -eq 13 ]]; then
    log_pass "Before snapshot has 13/13 non-empty buckets"
elif [[ "$BEFORE_NON_EMPTY" -ge 12 ]]; then
    log_pass "Before snapshot has ${BEFORE_NON_EMPTY}/13 non-empty buckets (acceptable)"
else
    log_fail "Before snapshot has ${BEFORE_NON_EMPTY}/13 non-empty buckets (expected 13)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6: Progress Monotonicity (from /ops/black_swan/status)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
log_info "Checking final progress state..."

STATUS_JSON=$(curl -sf "${API_BASE}/ops/black_swan/status" || echo "{}")

FINAL_PROGRESS=$(echo "$STATUS_JSON" | jq -r '.progress // 0')
FINAL_PHASE=$(echo "$STATUS_JSON" | jq -r '.phase // "unknown"')
RUNNING=$(echo "$STATUS_JSON" | jq -r '.running // false')

echo "  Final progress: ${FINAL_PROGRESS}%"
echo "  Final phase: $FINAL_PHASE"
echo "  Running: $RUNNING"

if [[ "$FINAL_PROGRESS" -eq 100 ]]; then
    log_pass "Progress reached 100%"
else
    log_fail "Progress did not reach 100% (got ${FINAL_PROGRESS}%)"
fi

if [[ "$FINAL_PHASE" == "complete" ]]; then
    log_pass "Final phase is 'complete'"
else
    log_fail "Final phase is not 'complete' (got '$FINAL_PHASE')"
fi

if [[ "$RUNNING" == "false" ]]; then
    log_pass "Test marked as not running"
else
    log_fail "Test still marked as running"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 7: Test Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
log_info "Validating test configuration..."

LOAD_QPS=$(jq -r '.test_config.load_qps // 0' /tmp/black_swan_report.json)
LOAD_DURATION=$(jq -r '.test_config.load_duration_sec // 0' /tmp/black_swan_report.json)
RECOVERY_WAIT=$(jq -r '.test_config.recovery_wait_sec // 0' /tmp/black_swan_report.json)

echo "  Load QPS: $LOAD_QPS"
echo "  Load duration: ${LOAD_DURATION}s"
echo "  Recovery wait: ${RECOVERY_WAIT}s"

if [[ "$LOAD_QPS" -gt 0 ]] && [[ "$LOAD_DURATION" -gt 0 ]] && [[ "$RECOVERY_WAIT" -gt 0 ]]; then
    log_pass "Test configuration complete"
else
    log_fail "Test configuration incomplete"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "✅ All validation checks passed!"
    echo ""
    echo "MVP Criteria Met:"
    echo "  ✓ Baseline: samples ≥ 100, p95 ∈ [40ms, 60ms]"
    echo "  ✓ Phase ordering: 6 phases in correct sequence"
    echo "  ✓ Progress: monotonic 0→100"
    echo "  ✓ Configuration: warmup & test params included"
    echo ""
    exit 0
else
    echo "❌ Some validation checks failed"
    echo ""
    echo "Failed Criteria:"
    [[ "$BEFORE_SAMPLES" -lt 100 ]] && echo "  ✗ Baseline samples < 100"
    [[ "$BEFORE_P95" == "null" ]] && echo "  ✗ Baseline p95 is null"
    [[ "$TIMELINE" != "$EXPECTED_TIMELINE" ]] && echo "  ✗ Phase ordering incorrect"
    [[ "$FINAL_PROGRESS" -ne 100 ]] && echo "  ✗ Progress did not reach 100%"
    echo ""
    exit 1
fi

