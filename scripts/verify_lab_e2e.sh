#!/bin/bash
# Lab Dashboard E2E Verification Script
# Verifies all Lab endpoints and main panel endpoints

set -e

BACKEND_URL="http://localhost:8011"
PASS="\033[0;32m✓\033[0m"
FAIL="\033[0;31m✗\033[0m"
INFO="\033[0;36m→\033[0m"

echo "========================================================================"
echo "LAB DASHBOARD E2E VERIFICATION"
echo "========================================================================"
echo ""

# Counter for passed/failed tests
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_field="$3"
    
    echo -e "${INFO} Testing: $name"
    echo "   URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        if echo "$body" | jq -e "$expected_field" > /dev/null 2>&1; then
            echo -e "   ${PASS} Status: $http_code | Field '$expected_field' present"
            ((PASSED++))
        else
            echo -e "   ${FAIL} Status: $http_code | Field '$expected_field' MISSING"
            echo "   Response: $(echo $body | jq -c . 2>/dev/null || echo $body)"
            ((FAILED++))
        fi
    else
        echo -e "   ${FAIL} Status: $http_code (expected 200)"
        echo "   Response: $(echo $body | jq -c . 2>/dev/null || echo $body)"
        ((FAILED++))
    fi
    echo ""
}

# Health Endpoints
echo "──────────────────────────────────────────────────────────────────────"
echo "HEALTH ENDPOINTS"
echo "──────────────────────────────────────────────────────────────────────"
test_endpoint "Health Check" "$BACKEND_URL/healthz" ".ok"
test_endpoint "Readiness Check" "$BACKEND_URL/readyz" ".data_sources.redis"

# Lab Dashboard Endpoints
echo "──────────────────────────────────────────────────────────────────────"
echo "LAB DASHBOARD ENDPOINTS"
echo "──────────────────────────────────────────────────────────────────────"
test_endpoint "Lab Config" "$BACKEND_URL/api/lab/config" ".health.redis.ok"
test_endpoint "Lab Status" "$BACKEND_URL/ops/lab/status" ".phase"

# Quiet Mode Endpoints
echo "──────────────────────────────────────────────────────────────────────"
echo "QUIET MODE ENDPOINTS"
echo "──────────────────────────────────────────────────────────────────────"
test_endpoint "Quiet Mode Status" "$BACKEND_URL/ops/quiet_mode/status" ".ok"

# Main Panel Endpoints
echo "──────────────────────────────────────────────────────────────────────"
echo "MAIN PANEL ENDPOINTS"
echo "──────────────────────────────────────────────────────────────────────"
test_endpoint "Ops Summary" "$BACKEND_URL/ops/summary" ".window60s"
test_endpoint "Force Status" "$BACKEND_URL/ops/force_status" ".effective_params"
test_endpoint "Black Swan Status" "$BACKEND_URL/ops/black_swan/status" ".phase"

# Results Summary
echo "========================================================================"
echo "TEST RESULTS"
echo "========================================================================"
echo -e "Passed: ${PASS} $PASSED"
echo -e "Failed: ${FAIL} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${PASS} All tests passed!"
    echo ""
    echo "Access Lab Dashboard at:"
    echo "  → http://localhost:3000/lab"
    echo ""
    exit 0
else
    echo -e "${FAIL} Some tests failed. Check output above."
    exit 1
fi

