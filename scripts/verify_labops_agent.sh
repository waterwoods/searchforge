#!/bin/bash
# verify_labops_agent.sh - Verification script for LabOps Agent V1
# =================================================================
# Comprehensive verification of all agent components.

# Note: Don't use 'set -e' as we want to collect all failures

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================================"
echo "LABOPS AGENT V1 - VERIFICATION"
echo "======================================================================"
echo

PASS_COUNT=0
FAIL_COUNT=0

check() {
    local name="$1"
    local cmd="$2"
    
    echo -n "[$((PASS_COUNT + FAIL_COUNT + 1))] $name... "
    
    if bash -c "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASS_COUNT++)) || true
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAIL_COUNT++)) || true
    fi
}

# File structure checks
echo "FILE STRUCTURE CHECKS"
echo "----------------------------------------------------------------------"

check "Agent runner exists" "test -f agents/labops/agent_runner.py"
check "OpsClient exists" "test -f agents/labops/tools/ops_client.py"
check "Report parser exists" "test -f agents/labops/tools/report_parser.py"
check "Decision engine exists" "test -f agents/labops/policies/decision.py"
check "Config file exists" "test -f agents/labops/plan/plan_combo.yaml"
check "System prompt exists" "test -f agents/labops/prompts/system.md"
check "Tests exist" "test -f agents/labops/tests/test_smoke.py"
check "Runner script exists" "test -x scripts/run_labops_agent.sh"
check "README exists" "test -f agents/labops/README.md"

echo

# Code quality checks
echo "CODE QUALITY CHECKS"
echo "----------------------------------------------------------------------"

check "No syntax errors in agent_runner" "python3 -m py_compile agents/labops/agent_runner.py"
check "No syntax errors in ops_client" "python3 -m py_compile agents/labops/tools/ops_client.py"
check "No syntax errors in report_parser" "python3 -m py_compile agents/labops/tools/report_parser.py"
check "No syntax errors in decision" "python3 -m py_compile agents/labops/policies/decision.py"

echo

# Unit tests
echo "UNIT TESTS"
echo "----------------------------------------------------------------------"

check "Smoke tests pass" "python3 agents/labops/tests/test_smoke.py"

echo

# Functional tests
echo "FUNCTIONAL TESTS"
echo "----------------------------------------------------------------------"

check "Dry-run executes" "./scripts/run_labops_agent.sh --dry-run"
check "Summary generated" "test -f reports/LABOPS_AGENT_SUMMARY.txt"
check "History appended" "test -f agents/labops/state/history.jsonl"
check "Summary ≤60 lines" "test \$(wc -l < reports/LABOPS_AGENT_SUMMARY.txt) -le 60"

echo

# Configuration checks
echo "CONFIGURATION CHECKS"
echo "----------------------------------------------------------------------"

check "Config is valid YAML" "python3 -c 'import yaml; yaml.safe_load(open(\"agents/labops/plan/plan_combo.yaml\"))'"
check "Config has experiment section" "grep -q 'experiment:' agents/labops/plan/plan_combo.yaml"
check "Config has thresholds section" "grep -q 'thresholds:' agents/labops/plan/plan_combo.yaml"

echo

# Documentation checks
echo "DOCUMENTATION CHECKS"
echo "----------------------------------------------------------------------"

check "README has quick commands" "grep -qi 'quick start' agents/labops/README.md"
check "README has decision rules" "grep -q 'Decision Logic' agents/labops/README.md"
check "Main README updated" "grep -q 'LabOps Agent' README.md"

echo

# Summary
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"
echo "Total Tests: $((PASS_COUNT + FAIL_COUNT))"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo
    echo "LabOps Agent V1 is ready for use!"
    echo
    echo "Quick start:"
    echo "  ./scripts/run_labops_agent.sh --dry-run"
    echo "  cat reports/LABOPS_AGENT_SUMMARY.txt"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo
    echo "Please review failures and fix before use."
    exit 1
fi

