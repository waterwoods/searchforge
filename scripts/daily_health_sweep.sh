#!/usr/bin/env bash
set -euo pipefail

# Daily Health Sweep (one-click)
# 审计对齐 → 小样本 Smoke → 拉报告 → 回写 SLA → 最终验收

# Default environment variables
DATASET="${DATASET:-fiqa_para_50k}"
SAMPLE="${SAMPLE:-30}"
TOPK="${TOPK:-10}"
ORCH_BASE="${ORCH_BASE:-http://127.0.0.1:8000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Temporary files
REPORT_JSON="/tmp/_report.json"
ALIGNMENT_JSON="/tmp/_align_${DATASET}.json"
ACCEPTANCE_JSON="/tmp/_acceptance.json"

# Cleanup function
cleanup() {
    # Keep report JSON for inspection
    echo ""
    echo "📄 Report saved to: ${REPORT_JSON}"
    echo "📄 Acceptance summary: ${ACCEPTANCE_JSON}"
}

trap cleanup EXIT

# Step 1: Preflight (alignment gate)
echo "=========================================="
echo "Step 1/5: Preflight (Alignment Gate)"
echo "=========================================="
echo "Dataset: ${DATASET}"
echo ""

if ! make orchestrate.policy.audit DATASET="${DATASET}" > /tmp/_audit_output.txt 2>&1; then
    echo -e "${RED}❌ ALIGNMENT_BLOCK: Preflight check failed${NC}"
    echo ""
    echo "Audit output:"
    cat /tmp/_audit_output.txt
    exit 1
fi

# Check mismatch_rate from JSON output
if [ -f "${ALIGNMENT_JSON}" ]; then
    MISMATCH_RATE=$(python3 -c "import json; d=json.load(open('${ALIGNMENT_JSON}')); print(d.get('mismatch_rate', 1.0))" 2>/dev/null || echo "1.0")
    if [ "$(echo "${MISMATCH_RATE} > 0" | bc -l 2>/dev/null || python3 -c "print(1 if ${MISMATCH_RATE} > 0 else 0)")" -eq 1 ]; then
        echo -e "${RED}❌ ALIGNMENT_BLOCK: mismatch_rate=${MISMATCH_RATE} > 0${NC}"
        echo ""
        echo "Alignment check details:"
        cat "${ALIGNMENT_JSON}" | python3 -m json.tool 2>/dev/null || cat "${ALIGNMENT_JSON}"
        exit 1
    fi
    echo -e "${GREEN}✅ Alignment check passed (mismatch_rate=${MISMATCH_RATE})${NC}"
else
    echo -e "${YELLOW}⚠️  Alignment JSON not found, but audit passed${NC}"
fi

echo ""

# Step 2: Smoke run
echo "=========================================="
echo "Step 2/5: Smoke Run"
echo "=========================================="
echo "Sample: ${SAMPLE}, TopK: ${TOPK}"
echo ""

if ! make orchestrate.run DATASET="${DATASET}" SAMPLE="${SAMPLE}" TOPK="${TOPK}" > /tmp/_run_output.txt 2>&1; then
    echo -e "${RED}❌ Smoke run failed${NC}"
    echo ""
    echo "Run output:"
    cat /tmp/_run_output.txt
    exit 1
fi

# Extract RUN_ID from .last_run
if [ ! -f .last_run ]; then
    echo -e "${RED}❌ .last_run not found after smoke run${NC}"
    exit 1
fi

RUN_ID=$(cat .last_run)
echo -e "${GREEN}✅ Smoke run started: run_id=${RUN_ID}${NC}"
echo ""

# Wait for completion (poll status)
echo "Waiting for experiment to complete..."
MAX_WAIT=1800  # 30 minutes max
WAIT_INTERVAL=10
ELAPSED=0
STATUS="unknown"

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if make orchestrate.status > /tmp/_status.txt 2>&1; then
        # Extract status from JSON (handle both direct status and nested structure)
        STATUS=$(python3 <<PY 2>/dev/null || echo "unknown"
import json
import sys
try:
    with open('/tmp/_status.txt', 'r') as f:
        content = f.read()
        # Skip the "run_id=..." line if present
        lines = content.split('\n')
        json_lines = [l for l in lines if l.strip().startswith('{')]
        if json_lines:
            data = json.loads(json_lines[0])
            print(data.get('status', 'unknown'))
        else:
            print('unknown')
except Exception:
    print('unknown')
PY
)
        if [ "${STATUS}" = "completed" ]; then
            echo -e "${GREEN}✅ Experiment completed${NC}"
            break
        elif [ "${STATUS}" = "failed" ] || [ "${STATUS}" = "error" ]; then
            echo -e "${RED}❌ Experiment failed (status: ${STATUS})${NC}"
            cat /tmp/_status.txt
            exit 1
        fi
    else
        # Status check failed, might be still starting
        STATUS="starting"
    fi
    if [ $((ELAPSED % 60)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        echo "  Status: ${STATUS} (waiting ${ELAPSED}s/${MAX_WAIT}s)..."
    fi
    sleep ${WAIT_INTERVAL}
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ Experiment timed out after ${MAX_WAIT}s (status: ${STATUS})${NC}"
    cat /tmp/_status.txt
    exit 1
fi

echo ""

# Step 3: Report & SLA update
echo "=========================================="
echo "Step 3/5: Report & SLA Update"
echo "=========================================="

if ! make orchestrate.report > "${REPORT_JSON}" 2>&1; then
    echo -e "${RED}❌ Failed to fetch report${NC}"
    cat "${REPORT_JSON}"
    exit 1
fi

echo -e "${GREEN}✅ Report fetched${NC}"

# Update SLA
if ! make orchestrate.update-sla > /tmp/_sla_update.txt 2>&1; then
    echo -e "${YELLOW}⚠️  SLA update failed (non-fatal)${NC}"
    cat /tmp/_sla_update.txt
else
    echo -e "${GREEN}✅ SLA updated${NC}"
fi

echo ""

# Step 4: Verify artifacts
echo "=========================================="
echo "Step 4/5: Verify Artifacts"
echo "=========================================="

RUN_DIR="reports/${RUN_ID}"
ARTIFACTS_OK=true
MISSING_ARTIFACTS=()

check_artifact() {
    local artifact="$1"
    if [ -f "${RUN_DIR}/${artifact}" ]; then
        echo -e "${GREEN}  ✅ ${artifact}${NC}"
    else
        echo -e "${RED}  ❌ ${artifact} (missing)${NC}"
        ARTIFACTS_OK=false
        MISSING_ARTIFACTS+=("${artifact}")
    fi
}

check_artifact "winners.json"
check_artifact "winners.md"
check_artifact "pareto.png"
check_artifact "ab_diff.png"
check_artifact "failTopN.csv"
check_artifact "events.jsonl"

echo ""

# Step 5: Acceptance summary
echo "=========================================="
echo "Step 5/5: Acceptance Summary"
echo "=========================================="

# Parse report and winners.json
ARTIFACTS_OK_VALUE="${ARTIFACTS_OK}"
python3 <<PY > "${ACCEPTANCE_JSON}"
import json
import sys
from pathlib import Path

run_id = "${RUN_ID}"
run_dir = Path("reports") / run_id
report_json_path = Path("${REPORT_JSON}")
artifacts_ok_str = "${ARTIFACTS_OK_VALUE}"

# Load report
try:
    with open(report_json_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
except Exception as e:
    print(f'{{"error": "Failed to load report: {e}"}}', file=sys.stderr)
    sys.exit(1)

# Load winners.json
winners_path = run_dir / "winners.json"
winners_data = {}
if winners_path.exists():
    try:
        with open(winners_path, 'r', encoding='utf-8') as f:
            winners_data = json.load(f)
    except Exception as e:
        print(f'{{"error": "Failed to load winners.json: {e}"}}', file=sys.stderr)

# Extract metrics
metrics = {}
winner = winners_data.get("winner", {})
if isinstance(winner, dict):
    winner_metrics = winner.get("metrics", {})
    metrics["recall_at_10"] = float(winner_metrics.get("recall_at_10", 0.0))
    metrics["p95_ms"] = float(winner_metrics.get("p95_ms", 0.0))

# Extract dataset info
dataset = winners_data.get("dataset", "${DATASET}")
queries_path = winners_data.get("queries_path", "")
qrels_path = winners_data.get("qrels_path", "")
id_normalization = winners_data.get("id_normalization", "")

# Get SLA verdict
sla_verdict = report_data.get("sla_verdict", "unknown")

# Get status
status = "completed"  # Assume completed if we got here

# Check artifacts (convert string to bool)
artifacts_ok = artifacts_ok_str.lower() == "true"

# Build acceptance summary
acceptance = {
    "run_id": run_id,
    "status": status,
    "sla_verdict": sla_verdict,
    "metrics": metrics,
    "dataset": dataset,
    "queries_path": queries_path,
    "qrels_path": qrels_path,
    "id_normalization": id_normalization,
    "artifacts_ok": artifacts_ok
}

print(json.dumps(acceptance, indent=2))
PY

# Display acceptance summary
cat "${ACCEPTANCE_JSON}" | python3 -m json.tool

# Check PASS criteria
PASS=true
REASONS=()

STATUS=$(python3 -c "import json; d=json.load(open('${ACCEPTANCE_JSON}')); print(d.get('status', 'unknown'))")
SLA_VERDICT=$(python3 -c "import json; d=json.load(open('${ACCEPTANCE_JSON}')); print(d.get('sla_verdict', 'unknown'))")
ARTIFACTS_OK=$(python3 -c "import json; d=json.load(open('${ACCEPTANCE_JSON}')); print(d.get('artifacts_ok', False))")

if [ "${STATUS}" != "completed" ]; then
    PASS=false
    REASONS+=("status != completed (got: ${STATUS})")
fi

if [ "${ARTIFACTS_OK}" != "true" ]; then
    PASS=false
    REASONS+=("artifacts_ok != true (missing: ${MISSING_ARTIFACTS[*]})")
fi

# Check winners.json structure
if [ -f "${RUN_DIR}/winners.json" ]; then
    HAS_DATASET=$(python3 -c "import json; d=json.load(open('${RUN_DIR}/winners.json')); print('dataset' in d)" 2>/dev/null || echo "False")
    HAS_QUERIES=$(python3 -c "import json; d=json.load(open('${RUN_DIR}/winners.json')); print('queries_path' in d)" 2>/dev/null || echo "False")
    HAS_QRELS=$(python3 -c "import json; d=json.load(open('${RUN_DIR}/winners.json')); print('qrels_path' in d)" 2>/dev/null || echo "False")
    HAS_NORM=$(python3 -c "import json; d=json.load(open('${RUN_DIR}/winners.json')); print('id_normalization' in d)" 2>/dev/null || echo "False")
    
    if [ "${HAS_DATASET}" != "True" ] || [ "${HAS_QUERIES}" != "True" ] || [ "${HAS_QRELS}" != "True" ] || [ "${HAS_NORM}" != "True" ]; then
        PASS=false
        REASONS+=("winners.json missing required fields")
    fi
fi

echo ""
echo "=========================================="
if [ "${PASS}" = "true" ] && [ "${SLA_VERDICT}" = "pass" ]; then
    echo -e "${GREEN}✅ ACCEPTANCE: PASS${NC}"
    echo ""
    echo "All checks passed:"
    echo "  - Status: ${STATUS}"
    echo "  - SLA Verdict: ${SLA_VERDICT}"
    echo "  - Artifacts: OK"
    echo "  - Winners.json structure: OK"
else
    echo -e "${RED}❌ ACCEPTANCE: FAIL${NC}"
    echo ""
    echo "Failure reasons:"
    for reason in "${REASONS[@]}"; do
        echo "  - ${reason}"
    done
    
    if [ "${SLA_VERDICT}" = "fail" ]; then
        echo ""
        echo "=========================================="
        echo "Diagnostic Clues (SLA_FAIL):"
        echo "=========================================="
        
        # 1) Latest alignment audit mismatch_rate
        if [ -f "${ALIGNMENT_JSON}" ]; then
            MISMATCH_RATE=$(python3 -c "import json; d=json.load(open('${ALIGNMENT_JSON}')); print(d.get('mismatch_rate', 'N/A'))" 2>/dev/null || echo "N/A")
            echo "1) Latest alignment audit mismatch_rate: ${MISMATCH_RATE}"
        else
            echo "1) Latest alignment audit mismatch_rate: N/A (file not found)"
        fi
        
        # 2) Check events.jsonl for blocks
        EVENTS_FILE="${RUN_DIR}/events.jsonl"
        if [ -f "${EVENTS_FILE}" ]; then
            echo "2) Events.jsonl analysis:"
            BLOCKS=$(grep -E "ALIGNMENT_BLOCK|BUDGET_BLOCK|RUNNER_TIMEOUT" "${EVENTS_FILE}" 2>/dev/null || echo "")
            if [ -n "${BLOCKS}" ]; then
                echo "   Found blocking events:"
                echo "${BLOCKS}" | head -5 | sed 's/^/   /'
            else
                echo "   No blocking events found"
            fi
        else
            echo "2) Events.jsonl: Not found"
        fi
        
        # 3) Show top 5 lines of failTopN.csv
        FAIL_CSV="${RUN_DIR}/failTopN.csv"
        if [ -f "${FAIL_CSV}" ]; then
            echo "3) failTopN.csv (top 5 lines):"
            head -5 "${FAIL_CSV}" | sed 's/^/   /'
        else
            echo "3) failTopN.csv: Not found"
        fi
        
        # Also check ab_diff.csv if exists
        AB_DIFF_CSV="${RUN_DIR}/ab_diff.csv"
        if [ -f "${AB_DIFF_CSV}" ]; then
            echo ""
            echo "   ab_diff.csv (top 5 lines):"
            head -5 "${AB_DIFF_CSV}" | sed 's/^/   /'
        fi
    fi
    
    exit 1
fi

echo "=========================================="
echo ""
echo -e "${GREEN}🎉 Daily Health Sweep completed successfully!${NC}"

