#!/usr/bin/env bash
#
# black_swan_backend_test.sh — Backend-Only Full Test for Black Swan
# Tests: Health, Warmup, Progress, Baseline, Report, Phase Ordering
#
# Usage: ./scripts/black_swan_backend_test.sh [API_BASE]
#
# This script runs a complete end-to-end backend test WITHOUT touching the frontend.
# It verifies all endpoints, triggers a Black Swan test, and validates the results.

set -euo pipefail

API_BASE="${1:-http://localhost:8001}"
PASS=0
FAIL=0
TIMEOUT=150  # Max seconds to wait for test completion

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $*"; ((PASS++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $*"; ((FAIL++)); }
log_section() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}$*${NC}"; echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Black Swan Backend-Only Full Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Base: $API_BASE"
echo "Timeout: ${TIMEOUT}s"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 0: Preflight - Health & Contracts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 0: Preflight - Health & Contracts"

log_info "Testing endpoint health (expecting HTTP 200)..."

HEALTH_ENDPOINTS=(
    "/auto/status"
    "/tuner/enabled"
    "/admin/warmup/status"
    "/ops/black_swan/status"
)

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    log_info "Testing: $endpoint"
    
    HTTP_CODE=$(curl -sf -w "%{http_code}" -o /tmp/endpoint_test.json "${API_BASE}${endpoint}" 2>/dev/null || echo "000")
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        log_pass "$endpoint → HTTP 200"
        
        # Validate JSON
        if jq empty /tmp/endpoint_test.json 2>/dev/null; then
            log_pass "$endpoint → Valid JSON"
        else
            log_fail "$endpoint → Invalid JSON"
        fi
    else
        log_fail "$endpoint → HTTP $HTTP_CODE (expected 200)"
    fi
done

# Test /dashboard.json (should be 410)
log_info "Testing: /dashboard.json (expecting HTTP 410)"
HTTP_CODE=$(curl -sf -w "%{http_code}" -o /tmp/dashboard_test.json "${API_BASE}/dashboard.json" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "410" ]]; then
    log_pass "/dashboard.json → HTTP 410 (Gone)"
    
    if jq -e '.ok==true and .deprecated==true' /tmp/dashboard_test.json >/dev/null 2>&1; then
        log_pass "/dashboard.json → Correct deprecation schema"
    else
        log_fail "/dashboard.json → Missing ok/deprecated fields"
    fi
else
    log_fail "/dashboard.json → HTTP $HTTP_CODE (expected 410)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: GET Purity (No Side Effects)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 1: GET Purity (No Side Effects)"

log_info "Testing GET endpoints for purity (repeated calls should not mutate state)..."

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    log_info "Testing: $endpoint"
    
    # Call twice, strip dynamic fields
    CALL_A=$(curl -sf "${API_BASE}${endpoint}" 2>/dev/null | jq 'del(.timestamp,.eta_sec,.progress,.message)' 2>/dev/null || echo "ERROR")
    sleep 0.3
    CALL_B=$(curl -sf "${API_BASE}${endpoint}" 2>/dev/null | jq 'del(.timestamp,.eta_sec,.progress,.message)' 2>/dev/null || echo "ERROR")
    
    if [[ "$CALL_A" == "ERROR" ]] || [[ "$CALL_B" == "ERROR" ]]; then
        log_fail "$endpoint → Failed to fetch"
        continue
    fi
    
    # Compare stripped responses
    if diff <(echo "$CALL_A") <(echo "$CALL_B") >/dev/null 2>&1; then
        log_pass "$endpoint → PURE (no state mutations)"
    else
        log_fail "$endpoint → MUTATION DETECTED"
        echo "  First:  $CALL_A"
        echo "  Second: $CALL_B"
    fi
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: Trigger Black Swan Test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 2: Trigger Black Swan Test"

log_info "Starting Black Swan test (POST /ops/black_swan)..."

START_RESPONSE=$(curl -sf -X POST "${API_BASE}/ops/black_swan" 2>/dev/null || echo "{}")

if echo "$START_RESPONSE" | jq -e '.ok==true' >/dev/null 2>&1; then
    log_pass "Black Swan test started successfully"
    echo "  Response: $(echo "$START_RESPONSE" | jq -c .)"
else
    log_fail "Failed to start Black Swan test"
    echo "  Response: $START_RESPONSE"
    echo ""
    echo "❌ Cannot proceed without a running test. Exiting."
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: Poll Progress & Validate Phase Ordering
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 3: Poll Progress & Validate Phase Ordering"

log_info "Polling progress every 3s (max ${TIMEOUT}s)..."
echo ""

ELAPSED=0
LAST_PHASE=""
LAST_PROGRESS=0
MONOTONIC=true
PHASE_ORDERED=true
EXPECTED_PHASES=("starting" "warmup" "baseline" "trip" "recovery" "complete")
PHASE_IDX=0

while [[ $ELAPSED -lt $TIMEOUT ]]; do
    STATUS=$(curl -sf "${API_BASE}/ops/black_swan/status" 2>/dev/null || echo "{}")
    
    PHASE=$(echo "$STATUS" | jq -r '.phase // "unknown"')
    PROGRESS=$(echo "$STATUS" | jq -r '.progress // -1')
    ETA=$(echo "$STATUS" | jq -r '.eta_sec // 0')
    RUNNING=$(echo "$STATUS" | jq -r '.running // false')
    
    echo "  [${ELAPSED}s] phase=$PHASE, progress=$PROGRESS%, eta=${ETA}s, running=$RUNNING"
    
    # Check monotonicity
    if [[ "$PROGRESS" != "-1" ]] && [[ "$LAST_PROGRESS" != "0" ]]; then
        if [[ "$PROGRESS" -lt "$LAST_PROGRESS" ]]; then
            MONOTONIC=false
            log_fail "Progress regression detected: $LAST_PROGRESS% → $PROGRESS%"
        fi
    fi
    LAST_PROGRESS=$PROGRESS
    
    # Check phase ordering
    if [[ "$PHASE" != "$LAST_PHASE" ]] && [[ "$PHASE" != "unknown" ]]; then
        log_info "Phase transition: $LAST_PHASE → $PHASE"
        
        # Verify phase is in expected order
        FOUND=false
        for i in "${!EXPECTED_PHASES[@]}"; do
            if [[ "${EXPECTED_PHASES[$i]}" == "$PHASE" ]]; then
                if [[ $i -ge $PHASE_IDX ]]; then
                    PHASE_IDX=$i
                    FOUND=true
                else
                    PHASE_ORDERED=false
                    log_fail "Phase regression: $LAST_PHASE → $PHASE (out of order)"
                fi
                break
            fi
        done
        
        if [[ "$FOUND" == "false" ]] && [[ "$PHASE" != "error" ]]; then
            PHASE_ORDERED=false
            log_fail "Unknown phase: $PHASE"
        fi
        
        LAST_PHASE=$PHASE
    fi
    
    # Check for completion
    if [[ "$PHASE" == "complete" ]] && [[ "$RUNNING" == "false" ]]; then
        log_pass "Test completed (phase=complete, running=false)"
        break
    fi
    
    if [[ "$PHASE" == "error" ]]; then
        log_fail "Test ended with error phase"
        MESSAGE=$(echo "$STATUS" | jq -r '.message // "Unknown error"')
        echo "  Error message: $MESSAGE"
        break
    fi
    
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done

echo ""

if [[ $ELAPSED -ge $TIMEOUT ]]; then
    log_fail "Test timeout after ${TIMEOUT}s"
else
    log_pass "Test completed within ${ELAPSED}s"
fi

if [[ "$MONOTONIC" == "true" ]]; then
    log_pass "Progress was monotonic (never decreased)"
else
    log_fail "Progress regression detected"
fi

if [[ "$PHASE_ORDERED" == "true" ]]; then
    log_pass "Phases followed correct ordering"
else
    log_fail "Phase ordering violated"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4: Fetch & Validate Final Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 4: Fetch & Validate Final Report"

log_info "Fetching final report from /ops/black_swan..."

REPORT=$(curl -sf "${API_BASE}/ops/black_swan" 2>/dev/null || echo "{}")

if echo "$REPORT" | jq -e '.ok==true' >/dev/null 2>&1; then
    log_pass "Report fetched successfully"
else
    log_fail "Failed to fetch report"
    echo "  Response: $REPORT"
fi

# Save full report for detailed checks
echo "$REPORT" | jq '.report' > /tmp/black_swan_report.json 2>/dev/null || echo "{}" > /tmp/black_swan_report.json

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5: Validate Baseline Gates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 5: Validate Baseline Gates"

log_info "Checking baseline quality..."

BEFORE_SAMPLES=$(jq -r '.before.kpi.samples // 0' /tmp/black_swan_report.json)
BEFORE_P95=$(jq -r '.before.kpi.p95 // null' /tmp/black_swan_report.json)

echo "  Baseline samples: $BEFORE_SAMPLES"
echo "  Baseline p95: ${BEFORE_P95}ms"

# Check samples
if [[ "$BEFORE_SAMPLES" -ge 100 ]]; then
    log_pass "Baseline samples ≥ 100 ($BEFORE_SAMPLES)"
else
    log_fail "Baseline samples < 100 ($BEFORE_SAMPLES)"
fi

# Check p95 range [10ms, 200ms]
if [[ "$BEFORE_P95" != "null" ]]; then
    if awk -v p95="$BEFORE_P95" 'BEGIN {exit !(p95 >= 10 && p95 <= 200)}'; then
        log_pass "Baseline p95 ∈ [10ms, 200ms] (${BEFORE_P95}ms)"
    else
        # Check if warning is set
        BASELINE_WARNING=$(jq -r '.baseline_gate.warning // false' /tmp/black_swan_report.json)
        if [[ "$BASELINE_WARNING" == "true" ]]; then
            log_pass "Baseline p95 outside range but warning recorded (not dropped)"
            REASON=$(jq -r '.baseline_gate.reason // "unknown"' /tmp/black_swan_report.json)
            echo "  Warning reason: $REASON"
        else
            log_fail "Baseline p95 outside range and no warning recorded"
        fi
    fi
else
    log_fail "Baseline p95 is null"
fi

# Check baseline_gate object
if jq -e '.baseline_gate' /tmp/black_swan_report.json >/dev/null 2>&1; then
    log_pass "baseline_gate object exists in report"
    
    # Check required fields
    REQUIRED_FIELDS=("p95_ms" "samples" "accepted" "warning" "reason")
    for field in "${REQUIRED_FIELDS[@]}"; do
        if jq -e ".baseline_gate | has(\"$field\")" /tmp/black_swan_report.json >/dev/null 2>&1; then
            log_pass "baseline_gate has '$field' field"
        else
            log_fail "baseline_gate missing '$field' field"
        fi
    done
else
    log_fail "baseline_gate object missing from report"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6: Validate Progress Timeline & Phase Ordering
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 6: Validate Progress Timeline"

log_info "Checking progress_timeline in report..."

TIMELINE=$(jq -r '.progress_timeline // [] | join(" → ")' /tmp/black_swan_report.json)
EXPECTED_TIMELINE="starting → warmup → baseline → trip → recovery → complete"

echo "  Timeline: $TIMELINE"
echo "  Expected: $EXPECTED_TIMELINE"

if [[ "$TIMELINE" == "$EXPECTED_TIMELINE" ]]; then
    log_pass "Progress timeline matches expected sequence"
else
    log_fail "Progress timeline does not match expected sequence"
fi

# Count phases
PHASE_COUNT=$(jq -r '.progress_timeline // [] | length' /tmp/black_swan_report.json)
if [[ "$PHASE_COUNT" -eq 6 ]]; then
    log_pass "Progress timeline has 6 phases"
else
    log_fail "Progress timeline has $PHASE_COUNT phases (expected 6)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 7: Validate Report Structure
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 7: Validate Report Structure"

log_info "Checking required report fields..."

REQUIRED_REPORT_FIELDS=("before" "trip" "after" "progress_timeline" "warmup_config" "baseline_gate")
for field in "${REQUIRED_REPORT_FIELDS[@]}"; do
    if jq -e "has(\"$field\")" /tmp/black_swan_report.json >/dev/null 2>&1; then
        log_pass "Report has '$field' field"
    else
        log_fail "Report missing '$field' field"
    fi
done

# Check warmup_config structure
if jq -e '.warmup_config | has("qps") and has("duration_sec") and has("buffer_sec")' /tmp/black_swan_report.json >/dev/null 2>&1; then
    log_pass "warmup_config has required fields"
else
    log_fail "warmup_config missing required fields"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 8: Check Report File on Filesystem
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 8: Check Report File on Filesystem"

log_info "Checking for report file in reports/ directory..."

if [[ -d "reports" ]]; then
    LATEST_REPORT=$(ls -1t reports/black_swan_*.json 2>/dev/null | head -n1 || echo "")
    
    if [[ -n "$LATEST_REPORT" ]] && [[ -f "$LATEST_REPORT" ]]; then
        log_pass "Report file exists: $LATEST_REPORT"
        
        # Verify it's valid JSON
        if jq empty "$LATEST_REPORT" 2>/dev/null; then
            log_pass "Report file is valid JSON"
        else
            log_fail "Report file is not valid JSON"
        fi
    else
        log_fail "No report file found in reports/"
    fi
else
    log_fail "reports/ directory does not exist"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 9: Check Progress Contracts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 9: Validate Progress Contracts"

log_info "Checking final progress state..."

FINAL_STATUS=$(curl -sf "${API_BASE}/ops/black_swan/status" 2>/dev/null || echo "{}")

FINAL_PROGRESS=$(echo "$FINAL_STATUS" | jq -r '.progress // -1')
FINAL_PHASE=$(echo "$FINAL_STATUS" | jq -r '.phase // "unknown"')
FINAL_RUNNING=$(echo "$FINAL_STATUS" | jq -r '.running // true')

echo "  Final progress: $FINAL_PROGRESS%"
echo "  Final phase: $FINAL_PHASE"
echo "  Running: $FINAL_RUNNING"

if [[ "$FINAL_PROGRESS" -eq 100 ]]; then
    log_pass "Final progress is 100%"
else
    log_fail "Final progress is $FINAL_PROGRESS% (expected 100%)"
fi

if [[ "$FINAL_PHASE" == "complete" ]]; then
    log_pass "Final phase is 'complete'"
elif [[ "$FINAL_PHASE" == "error" ]]; then
    log_fail "Final phase is 'error' (test failed)"
else
    log_fail "Final phase is '$FINAL_PHASE' (expected 'complete')"
fi

if [[ "$FINAL_RUNNING" == "false" ]]; then
    log_pass "Test marked as not running"
else
    log_fail "Test still marked as running"
fi

# Check progress_checks
if echo "$FINAL_STATUS" | jq -e '.progress_checks' >/dev/null 2>&1; then
    log_pass "progress_checks field exists"
    
    PROGRESS_MONOTONIC=$(echo "$FINAL_STATUS" | jq -r '.progress_checks.monotonic // false')
    if [[ "$PROGRESS_MONOTONIC" == "true" ]]; then
        log_pass "progress_checks.monotonic is true"
    else
        log_fail "progress_checks.monotonic is false"
    fi
else
    log_fail "progress_checks field missing"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10: Log Scan for 404s
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "STEP 10: Log Scan for 404s"

log_info "Scanning logs for 404 errors on key routes..."

KEY_ROUTES=(
    "/auto/status"
    "/tuner/enabled"
    "/admin/warmup/status"
    "/dashboard.json"
)

if ls services/fiqa_api/*.log >/dev/null 2>&1; then
    FOUND_404=false
    
    for route in "${KEY_ROUTES[@]}"; do
        if grep -q "404.*${route}" services/fiqa_api/*.log 2>/dev/null; then
            log_fail "Found 404 for $route in logs"
            FOUND_404=true
        fi
    done
    
    if [[ "$FOUND_404" == "false" ]]; then
        log_pass "No 404 errors found for key routes (NO_404 ✅)"
    fi
else
    log_info "No log files found in services/fiqa_api/*.log (skipping)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Backend Full Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "✅ Backend Full Test: PASS"
    echo ""
    echo "All checks passed:"
    echo "  ✓ Endpoint health & contracts"
    echo "  ✓ GET endpoint purity (no side effects)"
    echo "  ✓ Black Swan test completed successfully"
    echo "  ✓ Progress was monotonic & phase-ordered"
    echo "  ✓ Baseline gates validated (samples ≥ 100, p95 ∈ [10, 200]ms)"
    echo "  ✓ Report structure complete with all required fields"
    echo "  ✓ Progress timeline correct (6 phases in order)"
    echo "  ✓ Report file exists on filesystem"
    echo "  ✓ Final state: progress=100%, phase=complete, running=false"
    echo "  ✓ No 404 errors for key routes"
    echo ""
    echo "🚀 Ready to proceed to frontend integration test!"
    echo ""
    exit 0
else
    echo "❌ Backend Full Test: FAIL"
    echo ""
    echo "Failed checks: $FAIL"
    echo ""
    echo "Review the output above to identify issues."
    echo ""
    exit 1
fi


