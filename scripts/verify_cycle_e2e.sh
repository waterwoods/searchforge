#!/bin/bash
# 🔍 Cycle E2E Verification Script
# 验证 cycle_sec 和 total_cycles 从 UI→API→Worker→Status 的完整链路

set -e

echo "======================================"
echo "🔍 Cycle E2E Verification Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
FAIL_COUNT=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASS_COUNT++))
}

fail_test() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

warn_test() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

# Check if server is running
echo "📡 Checking if API server is running..."
if ! curl -s http://localhost:28002/health > /dev/null 2>&1; then
    echo -e "${RED}✗ API server not running on port 28002${NC}"
    echo "Please start the server first: cd services/fiqa_api && python app.py"
    exit 1
fi
pass_test "API server is running"
echo ""

# Test 1: Check /auto/status structure
echo "Test 1: Verify /auto/status returns cycle fields"
echo "----------------------------------------------"
STATUS=$(curl -s http://localhost:28002/auto/status)

if echo "$STATUS" | jq -e '.cycle_sec' > /dev/null 2>&1; then
    pass_test "cycle_sec field exists"
else
    fail_test "cycle_sec field missing"
fi

if echo "$STATUS" | jq -e '.total_cycles' > /dev/null 2>&1; then
    pass_test "total_cycles field exists (can be null)"
else
    fail_test "total_cycles field missing"
fi

if echo "$STATUS" | jq -e '.total_cycles_label' > /dev/null 2>&1; then
    pass_test "total_cycles_label field exists"
else
    fail_test "total_cycles_label field missing"
fi

if echo "$STATUS" | jq -e '.completed_cycles' > /dev/null 2>&1; then
    pass_test "completed_cycles field exists"
else
    fail_test "completed_cycles field missing"
fi

if echo "$STATUS" | jq -e '.desired_cycle_sec' > /dev/null 2>&1; then
    pass_test "desired_cycle_sec field exists"
else
    fail_test "desired_cycle_sec field missing"
fi

echo ""

# Test 2: Parameter validation - cycle_sec too short
echo "Test 2: Verify parameter guard (cycle_sec < duration + 5)"
echo "----------------------------------------------------------"
RESPONSE=$(curl -s -X POST "http://localhost:28002/auto/start?cycle=25&duration=30&qps=6&total_cycles=1")

if echo "$RESPONSE" | jq -e '.ok == false' > /dev/null 2>&1; then
    pass_test "API rejects cycle_sec < duration + 5"
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error')
    if echo "$ERROR_MSG" | grep -qi "too short"; then
        pass_test "Error message mentions 'too short'"
    else
        fail_test "Error message doesn't mention 'too short': $ERROR_MSG"
    fi
else
    fail_test "API should reject cycle_sec=25 with duration=30 (need >= 35)"
fi

echo ""

# Test 3: Start with valid params and verify state
echo "Test 3: Start with valid params (cycle=40, duration=30, total=2)"
echo "-----------------------------------------------------------------"

# Stop any existing traffic
curl -s -X POST http://localhost:28002/auto/stop > /dev/null
sleep 0.5

# Start with valid params
START_RESPONSE=$(curl -s -X POST "http://localhost:28002/auto/start?cycle=40&duration=30&qps=6&total_cycles=2")

if echo "$START_RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    pass_test "Start request accepted"
    
    # Wait a moment for state to update
    sleep 0.5
    
    # Check status
    STATUS=$(curl -s http://localhost:28002/auto/status)
    
    CYCLE_SEC=$(echo "$STATUS" | jq -r '.cycle_sec')
    DURATION=$(echo "$STATUS" | jq -r '.duration')
    TOTAL_CYCLES=$(echo "$STATUS" | jq -r '.total_cycles')
    ENABLED=$(echo "$STATUS" | jq -r '.enabled')
    
    if [ "$CYCLE_SEC" = "40" ]; then
        pass_test "cycle_sec = 40 (correct)"
    else
        fail_test "cycle_sec = $CYCLE_SEC (expected 40)"
    fi
    
    if [ "$DURATION" = "30" ]; then
        pass_test "duration = 30 (correct)"
    else
        fail_test "duration = $DURATION (expected 30)"
    fi
    
    if [ "$TOTAL_CYCLES" = "2" ]; then
        pass_test "total_cycles = 2 (correct)"
    else
        fail_test "total_cycles = $TOTAL_CYCLES (expected 2)"
    fi
    
    if [ "$ENABLED" = "true" ]; then
        pass_test "Worker is enabled"
    else
        fail_test "Worker should be enabled, got: $ENABLED"
    fi
    
    # Stop traffic for next test
    curl -s -X POST http://localhost:28002/auto/stop > /dev/null
    sleep 0.5
else
    fail_test "Start request failed: $(echo "$START_RESPONSE" | jq -r '.error // "unknown"')"
fi

echo ""

# Test 4: Start with infinite cycles (total_cycles=0 or omitted)
echo "Test 4: Start with infinite cycles (total_cycles=0)"
echo "-----------------------------------------------------"

START_RESPONSE=$(curl -s -X POST "http://localhost:28002/auto/start?cycle=40&duration=30&qps=6&total_cycles=0")

if echo "$START_RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    pass_test "Start with total_cycles=0 accepted"
    
    sleep 0.5
    STATUS=$(curl -s http://localhost:28002/auto/status)
    
    TOTAL_CYCLES=$(echo "$STATUS" | jq -r '.total_cycles')
    TOTAL_LABEL=$(echo "$STATUS" | jq -r '.total_cycles_label')
    
    if [ "$TOTAL_CYCLES" = "null" ]; then
        pass_test "total_cycles = null (infinite)"
    else
        fail_test "total_cycles should be null, got: $TOTAL_CYCLES"
    fi
    
    if [ "$TOTAL_LABEL" = "∞" ]; then
        pass_test "total_cycles_label = ∞ (correct)"
    else
        fail_test "total_cycles_label = $TOTAL_LABEL (expected ∞)"
    fi
    
    # Stop traffic
    curl -s -X POST http://localhost:28002/auto/stop > /dev/null
    sleep 0.5
else
    fail_test "Start with infinite cycles failed"
fi

echo ""

# Test 5: Check /auto/debug endpoint
echo "Test 5: Verify /auto/debug returns cycle information"
echo "-----------------------------------------------------"

DEBUG=$(curl -s http://localhost:28002/auto/debug)

if echo "$DEBUG" | jq -e '.completed_cycles' > /dev/null 2>&1; then
    pass_test "/auto/debug has completed_cycles"
else
    fail_test "/auto/debug missing completed_cycles"
fi

if echo "$DEBUG" | jq -e '.total_cycles' > /dev/null 2>&1; then
    pass_test "/auto/debug has total_cycles"
else
    fail_test "/auto/debug missing total_cycles"
fi

if echo "$DEBUG" | jq -e '.runtime_params' > /dev/null 2>&1; then
    pass_test "/auto/debug has runtime_params"
    
    if echo "$DEBUG" | jq -e '.runtime_params.cycle_sec' > /dev/null 2>&1; then
        pass_test "runtime_params.cycle_sec exists"
    else
        fail_test "runtime_params.cycle_sec missing"
    fi
else
    fail_test "/auto/debug missing runtime_params"
fi

if echo "$DEBUG" | jq -e '.desired_params' > /dev/null 2>&1; then
    pass_test "/auto/debug has desired_params"
    
    if echo "$DEBUG" | jq -e '.desired_params.cycle_sec' > /dev/null 2>&1; then
        pass_test "desired_params.cycle_sec exists"
    else
        fail_test "desired_params.cycle_sec missing"
    fi
    
    if echo "$DEBUG" | jq -e '.desired_params.total_cycles' > /dev/null 2>&1; then
        pass_test "desired_params.total_cycles exists"
    else
        fail_test "desired_params.total_cycles missing"
    fi
else
    fail_test "/auto/debug missing desired_params"
fi

echo ""

# Test 6: Verify debounce guard
echo "Test 6: Verify debounce guard (rapid start requests)"
echo "-----------------------------------------------------"

# Stop first
curl -s -X POST http://localhost:28002/auto/stop > /dev/null
sleep 0.5

# Send two rapid start requests
START1=$(curl -s -X POST "http://localhost:28002/auto/start?cycle=40&duration=30&qps=6&total_cycles=1")
START2=$(curl -s -X POST "http://localhost:28002/auto/start?cycle=40&duration=30&qps=6&total_cycles=1")

OK1=$(echo "$START1" | jq -r '.ok')
OK2=$(echo "$START2" | jq -r '.ok')

if [ "$OK1" = "true" ]; then
    pass_test "First start request succeeded"
else
    warn_test "First start request failed (maybe already running?)"
fi

if [ "$OK2" = "false" ]; then
    ERROR2=$(echo "$START2" | jq -r '.error // ""')
    if echo "$ERROR2" | grep -qi "debounce"; then
        pass_test "Second request blocked by debounce guard"
    else
        warn_test "Second request failed, but not due to debounce: $ERROR2"
    fi
else
    warn_test "Second request succeeded (debounce may not be working, or was too slow)"
fi

# Cleanup
curl -s -X POST http://localhost:28002/auto/stop > /dev/null
sleep 0.5

echo ""

# Test 7: Verify cycle_sec and total_cycles are separate
echo "Test 7: Verify cycle_sec and total_cycles are independent"
echo "----------------------------------------------------------"

START_RESPONSE=$(curl -s -X POST "http://localhost:28002/auto/start?cycle=50&duration=30&qps=6&total_cycles=3")

if echo "$START_RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    sleep 0.5
    STATUS=$(curl -s http://localhost:28002/auto/status)
    
    CYCLE_SEC=$(echo "$STATUS" | jq -r '.cycle_sec')
    TOTAL_CYCLES=$(echo "$STATUS" | jq -r '.total_cycles')
    
    if [ "$CYCLE_SEC" = "50" ] && [ "$TOTAL_CYCLES" = "3" ]; then
        pass_test "cycle_sec=50 and total_cycles=3 are correctly separated"
    else
        fail_test "cycle_sec=$CYCLE_SEC, total_cycles=$TOTAL_CYCLES (expected 50 and 3)"
    fi
    
    if [ "$CYCLE_SEC" != "$TOTAL_CYCLES" ]; then
        pass_test "cycle_sec ≠ total_cycles (they are different concepts)"
    else
        fail_test "cycle_sec equals total_cycles (should be different)"
    fi
    
    curl -s -X POST http://localhost:28002/auto/stop > /dev/null
else
    fail_test "Start with cycle=50, total=3 failed"
fi

echo ""
echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo -e "${GREEN}✓ Passed${NC}: $PASS_COUNT"
echo -e "${RED}✗ Failed${NC}: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open http://localhost:28002 in browser"
    echo "2. Check that UI label shows 'CYCLE (sec)' and 'TOTAL'"
    echo "3. Try setting CYCLE=40, DURATION=30, TOTAL=2 and verify badge shows 'Cycle 0/2'"
    echo "4. Start traffic and verify it completes 2 cycles then stops"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi

