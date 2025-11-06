#!/usr/bin/env bash
#
# black_swan_fixpack_check.sh — Validation for Small Fix Pack
# Tests: Adaptive baseline gates, GET purity, Progress contracts
#
# Usage: ./scripts/black_swan_fixpack_check.sh [API_BASE]

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
echo "🔧 Black Swan Small Fix Pack Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Base: $API_BASE"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Baseline Gate (Adaptive)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Adaptive Baseline Gates"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_info "Checking if Black Swan report exists..."

REPORT_JSON=$(curl -sf "${API_BASE}/ops/black_swan" 2>/dev/null || echo "")

if [[ -z "$REPORT_JSON" ]] || ! echo "$REPORT_JSON" | jq -e '.ok == true' >/dev/null 2>&1; then
    log_info "No report yet. Run Black Swan test first:"
    echo "  curl -X POST ${API_BASE}/ops/black_swan"
    echo ""
    log_fail "Cannot validate baseline_gate without a report"
else
    log_pass "Report available"
    
    # Check baseline_gate structure
    if echo "$REPORT_JSON" | jq -e '.report.baseline_gate' >/dev/null 2>&1; then
        log_pass "baseline_gate exists in report"
        
        # Extract baseline_gate
        BASELINE_GATE=$(echo "$REPORT_JSON" | jq '.report.baseline_gate')
        
        # Check required fields
        REQUIRED_FIELDS=("p95_ms" "samples" "accepted" "warning" "reason")
        for field in "${REQUIRED_FIELDS[@]}"; do
            if echo "$BASELINE_GATE" | jq -e "has(\"$field\")" >/dev/null 2>&1; then
                log_pass "baseline_gate has '$field' field"
            else
                log_fail "baseline_gate missing '$field' field"
            fi
        done
        
        # Display baseline_gate
        echo ""
        echo "Baseline Gate Details:"
        echo "$BASELINE_GATE" | jq '.'
        echo ""
        
        # Check logic: accepted OR warning with reason
        ACCEPTED=$(echo "$BASELINE_GATE" | jq -r '.accepted // false')
        WARNING=$(echo "$BASELINE_GATE" | jq -r '.warning // false')
        REASON=$(echo "$BASELINE_GATE" | jq -r '.reason // "unknown"')
        
        if [[ "$ACCEPTED" == "true" ]] && [[ "$WARNING" == "false" ]] && [[ "$REASON" == "ok" ]]; then
            log_pass "Baseline accepted (no warnings)"
        elif [[ "$WARNING" == "true" ]] && [[ "$REASON" != "ok" ]]; then
            log_pass "Baseline warning recorded (reason: $REASON) - data not dropped"
        else
            log_fail "Baseline gate logic unclear (accepted=$ACCEPTED, warning=$WARNING, reason=$REASON)"
        fi
        
    else
        log_fail "baseline_gate not found in report"
    fi
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: GET Purity
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: GET Endpoint Purity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_info "Testing GET endpoints for purity (no state mutations)..."

ENDPOINTS=(
    "/auto/status"
    "/tuner/enabled"
    "/admin/warmup/status"
    "/ops/black_swan/status"
)

for endpoint in "${ENDPOINTS[@]}"; do
    log_info "Testing: $endpoint"
    
    # Call twice, stripping dynamic fields (timestamp, eta_sec, progress, message)
    CALL1=$(curl -sf "${API_BASE}${endpoint}" 2>/dev/null | jq '.|del(.timestamp,.eta_sec,.progress,.message)' 2>/dev/null || echo "ERROR")
    sleep 0.5  # Small delay to avoid rate limiting
    CALL2=$(curl -sf "${API_BASE}${endpoint}" 2>/dev/null | jq '.|del(.timestamp,.eta_sec,.progress,.message)' 2>/dev/null || echo "ERROR")
    
    if [[ "$CALL1" == "ERROR" ]] || [[ "$CALL2" == "ERROR" ]]; then
        log_fail "$endpoint - Failed to call endpoint"
        continue
    fi
    
    # Compare
    if diff <(echo "$CALL1") <(echo "$CALL2") >/dev/null 2>&1; then
        log_pass "$endpoint - PURE (no state changes)"
    else
        log_fail "$endpoint - MUTATION DETECTED (state changed between calls)"
        echo "  First call:  $CALL1"
        echo "  Second call: $CALL2"
    fi
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: Progress Contracts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Progress Contracts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_info "Checking current Black Swan state..."

STATUS_JSON=$(curl -sf "${API_BASE}/ops/black_swan/status" 2>/dev/null || echo "{}")

PHASE=$(echo "$STATUS_JSON" | jq -r '.phase // "unknown"')
PROGRESS=$(echo "$STATUS_JSON" | jq -r '.progress // -1')
RUNNING=$(echo "$STATUS_JSON" | jq -r '.running // false')

echo "Current state: phase=$PHASE, progress=$PROGRESS%, running=$RUNNING"
echo ""

# Check progress_checks field
if echo "$STATUS_JSON" | jq -e '.progress_checks' >/dev/null 2>&1; then
    log_pass "progress_checks field exists"
    
    PROGRESS_CHECKS=$(echo "$STATUS_JSON" | jq '.progress_checks')
    echo "Progress Checks:"
    echo "$PROGRESS_CHECKS" | jq '.'
    echo ""
    
    MONOTONIC=$(echo "$PROGRESS_CHECKS" | jq -r '.monotonic // false')
    if [[ "$MONOTONIC" == "true" ]]; then
        log_pass "Progress is monotonic"
    else
        log_fail "Progress monotonicity violated"
    fi
else
    log_fail "progress_checks field missing"
fi

# If test is complete, validate final state
if [[ "$PHASE" == "complete" ]]; then
    if [[ "$PROGRESS" -eq 100 ]]; then
        log_pass "Final progress is 100%"
    else
        log_fail "Final progress is $PROGRESS% (expected 100%)"
    fi
    
    if [[ "$RUNNING" == "false" ]]; then
        log_pass "Test marked as not running"
    else
        log_fail "Test still marked as running"
    fi
elif [[ "$PHASE" == "error" ]]; then
    log_info "Test ended with error phase (expected behavior for failures)"
    
    if [[ "$RUNNING" == "false" ]]; then
        log_pass "Error phase marked as not running"
    else
        log_fail "Error phase still marked as running"
    fi
elif [[ "$PHASE" != "unknown" ]] && [[ "$RUNNING" == "true" ]]; then
    log_info "Test in progress (phase=$PHASE, progress=$PROGRESS%)"
    log_info "Run this script again after test completion for full validation"
fi

# Check phase timeline ordering (if report exists)
if [[ -n "$REPORT_JSON" ]] && echo "$REPORT_JSON" | jq -e '.ok == true' >/dev/null 2>&1; then
    echo ""
    log_info "Validating phase timeline ordering from report..."
    
    TIMELINE=$(echo "$REPORT_JSON" | jq -r '.report.progress_timeline // [] | join(" → ")')
    EXPECTED="starting → warmup → baseline → trip → recovery → complete"
    
    echo "  Timeline: $TIMELINE"
    
    if [[ "$TIMELINE" == "$EXPECTED" ]]; then
        log_pass "Phase timeline ordering correct"
    else
        log_fail "Phase timeline ordering incorrect"
        echo "    Expected: $EXPECTED"
        echo "    Got:      $TIMELINE"
    fi
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
    echo "✅ All fix pack checks passed!"
    echo ""
    echo "Fix Pack Status:"
    echo "  ✓ Adaptive baseline gates (warn instead of reject)"
    echo "  ✓ GET endpoints are pure (no state mutations)"
    echo "  ✓ Progress contracts enforced (monotonic, ordered phases)"
    echo ""
    exit 0
else
    echo "❌ Some fix pack checks failed"
    echo ""
    if [[ "$REPORT_JSON" == "" ]] || ! echo "$REPORT_JSON" | jq -e '.ok == true' >/dev/null 2>&1; then
        echo "Note: Run a Black Swan test first to enable full validation:"
        echo "  curl -X POST ${API_BASE}/ops/black_swan"
        echo ""
    fi
    exit 1
fi

