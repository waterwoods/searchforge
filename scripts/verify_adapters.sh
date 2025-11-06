#!/usr/bin/env bash
# Adapter Verification Script
# Tests all endpoints and validates adapter transformations

set -e

BASE_URL="http://localhost:8011"
REPORT_FILE="reports/ADAPTERS_VERIFY_MINI.txt"
PROBE_SCRIPT="scripts/adapter_probe.mjs"

echo "========================================"
echo "Adapter Verification Script"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to test endpoint
test_endpoint() {
    local path=$1
    local name=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing ${name}... "
    
    if curl -s -f -m 5 "${BASE_URL}${path}" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to test JSON validity
test_json() {
    local path=$1
    local name=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Validating JSON for ${name}... "
    
    if curl -s -f -m 5 "${BASE_URL}${path}" | jq -e . > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test all endpoints
echo "=== Endpoint Availability ==="
test_endpoint "/ops/verify" "verify"
test_endpoint "/ops/force_status" "force_status"
test_endpoint "/ops/black_swan/config" "black_swan_config"
test_endpoint "/ops/black_swan/status" "black_swan_status"
test_endpoint "/ops/qdrant/stats" "qdrant_stats"
test_endpoint "/ops/qa/feed?limit=20" "qa_feed"

echo ""
echo "=== JSON Validation ==="
test_json "/ops/verify" "verify"
test_json "/ops/force_status" "force_status"
test_json "/ops/black_swan/config" "black_swan_config"
test_json "/ops/black_swan/status" "black_swan_status"
test_json "/ops/qdrant/stats" "qdrant_stats"
test_json "/ops/qa/feed?limit=20" "qa_feed"

echo ""
echo "=== Adapter Transformation Tests ==="

# Run Node probe script
if [ -f "$PROBE_SCRIPT" ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Running adapter probe... "
    
    if node "$PROBE_SCRIPT" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (probe script not found)"
fi

echo ""
echo "=== Summary ==="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

# Generate report
echo "Generating report: $REPORT_FILE"
mkdir -p reports
node "$PROBE_SCRIPT" > "$REPORT_FILE" 2>&1

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}SOME TESTS FAILED${NC}"
    exit 1
fi

