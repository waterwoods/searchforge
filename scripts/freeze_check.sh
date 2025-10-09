#!/bin/bash
# Freeze Check - Comprehensive API Validation Orchestrator
set -e

echo "🧊 FIQA API Freeze Check"
echo "======================================================"
echo "This script validates the frozen API contract"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if service is already running
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Service already running on port 8080${NC}"
    ALREADY_RUNNING=1
else
    echo "▶ Starting FIQA API service..."
    ./launch.sh > /tmp/fiqa_launch.log 2>&1 &
    LAUNCH_PID=$!
    ALREADY_RUNNING=0
    
    # Wait for service to be ready
    echo "  Waiting for service to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Service ready after ${i}s"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Service failed to start after 30s${NC}"
            cat /tmp/fiqa_launch.log
            exit 1
        fi
    done
    echo ""
fi

# Cleanup function
cleanup() {
    if [ "$ALREADY_RUNNING" -eq 0 ]; then
        echo ""
        echo "🛑 Shutting down test service..."
        pkill -P $LAUNCH_PID 2>/dev/null || true
        kill $LAUNCH_PID 2>/dev/null || true
        sleep 2
    fi
}
trap cleanup EXIT

# Run contract validation
echo "📋 Running Contract Validation..."
echo "------------------------------------------------------"
python3 scripts/contract_check.py
CONTRACT_RESULT=$?
echo ""

# Run smoke load test
echo "🔥 Running Smoke Load Test..."
echo "------------------------------------------------------"
python3 scripts/smoke_load.py
SMOKE_RESULT=$?
echo ""

# Final summary
echo "======================================================"
echo "📊 FREEZE CHECK SUMMARY"
echo "======================================================"

if [ $CONTRACT_RESULT -eq 0 ]; then
    echo -e "[CONTRACT] ${GREEN}✓ PASS${NC} - All endpoint contracts validated"
else
    echo -e "[CONTRACT] ${RED}✗ FAIL${NC} - Contract validation failed"
fi

if [ $SMOKE_RESULT -eq 0 ]; then
    echo -e "[SANITY]   ${GREEN}✓ PASS${NC} - Load test passed (success_rate≥90%, P95<300ms)"
else
    echo -e "[SANITY]   ${RED}✗ FAIL${NC} - Load test failed"
fi

echo ""

# Overall result
if [ $CONTRACT_RESULT -eq 0 ] && [ $SMOKE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ FREEZE CHECK PASSED - API is stable and ready${NC}"
    exit 0
else
    echo -e "${RED}❌ FREEZE CHECK FAILED - Review failures above${NC}"
    exit 1
fi

