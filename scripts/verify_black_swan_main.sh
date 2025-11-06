#!/bin/bash
# Black Swan E2E Verification Script
# Tests that Black Swan runs successfully from idle → complete on app_main

set -e

BASE_URL="http://localhost:8011"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Black Swan E2E Verification (app_main)"
echo "======================================"
echo ""

# 1. Check app_main is running
echo -n "1. Checking app_main health... "
HEALTH=$(curl -s ${BASE_URL}/healthz | jq -r '.ok')
if [ "$HEALTH" != "true" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "   app_main is not running or not healthy"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# 2. POST to start Black Swan test
echo -n "2. Starting Black Swan test (mode B)... "
RESPONSE=$(curl -s -X POST ${BASE_URL}/ops/black_swan \
  -H "Content-Type: application/json" \
  -d '{"mode":"B","params":{"warmup_duration":5,"baseline_duration":5,"trip_duration":10,"recovery_duration":10}}')

OK=$(echo "$RESPONSE" | jq -r '.ok')
STATUS=$(echo "$RESPONSE" | jq -r '.status')

if [ "$OK" != "true" ] || [ "$STATUS" != "starting" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "   Response: $RESPONSE"
    exit 1
fi
echo -e "${GREEN}OK${NC} (202 with ok:true, status:starting)"

# 3. Wait and poll until phase changes from idle
echo -n "3. Waiting for phase to start (max 10s)... "
PHASE="idle"
for i in {1..10}; do
    sleep 1
    STATUS_RESP=$(curl -s ${BASE_URL}/ops/black_swan/status)
    PHASE=$(echo "$STATUS_RESP" | jq -r '.phase')
    
    if [ "$PHASE" != "idle" ] && [ "$PHASE" != "null" ]; then
        echo -e "${GREEN}OK${NC} (phase: $PHASE)"
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo -e "${RED}FAIL${NC}"
        echo "   Phase still idle after 10s"
        echo "   Status: $STATUS_RESP"
        exit 1
    fi
done

# 4. Monitor progression through all phases
echo "4. Monitoring phase progression..."
LAST_PHASE=""
START_TIME=$(date +%s)

while true; do
    sleep 2
    STATUS_RESP=$(curl -s ${BASE_URL}/ops/black_swan/status)
    PHASE=$(echo "$STATUS_RESP" | jq -r '.phase')
    PROGRESS=$(echo "$STATUS_RESP" | jq -r '.progress')
    COUNT=$(echo "$STATUS_RESP" | jq -r '.metrics.count // 0')
    
    # Log phase changes
    if [ "$PHASE" != "$LAST_PHASE" ]; then
        ELAPSED=$(($(date +%s) - START_TIME))
        echo "   [${ELAPSED}s] Phase: $PHASE (progress: $PROGRESS%, count: $COUNT)"
        LAST_PHASE="$PHASE"
    fi
    
    # Check for completion
    if [ "$PHASE" == "complete" ]; then
        echo -e "   ${GREEN}✅ Test completed successfully${NC}"
        break
    fi
    
    # Check for error
    if [ "$PHASE" == "error" ]; then
        echo -e "   ${RED}❌ Test failed${NC}"
        ERROR=$(echo "$STATUS_RESP" | jq -r '.error')
        echo "   Error: $ERROR"
        exit 1
    fi
    
    # Timeout after 2 minutes
    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -gt 120 ]; then
        echo -e "   ${RED}TIMEOUT${NC} (test took > 2 min)"
        exit 1
    fi
done

# 5. Verify report is available
echo -n "5. Checking final report... "
REPORT=$(curl -s ${BASE_URL}/ops/black_swan/report)
REPORT_OK=$(echo "$REPORT" | jq -r '.ok')
SOURCE=$(echo "$REPORT" | jq -r '.source')

if [ "$REPORT_OK" != "true" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "   Report not available"
    echo "   Response: $REPORT"
    exit 1
fi
echo -e "${GREEN}OK${NC} (source: $SOURCE)"

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "======================================"
echo "Black Swan test completed successfully:"
echo "  - POST returned 202"
echo "  - Phase progressed from idle → complete"
echo "  - Report available"
echo ""
