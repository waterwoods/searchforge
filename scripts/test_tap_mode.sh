#!/usr/bin/env bash
#
# test_tap_mode.sh - DEPRECATED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️  DEPRECATED: This script is replaced by test_metrics_quick.sh
# Please use: bash scripts/test_metrics_quick.sh
# Reason: Migration to /api/* endpoints only (no /ops/* dependencies)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# OLD DESCRIPTION: Validate Live Tap Mode implementation
#

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

API_BASE="${API_BASE:-${APP_DEMO_URL:-http://localhost:8001}}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[TEST]${NC} $*"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_error() { echo -e "${RED}[FAIL]${NC} $*"; }

PASSED=0
FAILED=0

test_case() {
    local name=$1
    local result=$2
    
    if [ "$result" == "0" ]; then
        log_success "$name"
        ((PASSED++)) || true
    else
        log_error "$name"
        ((FAILED++)) || true
    fi
}

log_info "Testing Live Tap Mode Implementation"
echo ""

# Test 1: Check if tap health endpoint exists
log_info "Test 1: Tap health endpoint"
if curl -sf "${API_BASE}/ops/tap/health" > /dev/null; then
    HEALTH=$(curl -sf "${API_BASE}/ops/tap/health")
    ENABLED=$(echo "$HEALTH" | jq -r '.enabled')
    
    if [ "$ENABLED" == "true" ]; then
        test_case "Tap enabled and health endpoint responding" 0
        
        # Show stats
        BACKEND_LOGS=$(echo "$HEALTH" | jq -r '.stats.backend_logs')
        EVENT_LOGS=$(echo "$HEALTH" | jq -r '.stats.event_logs')
        OVERHEAD=$(echo "$HEALTH" | jq -r '.stats.overhead_ms_avg')
        
        log_info "  Backend logs: $BACKEND_LOGS"
        log_info "  Event logs: $EVENT_LOGS"
        log_info "  Avg overhead: ${OVERHEAD}ms"
    else
        log_error "Tap not enabled (set TAP_ENABLED=true)"
        test_case "Tap enabled" 1
    fi
else
    test_case "Tap health endpoint exists" 1
fi

echo ""

# Test 2: Check if tap/tail endpoint works
log_info "Test 2: Tap tail endpoint"
if curl -sf "${API_BASE}/ops/tap/tail?file=events&n=10" > /dev/null; then
    TAIL_RESULT=$(curl -sf "${API_BASE}/ops/tap/tail?file=events&n=10")
    TAIL_OK=$(echo "$TAIL_RESULT" | jq -r '.ok')
    TAIL_COUNT=$(echo "$TAIL_RESULT" | jq -r '.count')
    
    if [ "$TAIL_OK" == "true" ]; then
        test_case "Tap tail endpoint returns events (count: $TAIL_COUNT)" 0
    else
        test_case "Tap tail endpoint returns ok=true" 1
    fi
else
    test_case "Tap tail endpoint exists" 1
fi

echo ""

# Test 3: Check if tap/timeline endpoint works
log_info "Test 3: Tap timeline endpoint"
if curl -sf "${API_BASE}/ops/tap/timeline?n=10" > /dev/null; then
    TIMELINE_RESULT=$(curl -sf "${API_BASE}/ops/tap/timeline?n=10")
    TIMELINE_OK=$(echo "$TIMELINE_RESULT" | jq -r '.ok')
    TIMELINE_COUNT=$(echo "$TIMELINE_RESULT" | jq -r '.count')
    
    if [ "$TIMELINE_OK" == "true" ]; then
        test_case "Tap timeline endpoint works (count: $TIMELINE_COUNT)" 0
    else
        test_case "Tap timeline endpoint returns ok=true" 1
    fi
else
    test_case "Tap timeline endpoint exists" 1
fi

echo ""

# Test 4: Send a test event
log_info "Test 4: Send custom tap event"
TEST_RUN_ID="test-$(date +%s)"
if curl -sf -X POST "${API_BASE}/ops/tap/event" \
    -H "Content-Type: application/json" \
    -d "{\"client\":\"test\",\"event\":\"test_event\",\"run_id\":\"${TEST_RUN_ID}\",\"message\":\"Test from test_tap_mode.sh\"}" \
    > /dev/null; then
    
    test_case "POST /ops/tap/event accepts custom events" 0
    
    # Wait a bit and verify event appears in tail
    sleep 1
    RECENT_EVENTS=$(curl -sf "${API_BASE}/ops/tap/tail?file=events&n=5")
    if echo "$RECENT_EVENTS" | jq -e ".entries[] | select(.run_id==\"${TEST_RUN_ID}\")" > /dev/null; then
        test_case "Custom event appears in tail" 0
    else
        test_case "Custom event appears in tail" 1
    fi
else
    test_case "POST /ops/tap/event works" 1
fi

echo ""

# Test 5: Check log files exist (if tap is enabled)
log_info "Test 5: Log files"
if [ "$ENABLED" == "true" ]; then
    # Find project root (2 levels up from scripts/)
    SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
    LOGS_DIR="$PROJECT_ROOT/logs"
    
    if [ -f "$LOGS_DIR/tap_backend.jsonl" ]; then
        BACKEND_SIZE=$(wc -c < "$LOGS_DIR/tap_backend.jsonl" | tr -d ' ')
        test_case "tap_backend.jsonl exists (${BACKEND_SIZE} bytes)" 0
    else
        test_case "tap_backend.jsonl exists" 1
    fi
    
    if [ -f "$LOGS_DIR/tap_events.jsonl" ]; then
        EVENTS_SIZE=$(wc -c < "$LOGS_DIR/tap_events.jsonl" | tr -d ' ')
        test_case "tap_events.jsonl exists (${EVENTS_SIZE} bytes)" 0
    else
        test_case "tap_events.jsonl exists" 1
    fi
else
    log_info "  Skipped (tap not enabled)"
fi

echo ""

# Test 6: Verify overhead is within target
log_info "Test 6: Performance overhead"
if [ "$ENABLED" == "true" ] && [ "$OVERHEAD" != "null" ]; then
    # Check if overhead is less than 2ms
    if awk -v overhead="$OVERHEAD" 'BEGIN {exit !(overhead < 2.0)}'; then
        test_case "Overhead within target (<2ms): ${OVERHEAD}ms" 0
    else
        test_case "Overhead within target (<2ms): ${OVERHEAD}ms" 1
    fi
else
    log_info "  Skipped (no overhead data)"
fi

echo ""

# Summary
log_info "================================"
log_info "Test Summary"
log_info "================================"
log_success "Passed: $PASSED"
log_error "Failed: $FAILED"

if [ "$FAILED" -eq 0 ]; then
    log_success "All tests passed! ✅"
    echo ""
    log_info "Tap Mode is working correctly."
    log_info "To view live timeline:"
    echo "  curl ${API_BASE}/ops/tap/tail?file=events&n=100 | jq"
    exit 0
else
    log_error "Some tests failed."
    echo ""
    log_info "Troubleshooting:"
    echo "  1. Check TAP_ENABLED=true in environment"
    echo "  2. Restart API server: python services/fiqa_api/app_v2.py"
    echo "  3. Check logs/ directory has write permissions"
    echo "  4. Review full docs: LIVE_TAP_MODE.md"
    exit 1
fi

