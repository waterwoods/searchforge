#!/usr/bin/env bash
#
# test_runid_gating.sh — Test run_id gating for "instant complete" fix
#
# Usage: ./scripts/test_runid_gating.sh [API_BASE]

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
echo "🧪 run_id Gating Tests (Instant Complete Fix)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Base: $API_BASE"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Start Returns run_id
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 1: Start endpoint returns run_id"

START_RESPONSE=$(curl -sf -X POST "${API_BASE}/ops/black_swan" 2>/dev/null || echo "{}")

if echo "$START_RESPONSE" | jq -e '.ok == true' >/dev/null 2>&1; then
    RUN_ID=$(echo "$START_RESPONSE" | jq -r '.run_id // ""')
    
    if [[ -n "$RUN_ID" ]] && [[ "$RUN_ID" != "null" ]]; then
        log_pass "Start returned run_id: $RUN_ID"
    else
        log_fail "Start response missing run_id"
        exit 1
    fi
else
    log_fail "Failed to start test"
    echo "  Response: $START_RESPONSE"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: No Instant Complete (<5s)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 2: No instant complete within 5 seconds"

sleep 3

STATUS_RESPONSE=$(curl -sf "${API_BASE}/ops/black_swan/status" 2>/dev/null || echo "{}")

PHASE=$(echo "$STATUS_RESPONSE" | jq -r '.phase // "unknown"')
PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress // -1')
STATUS_RUN_ID=$(echo "$STATUS_RESPONSE" | jq -r '.run_id // ""')

echo "  After 3s: phase=$PHASE, progress=$PROGRESS%, run_id=$STATUS_RUN_ID"

if [[ "$STATUS_RUN_ID" == "$RUN_ID" ]]; then
    log_pass "Status run_id matches started run_id"
else
    log_fail "Status run_id mismatch: $STATUS_RUN_ID != $RUN_ID"
fi

if [[ "$PHASE" != "complete" ]]; then
    log_pass "Not showing complete after <5s (phase=$PHASE)"
else
    log_fail "Showing complete too early! (instant complete bug)"
fi

if [[ "$PROGRESS" -lt 100 ]]; then
    log_pass "Progress not at 100% yet (progress=$PROGRESS%)"
else
    log_fail "Progress at 100% too early!"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: Concurrent Start (409)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 3: Concurrent start returns 409"

HTTP_CODE=$(curl -sf -w "%{http_code}" -o /tmp/concurrent_test.json -X POST "${API_BASE}/ops/black_swan" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "409" ]]; then
    log_pass "Concurrent start returned 409 (Already running)"
    
    CONCURRENT_RESPONSE=$(cat /tmp/concurrent_test.json)
    CONCURRENT_RUN_ID=$(echo "$CONCURRENT_RESPONSE" | jq -r '.run_id // ""')
    
    if [[ "$CONCURRENT_RUN_ID" == "$RUN_ID" ]]; then
        log_pass "409 response includes original run_id"
    else
        log_fail "409 response run_id mismatch"
    fi
else
    log_fail "Concurrent start did not return 409 (got $HTTP_CODE)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: Fake run_id Update (Rejected)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 4: Progress update with wrong run_id is rejected"

FAKE_UPDATE=$(curl -sf -X POST "${API_BASE}/ops/black_swan/progress" \
    -H "Content-Type: application/json" \
    -d '{"run_id":"WRONG-ID","phase":"complete","progress":100,"message":"fake"}' \
    2>/dev/null || echo "{}")

if echo "$FAKE_UPDATE" | jq -e '.ok == false' >/dev/null 2>&1; then
    log_pass "Fake run_id update rejected"
    
    ERROR_MSG=$(echo "$FAKE_UPDATE" | jq -r '.error // ""')
    if [[ "$ERROR_MSG" == *"run_id mismatch"* ]]; then
        log_pass "Error message indicates run_id mismatch"
    else
        log_fail "Error message doesn't mention run_id: $ERROR_MSG"
    fi
else
    log_fail "Fake run_id update was not rejected!"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: Report Endpoint State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info "TEST 5: Report endpoint includes state and gates by run_id"

REPORT_RESPONSE=$(curl -sf "${API_BASE}/ops/black_swan" 2>/dev/null || echo "{}")

if echo "$REPORT_RESPONSE" | jq -e '.state' >/dev/null 2>&1; then
    log_pass "Report endpoint includes state object"
    
    STATE_RUN_ID=$(echo "$REPORT_RESPONSE" | jq -r '.state.run_id // ""')
    HAS_REPORT=$(echo "$REPORT_RESPONSE" | jq -e '.report != null' >/dev/null 2>&1 && echo "true" || echo "false")
    
    if [[ "$STATE_RUN_ID" == "$RUN_ID" ]]; then
        log_pass "State run_id matches current run"
    else
        log_fail "State run_id mismatch: $STATE_RUN_ID != $RUN_ID"
    fi
    
    if [[ "$HAS_REPORT" == "false" ]]; then
        log_pass "No report shown for in-progress test (correct gating)"
    else
        log_fail "Report shown for in-progress test (should be gated)"
    fi
else
    log_fail "Report endpoint missing state object"
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
    echo "✅ All run_id gating tests passed!"
    echo ""
    echo "Fix verified:"
    echo "  ✓ run_id returned on start"
    echo "  ✓ No instant complete (<5s)"
    echo "  ✓ Concurrent starts return 409"
    echo "  ✓ Fake run_id updates rejected"
    echo "  ✓ Report endpoint gates by run_id"
    echo ""
    echo "Note: Test is still running. You may want to wait for completion"
    echo "or stop the test manually."
    echo ""
    exit 0
else
    echo "❌ Some run_id gating tests failed"
    echo ""
    echo "Review the output above to identify issues."
    echo ""
    exit 1
fi


