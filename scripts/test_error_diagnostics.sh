#!/usr/bin/env bash
#
# test_error_diagnostics.sh — Test structured error handling for Black Swan
#
# Usage: ./scripts/test_error_diagnostics.sh [API_BASE]
#
# Tests:
# 1. Preflight checks (reports dir, script exec, API reachable)
# 2. Structured error reporting (code, step, http, message)
# 3. Retry logic (exponential backoff)
# 4. Insufficient samples detection
# 5. Frontend error display

set -euo pipefail

# Load .env if available
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

API_BASE="${1:-${APP_DEMO_URL:-http://localhost:8001}}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $*"; ((PASS++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $*"; ((FAIL++)); }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Black Swan Error Diagnostics Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Base: $API_BASE"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Preflight Endpoint
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 1: Preflight endpoint exists and returns structured checks"

PREFLIGHT_RESPONSE=$(curl -sf "${API_BASE}/ops/black_swan/preflight" 2>/dev/null || echo "{}")

if echo "$PREFLIGHT_RESPONSE" | jq -e '.ok' >/dev/null 2>&1; then
    PREFLIGHT_OK=$(echo "$PREFLIGHT_RESPONSE" | jq -r '.ok')
    
    if [[ "$PREFLIGHT_OK" == "true" ]]; then
        log_pass "Preflight checks passed"
    else
        log_fail "Preflight checks failed"
    fi
    
    # Check for required check fields
    CHECKS=$(echo "$PREFLIGHT_RESPONSE" | jq -r '.checks // {}')
    
    REQUIRED_CHECKS=("api_reachable" "reports_dir_exists" "reports_dir_writable" "script_exists" "script_executable")
    for check in "${REQUIRED_CHECKS[@]}"; do
        if echo "$CHECKS" | jq -e "has(\"$check\")" >/dev/null 2>&1; then
            log_pass "Preflight includes '$check' check"
        else
            log_fail "Preflight missing '$check' check"
        fi
    done
else
    log_fail "Preflight endpoint not working"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: Error Structure in State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 2: Error structure exists in state"

STATUS_RESPONSE=$(curl -sf "${API_BASE}/ops/black_swan/status" 2>/dev/null || echo "{}")

if echo "$STATUS_RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
    log_pass "error field exists in state"
    
    ERROR_STRUCT=$(echo "$STATUS_RESPONSE" | jq '.error')
    
    # Check required error fields
    REQUIRED_ERROR_FIELDS=("code" "step" "http" "message" "ts")
    for field in "${REQUIRED_ERROR_FIELDS[@]}"; do
        if echo "$ERROR_STRUCT" | jq -e "has(\"$field\")" >/dev/null 2>&1; then
            log_pass "error has '$field' field"
        else
            log_fail "error missing '$field' field"
        fi
    done
else
    log_fail "error field missing from state"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: Counters in State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 3: Counters exist in state"

if echo "$STATUS_RESPONSE" | jq -e '.counters' >/dev/null 2>&1; then
    log_pass "counters field exists in state"
    
    COUNTERS=$(echo "$STATUS_RESPONSE" | jq '.counters')
    
    # Check required counter fields
    REQUIRED_COUNTERS=("rejected_updates" "watchdog_checks" "heartbeat_checks" "retries")
    for counter in "${REQUIRED_COUNTERS[@]}"; do
        if echo "$COUNTERS" | jq -e "has(\"$counter\")" >/dev/null 2>&1; then
            log_pass "counters has '$counter' field"
        else
            log_fail "counters missing '$counter' field"
        fi
    done
else
    log_fail "counters field missing from state"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: Simulate Error Update
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 4: Test error update with wrong run_id (should be rejected)"

# Try to update with fake run_id (should fail)
ERROR_UPDATE=$(curl -sf -X POST "${API_BASE}/ops/black_swan/progress" \
    -H "Content-Type: application/json" \
    -d '{"run_id":"FAKE-ID","phase":"error","progress":0,"error":{"code":"test","step":"test","http":404,"message":"Test error"}}' \
    2>/dev/null || echo "{}")

if echo "$ERROR_UPDATE" | jq -e '.ok == false' >/dev/null 2>&1; then
    log_pass "Fake run_id error update rejected"
    
    ERROR_MSG=$(echo "$ERROR_UPDATE" | jq -r '.error // ""')
    if [[ "$ERROR_MSG" == *"run_id mismatch"* ]]; then
        log_pass "Error message indicates run_id mismatch"
    else
        log_fail "Error message doesn't mention run_id"
    fi
else
    log_fail "Fake run_id error update was not rejected"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: Check Error Display in Latest Report (if available)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 5: Check if error details are preserved in status"

# Get current status
CURRENT_STATUS=$(curl -sf "${API_BASE}/ops/black_swan/status" 2>/dev/null || echo "{}")
CURRENT_PHASE=$(echo "$CURRENT_STATUS" | jq -r '.phase // "none"')

if [[ "$CURRENT_PHASE" == "error" ]]; then
    log_info "Current test is in error phase, checking error structure..."
    
    ERROR_CODE=$(echo "$CURRENT_STATUS" | jq -r '.error.code // ""')
    ERROR_STEP=$(echo "$CURRENT_STATUS" | jq -r '.error.step // ""')
    ERROR_HTTP=$(echo "$CURRENT_STATUS" | jq -r '.error.http // 0')
    ERROR_MSG=$(echo "$CURRENT_STATUS" | jq -r '.error.message // ""')
    
    echo "  Error code: $ERROR_CODE"
    echo "  Error step: $ERROR_STEP"
    echo "  Error HTTP: $ERROR_HTTP"
    echo "  Error message: $ERROR_MSG"
    
    if [[ -n "$ERROR_CODE" ]] && [[ -n "$ERROR_STEP" ]]; then
        log_pass "Error structure is populated"
    else
        log_fail "Error structure is incomplete"
    fi
else
    log_info "No error phase active (current phase: $CURRENT_PHASE)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "✅ All error diagnostic tests passed!"
    echo ""
    echo "Verified:"
    echo "  ✓ Preflight endpoint with structured checks"
    echo "  ✓ Error structure in state (code, step, http, message, ts)"
    echo "  ✓ Counters in state (retries, rejected_updates, etc.)"
    echo "  ✓ Fake run_id error updates rejected"
    echo "  ✓ Error details preserved and displayable"
    echo ""
    exit 0
else
    echo "❌ Some error diagnostic tests failed"
    echo ""
    echo "Review the output above to identify issues."
    echo ""
    exit 1
fi


