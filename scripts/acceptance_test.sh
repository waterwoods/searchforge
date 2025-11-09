#!/bin/bash
# 验收测试脚本 - 运行完整smoke测试并生成JSON报告

set -e

BASE_URL="http://localhost:8000"
TIMEOUT=600  # 10 minutes

echo "=========================================="
echo "ORCHESTRATOR SMOKE TEST - ACCEPTANCE"
echo "=========================================="
echo ""

# 1. Health checks
echo "[1/7] Health Checks..."
READY_RESP=$(curl -s "${BASE_URL}/ready" || echo '{"ok":false}')
READY_OK=$(echo "$READY_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "false")

EMBED_RESP=$(curl -s "${BASE_URL}/api/health/embeddings" || echo '{"ok":false}')
EMBED_OK=$(echo "$EMBED_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "false")

echo "  /ready: $([ "$READY_OK" = "True" ] && echo '✅' || echo '❌')"
echo "  /api/health/embeddings: $([ "$EMBED_OK" = "True" ] && echo '✅' || echo '❌')"

if [ "$READY_OK" != "True" ] || [ "$EMBED_OK" != "True" ]; then
    echo "❌ Health checks failed"
    exit 1
fi

# 2. Dry-run
echo ""
echo "[2/7] Dry-run Plan..."
DRY_RUN_RESP=$(curl -s -X POST "${BASE_URL}/orchestrate/run?commit=false" \
    -H 'content-type: application/json' \
    -d '{"preset":"smoke","collection":"fiqa_para_50k","overrides":{"sample":40,"top_k":10,"concurrency":2}}')

RUN_ID_DRY=$(echo "$DRY_RUN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('run_id', ''))" 2>/dev/null || echo "")
if [ -z "$RUN_ID_DRY" ]; then
    echo "  ❌ Dry-run failed: $DRY_RUN_RESP"
    exit 1
fi
echo "  ✅ Plan created (dry-run run_id: $RUN_ID_DRY)"

# 3. Commit run
echo ""
echo "[3/7] Commit Run..."
COMMIT_RESP=$(curl -s -X POST "${BASE_URL}/orchestrate/run?commit=true" \
    -H 'content-type: application/json' \
    -d '{"preset":"smoke","collection":"fiqa_para_50k","overrides":{"sample":40,"top_k":10,"concurrency":2}}')

RUN_ID=$(echo "$COMMIT_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('run_id', ''))" 2>/dev/null || echo "")
if [ -z "$RUN_ID" ]; then
    echo "  ❌ Commit failed: $COMMIT_RESP"
    exit 1
fi
echo "  ✅ Run started (run_id: $RUN_ID)"

# 4. Poll status
echo ""
echo "[4/7] Polling Status (max ${TIMEOUT}s)..."
START_TIME=$(date +%s)
STATUS="running"
STAGE="PENDING"
QUEUE_POS=0
STARTED_AT=""
FINISHED_AT=""

while [ $(($(date +%s) - START_TIME)) -lt $TIMEOUT ]; do
    STATUS_RESP=$(curl -s "${BASE_URL}/orchestrate/status?run_id=${RUN_ID}" || echo '{}')
    STATUS=$(echo "$STATUS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    STAGE=$(echo "$STATUS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stage', 'PENDING'))" 2>/dev/null || echo "PENDING")
    QUEUE_POS=$(echo "$STATUS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('queue_pos', 0))" 2>/dev/null || echo "0")
    STARTED_AT=$(echo "$STATUS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('started_at', ''))" 2>/dev/null || echo "")
    FINISHED_AT=$(echo "$STATUS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('finished_at', ''))" 2>/dev/null || echo "")
    
    ELAPSED=$(($(date +%s) - START_TIME))
    echo "  [${ELAPSED}s] Stage: $STAGE, Status: $STATUS, Queue: $QUEUE_POS"
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        break
    fi
    
    sleep 5
done

# 5. Get report
echo ""
echo "[5/7] Get Report..."
REPORT_RESP=$(curl -s "${BASE_URL}/orchestrate/report?run_id=${RUN_ID}" || echo '{}')
SLA_VERDICT=$(echo "$REPORT_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('sla_verdict', 'unknown'))" 2>/dev/null || echo "unknown")

# Extract artifacts
ARTIFACTS_JSON=$(echo "$REPORT_RESP" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).get('artifacts', {})))" 2>/dev/null || echo "{}")

# 6. Check artifacts
echo ""
echo "[6/7] Check Artifacts..."
cd /home/andy/searchforge

WINNERS_JSON=$(echo "$ARTIFACTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('winners_json', ''))" 2>/dev/null || echo "")
WINNERS_MD=$(echo "$ARTIFACTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('winners_md', ''))" 2>/dev/null || echo "")
PARETO_PNG=$(echo "$ARTIFACTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('pareto_png', ''))" 2>/dev/null || echo "")
AB_DIFF_PNG=$(echo "$ARTIFACTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ab_diff_png', ''))" 2>/dev/null || echo "")
FAIL_TOPN_CSV=$(echo "$ARTIFACTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('fail_topn_csv', ''))" 2>/dev/null || echo "")
EVENTS_JSONL=$(echo "$ARTIFACTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('events_jsonl', ''))" 2>/dev/null || echo "")

# Default paths if not in artifacts
[ -z "$WINNERS_JSON" ] && WINNERS_JSON="reports/${RUN_ID}/winners.json"
[ -z "$WINNERS_MD" ] && WINNERS_MD="reports/${RUN_ID}/winners.md"
[ -z "$PARETO_PNG" ] && PARETO_PNG="reports/${RUN_ID}/pareto.png"
[ -z "$AB_DIFF_PNG" ] && AB_DIFF_PNG="reports/${RUN_ID}/ab_diff.png"
[ -z "$FAIL_TOPN_CSV" ] && FAIL_TOPN_CSV="reports/${RUN_ID}/failTopN.csv"
[ -z "$EVENTS_JSONL" ] && EVENTS_JSONL="reports/events/${RUN_ID}.jsonl"

FILES_EXIST_JSON=$(python3 <<EOF
import json
from pathlib import Path

files = {
    "winners_json": "$WINNERS_JSON",
    "winners_md": "$WINNERS_MD",
    "pareto_png": "$PARETO_PNG",
    "ab_diff_png": "$AB_DIFF_PNG",
    "fail_topn_csv": "$FAIL_TOPN_CSV",
    "events_jsonl": "$EVENTS_JSONL"
}

result = {}
for key, path in files.items():
    result[key] = Path(path).exists()

print(json.dumps(result))
EOF
)

# 7. Idempotency check
echo ""
echo "[7/7] Idempotency Check..."
COMMIT_RESP2=$(curl -s -X POST "${BASE_URL}/orchestrate/run?commit=true" \
    -H 'content-type: application/json' \
    -d '{"preset":"smoke","collection":"fiqa_para_50k","overrides":{"sample":40,"top_k":10,"concurrency":2}}')

RUN_ID2=$(echo "$COMMIT_RESP2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('run_id', ''))" 2>/dev/null || echo "")
IDEMPOTENT="false"
if [ "$RUN_ID" = "$RUN_ID2" ] && [ -n "$RUN_ID" ]; then
    IDEMPOTENT="true"
fi
echo "  Run 1 ID: $RUN_ID"
echo "  Run 2 ID: $RUN_ID2"
echo "  Idempotent: $IDEMPOTENT"

# Generate final JSON report
echo ""
echo "=========================================="
echo "FINAL REPORT"
echo "=========================================="

python3 <<EOF
import json

report = {
    "health": {
        "ready": $([ "$READY_OK" = "True" ] && echo "True" || echo "False"),
        "embeddings": $([ "$EMBED_OK" = "True" ] && echo "True" || echo "False")
    },
    "run": {
        "run_id": "$RUN_ID",
        "stage": "$STAGE",
        "status": "$STATUS",
        "queue_pos": $QUEUE_POS,
        "started_at": "$STARTED_AT",
        "finished_at": "$FINISHED_AT"
    },
    "report": {
        "sla_verdict": "$SLA_VERDICT",
        "artifacts": {
            "winners_json": "$WINNERS_JSON",
            "winners_md": "$WINNERS_MD",
            "pareto_png": "$PARETO_PNG",
            "ab_diff_png": "$AB_DIFF_PNG",
            "fail_topn_csv": "$FAIL_TOPN_CSV",
            "events_jsonl": "$EVENTS_JSONL"
        },
        "files_exist": $FILES_EXIST_JSON
    },
    "idempotent_check": "$IDEMPOTENT",
    "notes": ""
}

print(json.dumps(report, indent=2))
EOF

