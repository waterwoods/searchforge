#!/bin/bash
# verify_lab_backend.sh - Lab Backend Verification
# =================================================
# Quick verification script for Lab Dashboard backend endpoints.
#
# Checks:
# 1. GET /api/lab/config - Configuration and health
# 2. POST /ops/lab/prewarm - Prewarm capability
# 3. POST /ops/lab/start - Experiment start (dry-run)
# 4. GET /ops/lab/status - Status endpoint
# 5. GET /ops/lab/report - Report endpoint
# 6. Core modules self-test
#
# Output: reports/LAB_BACKEND_VERIFY.txt (≤50 lines)

set -e

BASE_URL="${BASE_URL:-http://localhost:8011}"
REPORT_FILE="reports/LAB_BACKEND_VERIFY.txt"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize report
mkdir -p reports
cat > "$REPORT_FILE" <<EOF
==================================================================
LAB BACKEND VERIFICATION REPORT
==================================================================
Date: $(date +"%Y-%m-%d %H:%M:%S")
Target: $BASE_URL

EOF

log() {
    echo "$1" | tee -a "$REPORT_FILE"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    echo "[TEST] $1" >> "$REPORT_FILE"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    echo "[PASS] $1" >> "$REPORT_FILE"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    echo "[FAIL] $1" >> "$REPORT_FILE"
}

log_info() {
    echo -e "${BLUE}  →${NC} $1"
    echo "  → $1" >> "$REPORT_FILE"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}LAB BACKEND VERIFICATION${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Test 1: Core modules self-test
log_test "Test 1: Core Modules Self-Test"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

# Test flow_control.py
if [ -f "backend_core/flow_control.py" ]; then
    if python3 backend_core/flow_control.py > /dev/null 2>&1; then
        log_pass "flow_control.py self-test passed"
    else
        log_fail "flow_control.py self-test failed"
    fi
else
    log_fail "flow_control.py not found"
fi

# Test routing_policy.py
if [ -f "backend_core/routing_policy.py" ]; then
    if python3 backend_core/routing_policy.py > /dev/null 2>&1; then
        log_pass "routing_policy.py self-test passed"
    else
        log_fail "routing_policy.py self-test failed"
    fi
else
    log_fail "routing_policy.py not found"
fi

echo >> "$REPORT_FILE"

# Test 2: GET /api/lab/config
log_test "Test 2: GET /api/lab/config"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

RESPONSE=$(curl -s "$BASE_URL/api/lab/config" || echo '{"ok":false}')

if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    log_pass "Config endpoint accessible"
    
    # Check tabs
    if echo "$RESPONSE" | jq -e '.tabs | length == 2' > /dev/null 2>&1; then
        log_pass "Two experiment tabs defined"
    else
        log_fail "Expected 2 tabs, got: $(echo "$RESPONSE" | jq '.tabs | length')"
    fi
    
    # Check health fields
    if echo "$RESPONSE" | jq -e '.health.redis' > /dev/null 2>&1; then
        REDIS_OK=$(echo "$RESPONSE" | jq -r '.health.redis.ok')
        log_info "Redis: $REDIS_OK"
    fi
    
    if echo "$RESPONSE" | jq -e '.health.qdrant' > /dev/null 2>&1; then
        QDRANT_OK=$(echo "$RESPONSE" | jq -r '.health.qdrant.ok')
        log_info "Qdrant: $QDRANT_OK"
    fi
    
else
    log_fail "Config endpoint failed or returned error"
fi

echo >> "$REPORT_FILE"

# Test 3: POST /ops/lab/prewarm
log_test "Test 3: POST /ops/lab/prewarm"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

RESPONSE=$(curl -s -X POST "$BASE_URL/ops/lab/prewarm" \
    -H "Content-Type: application/json" \
    -d '{"duration_sec": 1}')

if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    log_pass "Prewarm endpoint accessible"
    log_info "Status: $(echo "$RESPONSE" | jq -r '.status')"
else
    log_fail "Prewarm endpoint failed"
fi

echo >> "$REPORT_FILE"

# Test 4: GET /ops/lab/status (without running experiment)
log_test "Test 4: GET /ops/lab/status"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

RESPONSE=$(curl -s "$BASE_URL/ops/lab/status")

if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
    log_pass "Status endpoint accessible"
    
    RUNNING=$(echo "$RESPONSE" | jq -r '.running')
    PHASE=$(echo "$RESPONSE" | jq -r '.phase')
    
    log_info "Running: $RUNNING"
    log_info "Phase: $PHASE"
    
    # Check for required fields
    if echo "$RESPONSE" | jq -e '.running' > /dev/null 2>&1; then
        log_pass "Status has 'running' field"
    fi
    
    if echo "$RESPONSE" | jq -e '.phase' > /dev/null 2>&1; then
        log_pass "Status has 'phase' field"
    fi
    
else
    log_fail "Status endpoint failed"
fi

echo >> "$REPORT_FILE"

# Test 5: POST /ops/lab/start (expect failure without quiet mode)
log_test "Test 5: POST /ops/lab/start (validation check)"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

RESPONSE=$(curl -s -X POST "$BASE_URL/ops/lab/start" \
    -H "Content-Type: application/json" \
    -d '{"experiment_type": "flow_shaping", "a_ms": 10000, "b_ms": 10000, "rounds": 1}')

if echo "$RESPONSE" | jq -e '.ok == false' > /dev/null 2>&1; then
    ERROR=$(echo "$RESPONSE" | jq -r '.error')
    
    if [ "$ERROR" = "quiet_mode_required" ] || [ "$ERROR" = "prewarm_required" ]; then
        log_pass "Start endpoint validates prerequisites correctly"
        log_info "Validation error: $ERROR (expected)"
    else
        log_info "Start endpoint returned error: $ERROR"
    fi
else
    log_info "Start endpoint returned ok (may have experiment running)"
fi

echo >> "$REPORT_FILE"

# Test 6: GET /ops/lab/report
log_test "Test 6: GET /ops/lab/report"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

RESPONSE=$(curl -s "$BASE_URL/ops/lab/report")

if echo "$RESPONSE" | jq -e '.ok' > /dev/null 2>&1; then
    OK=$(echo "$RESPONSE" | jq -r '.ok')
    
    if [ "$OK" = "false" ]; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error')
        if [ "$ERROR" = "report_not_found" ]; then
            log_pass "Report endpoint accessible (no report yet)"
        else
            log_fail "Report endpoint error: $ERROR"
        fi
    else
        log_pass "Report endpoint accessible (report available)"
    fi
else
    log_fail "Report endpoint failed"
fi

echo >> "$REPORT_FILE"

# Test 7: Backend structure check
log_test "Test 7: Backend Structure"
log "------------------------------------------------------------------" >> "$REPORT_FILE"

# Check core modules
if [ -d "backend_core" ]; then
    log_pass "backend_core/ directory exists"
    
    if [ -f "backend_core/flow_control.py" ]; then
        log_pass "flow_control.py present"
    else
        log_fail "flow_control.py missing"
    fi
    
    if [ -f "backend_core/routing_policy.py" ]; then
        log_pass "routing_policy.py present"
    else
        log_fail "routing_policy.py missing"
    fi
else
    log_fail "backend_core/ directory missing"
fi

# Check services
if [ -f "services/routers/ops_lab.py" ]; then
    log_pass "ops_lab.py present"
else
    log_fail "ops_lab.py missing"
fi

echo >> "$REPORT_FILE"

# Summary
log "=================================================================="
log "VERIFICATION SUMMARY"
log "=================================================================="

# Count pass/fail
PASS_COUNT=$(grep -c "\[PASS\]" "$REPORT_FILE" || echo 0)
FAIL_COUNT=$(grep -c "\[FAIL\]" "$REPORT_FILE" || echo 0)
TOTAL=$((PASS_COUNT + FAIL_COUNT))

log ""
log "Total Tests: $TOTAL"
log "Passed: $PASS_COUNT"
log "Failed: $FAIL_COUNT"
log ""

if [ $FAIL_COUNT -eq 0 ]; then
    log "Status: ✓ ALL TESTS PASSED"
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
else
    log "Status: ✗ SOME TESTS FAILED"
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
fi

log ""
log "Full report: $REPORT_FILE"
log "=================================================================="

# Check report size
LINE_COUNT=$(wc -l < "$REPORT_FILE")
if [ "$LINE_COUNT" -le 50 ]; then
    echo -e "${GREEN}✓${NC} Report is ≤50 lines ($LINE_COUNT lines)"
else
    echo -e "${YELLOW}⚠${NC} Report exceeds 50 lines ($LINE_COUNT lines)"
fi

echo
echo "Verification complete. Check $REPORT_FILE for details."

# Exit with appropriate code
if [ $FAIL_COUNT -eq 0 ]; then
    exit 0
else
    exit 1
fi


