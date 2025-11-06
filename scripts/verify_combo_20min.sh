#!/bin/bash
# verify_combo_20min.sh - Verification Script for 20-Minute Combo Test
# =====================================================================
# Validates results from the 20-minute combo test
#
# Usage:
#   ./scripts/verify_combo_20min.sh
#   ./scripts/verify_combo_20min.sh --lite  # Quick check only
#
# Checks:
#   1. Report files exist
#   2. Metrics are within acceptable ranges
#   3. Agent verdict (if available)
#   4. System health

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LITE_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --lite)
            LITE_MODE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "======================================================================"
echo "20-MINUTE COMBO TEST VERIFICATION"
echo "======================================================================"
echo

# Check 1: Report files
echo "[1/4] Checking report files..."
cd "$PROJECT_ROOT"

if [ -f "reports/LABOPS_COMBO_REPORT.txt" ]; then
    check_pass "LABOPS_COMBO_REPORT.txt exists"
else
    check_fail "LABOPS_COMBO_REPORT.txt not found"
fi

if [ -f "reports/lab_combo_report.txt" ]; then
    check_pass "lab_combo_report.txt exists"
else
    check_warn "lab_combo_report.txt not found (non-critical)"
fi

echo

# Check 2: Metrics validation
echo "[2/4] Validating metrics..."

if [ -f "reports/LABOPS_COMBO_REPORT.txt" ]; then
    REPORT="reports/LABOPS_COMBO_REPORT.txt"
    
    # Check for error rate
    if grep -q -i "error" "$REPORT"; then
        ERROR_RATE=$(grep -i "error" "$REPORT" | grep -oE '[0-9]+\.?[0-9]*%' | head -1)
        
        if [[ "$ERROR_RATE" != "" ]]; then
            ERROR_VAL=$(echo "$ERROR_RATE" | grep -oE '[0-9]+\.?[0-9]*')
            
            if (( $(echo "$ERROR_VAL < 1.0" | bc -l 2>/dev/null || echo 0) )); then
                check_pass "Error rate < 1%: $ERROR_RATE"
            else
                check_fail "Error rate ≥ 1%: $ERROR_RATE"
            fi
        fi
    fi
    
    # Check for P95 delta
    if grep -q -i "ΔP95\|delta.*p95" "$REPORT"; then
        DELTA_P95=$(grep -i "ΔP95\|delta.*p95" "$REPORT" | head -1 | grep -oE '[-+]?[0-9]+\.?[0-9]*%' | head -1)
        
        if [[ "$DELTA_P95" != "" ]]; then
            check_pass "P95 delta found: $DELTA_P95"
        else
            check_warn "P95 delta format unexpected"
        fi
    fi
    
    # Check report size
    LINE_COUNT=$(wc -l < "$REPORT")
    if [ "$LINE_COUNT" -lt 1000 ]; then
        check_pass "Report size reasonable: $LINE_COUNT lines"
    else
        check_warn "Report is large: $LINE_COUNT lines"
    fi
else
    check_fail "No report file to validate"
fi

echo

# Check 3: Agent verdict (if available)
echo "[3/4] Checking agent verdict..."

AGENT_V2="reports/LABOPS_AGENT_V2_SUMMARY.txt"
AGENT_V3="reports/LABOPS_AGENT_V3_SUMMARY.txt"

if [ -f "$AGENT_V2" ]; then
    VERDICT=$(grep -i "Decision:\|Verdict:" "$AGENT_V2" | head -1 | awk '{print $NF}')
    
    if [[ "$VERDICT" =~ ^(PASS|EDGE|FAIL|BLOCKED|ERROR)$ ]]; then
        if [ "$VERDICT" = "PASS" ] || [ "$VERDICT" = "EDGE" ]; then
            check_pass "Agent V2 verdict: $VERDICT"
        else
            check_warn "Agent V2 verdict: $VERDICT"
        fi
    else
        check_warn "Agent V2 verdict unclear"
    fi
elif [ -f "$AGENT_V3" ]; then
    VERDICT=$(grep -i "Decision:\|Verdict:" "$AGENT_V3" | head -1 | awk '{print $NF}')
    
    if [[ "$VERDICT" =~ ^(PASS|EDGE|FAIL|BLOCKED|ERROR)$ ]]; then
        if [ "$VERDICT" = "PASS" ] || [ "$VERDICT" = "EDGE" ]; then
            check_pass "Agent V3 verdict: $VERDICT"
        else
            check_warn "Agent V3 verdict: $VERDICT"
        fi
    else
        check_warn "Agent V3 verdict unclear"
    fi
else
    check_warn "No agent report found (agent may not have run)"
fi

echo

# Check 4: System health (if not lite mode)
if [ "$LITE_MODE" != true ]; then
    echo "[4/4] Checking system health..."
    
    if docker compose ps redis 2>/dev/null | grep -q "Up"; then
        check_pass "Redis is running"
    else
        check_fail "Redis is not running"
    fi
    
    if docker compose ps qdrant 2>/dev/null | grep -q "Up"; then
        check_pass "Qdrant is running"
    else
        check_fail "Qdrant is not running"
    fi
    
    if docker compose ps milvus-standalone 2>/dev/null | grep -q "Up"; then
        check_pass "Milvus is running"
    else
        check_fail "Milvus is not running"
    fi
else
    echo "[4/4] Skipping system health check (lite mode)"
fi

echo
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}ALL PASS ✅${NC}"
    exit 0
else
    echo -e "${YELLOW}SOME CHECKS FAILED ⚠${NC}"
    exit 1
fi

