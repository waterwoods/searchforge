#!/usr/bin/env bash
# Cutover to remote with SLA gate and auto-rollback

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

REMOTE=${REMOTE:-andy-wsl}
COMPOSE_DIR=${COMPOSE_DIR:-~/searchforge}
PROJECT=${PROJECT:-searchforge}

# Trap for auto-rollback on error
trap 'echo "[rollback] auto"; cp .env.local .env.current 2>/dev/null || true; docker compose --env-file .env.current -p "$PROJECT" up -d 2>/dev/null || true' ERR INT

# Refresh hostname mapping before remote checks
echo "[0/6] Refreshing hostname mapping..."
bash tools/switch/update_hosts.sh || {
    echo "⚠️  Warning: update_hosts.sh failed (may need sudo), continuing if hostname already configured..."
}
echo ""

# Ensure directories exist
MANIFESTS_DIR="artifacts/sla/manifests"
mkdir -p "$MANIFESTS_DIR"
mkdir -p "artifacts/sla"

# Get current git SHA
GIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ISO_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
MANIFEST_FILE="${MANIFESTS_DIR}/${TIMESTAMP}.json"

echo "=================================================="
echo "🚀 Cutover to Remote with SLA Gate"
echo "=================================================="
echo ""

# Step 1: Freeze writers
echo "[1/6] Freezing local writers..."
if [ -f "./migration_freeze_writers.sh" ]; then
    bash ./migration_freeze_writers.sh || {
        echo "⚠️  Warning: writer freeze script encountered issues (continuing anyway)"
    }
else
    echo "⚠️  Warning: migration_freeze_writers.sh not found (skipping freeze step)"
fi
echo ""

# Step 2: Pre-check remote health
echo "[2/6] Pre-checking remote health..."
if ! curl -fsS --max-time 5 "http://${REMOTE}:8000/health" >/dev/null 2>&1; then
    echo "❌ Error: Remote rag-api /health check failed"
    exit 1
fi

if ! curl -fsS --max-time 5 "http://${REMOTE}:6333/collections" >/dev/null 2>&1; then
    echo "❌ Error: Remote qdrant /collections check failed"
    exit 1
fi
echo "✅ Remote services are healthy"
echo ""

# Step 3: Switch to remote
echo "[3/6] Switching to remote configuration..."
if [ ! -f ".env.remote.template" ]; then
    echo "❌ Error: .env.remote.template not found"
    exit 1
fi

# Get RAG_API_BASE from remote template
RAG_API_BASE=$(grep "^RAG_API_BASE=" .env.remote.template | cut -d'=' -f2- | tr -d '"' || echo "http://${REMOTE}:8000")

cp .env.remote.template .env.current
echo "✅ .env.current updated to remote configuration"
echo "   RAG_API_BASE=${RAG_API_BASE}"
echo ""

# Step 4: Stop local containers
echo "[4/6] Stopping local containers..."
docker compose --env-file .env.current -p "$PROJECT" down
echo "✅ Local containers stopped"
echo ""

# Step 5: Determine baseline file based on target
TARGET=$(grep -E '^SEARCHFORGE_TARGET=' .env.current | cut -d= -f2 || echo "local")
if [[ "$TARGET" == remote* ]]; then
    BASELINE_FILE="artifacts/sla/baseline.remote.json"
    BASELINE_NAME="baseline.remote.json"
else
    BASELINE_FILE="artifacts/sla/baseline.local.json"
    BASELINE_NAME="baseline.local.json"
fi

# Step 6: Run smoke test with safer defaults
echo "[5/6] Running smoke test..."

# Default values
: "${N:=150}"
: "${C:=10}"
: "${WARMUP:=10}"
: "${TIMEOUT:=3}"

echo "  N=${N}, concurrency=${C}, warmup=${WARMUP}, timeout=${TIMEOUT}s"

SMOKE_OUTPUT=$(python3 tools/switch/smoke.py --n "$N" --concurrency "$C" --warmup "$WARMUP" --timeout "$TIMEOUT" --base "$RAG_API_BASE" 2>&1)
SMOKE_EXIT=$?

if [ $SMOKE_EXIT -ne 0 ]; then
    echo "❌ Error: Smoke test failed"
    echo "$SMOKE_OUTPUT"
    SMOKE_RESULT='{"error": "smoke_test_failed", "n": '$N', "warmup": '$WARMUP', "concurrency": '$C', "timeout": '$TIMEOUT', "p95": null, "p50": null, "avg": null, "error_rate": 1.0}'
else
    SMOKE_RESULT="$SMOKE_OUTPUT"
fi

# Parse smoke test results
P95=$(echo "$SMOKE_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('p95', 'null'))" 2>/dev/null || echo "null")
ERROR_RATE=$(echo "$SMOKE_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('error_rate', 1.0))" 2>/dev/null || echo "1.0")
P50=$(echo "$SMOKE_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('p50', 'null'))" 2>/dev/null || echo "null")
AVG=$(echo "$SMOKE_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('avg', 'null'))" 2>/dev/null || echo "null")

echo "Smoke test results:"
echo "  P50: ${P50}ms"
echo "  P95: ${P95}ms"
echo "  Avg: ${AVG}ms"
echo "  Error rate: ${ERROR_RATE}"
echo ""

# Step 7: Compare with baseline
echo "[6/6] Comparing with baseline..."

# Load baseline (required)
if [ -f "$BASELINE_FILE" ]; then
    BASELINE_P95=$(python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('p95', 0))" < "$BASELINE_FILE" 2>/dev/null || echo "0")
    BASELINE_ERROR_RATE=$(python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('error_rate', 0))" < "$BASELINE_FILE" 2>/dev/null || echo "0")
    echo "Baseline (${BASELINE_NAME}): P95=${BASELINE_P95}ms, Error rate=${BASELINE_ERROR_RATE}"
else
    echo "❌ Error: Baseline file not found at $BASELINE_FILE"
    echo "   Please create baseline first:"
    if [[ "$TARGET" == remote* ]]; then
        echo "     make baseline-save-remote"
    else
        echo "     make baseline-save-local"
    fi
    exit 1
fi

# Check SLA criteria
SLA_FAILED=false
FAIL_REASONS=()

if [ "$P95" != "null" ] && [ "$BASELINE_P95" != "0" ] && [ "$BASELINE_P95" != "null" ]; then
    # Compare P95 (allow 10% increase)
    THRESHOLD=$(python3 -c "print(${BASELINE_P95} * 1.10)" 2>/dev/null || echo "999999")
    if [ "$(python3 -c "print(1 if ${P95} > ${THRESHOLD} else 0)" 2>/dev/null || echo "1")" -eq 1 ]; then
        SLA_FAILED=true
        FAIL_REASONS+=("P95 ${P95}ms exceeds threshold ${THRESHOLD}ms (baseline: ${BASELINE_P95}ms)")
    fi
fi

# Check error rate (must be <= 1%)
ERROR_RATE_PCT=$(python3 -c "print(${ERROR_RATE} * 100)" 2>/dev/null || echo "100")
if [ "$(python3 -c "print(1 if ${ERROR_RATE} > 0.01 else 0)" 2>/dev/null || echo "1")" -eq 1 ]; then
    SLA_FAILED=true
    FAIL_REASONS+=("Error rate ${ERROR_RATE_PCT}% exceeds 1%")
fi

# Rollback if SLA failed (trap will handle rollback)
if [ "$SLA_FAILED" = true ]; then
    echo ""
    echo "❌ SLA CHECK FAILED"
    for reason in "${FAIL_REASONS[@]}"; do
        echo "   - $reason"
    done
    echo ""
    
    # Create manifest with rollback status before exit
    # Build fail_reasons JSON array
    if [ ${#FAIL_REASONS[@]} -eq 0 ]; then
        FAIL_REASONS_JSON="[]"
    else
        FAIL_REASONS_JSON="["
        for i in "${!FAIL_REASONS[@]}"; do
            if [ $i -gt 0 ]; then
                FAIL_REASONS_JSON+=", "
            fi
            FAIL_REASONS_JSON+="$(python3 -c "import json; print(json.dumps('${FAIL_REASONS[$i]}'))")"
        done
        FAIL_REASONS_JSON+="]"
    fi
    
    python3 <<PYTHON_SCRIPT > "$MANIFEST_FILE"
import json
import datetime

try:
    metrics = json.loads(r'''${SMOKE_RESULT}''')
except Exception as e:
    metrics = {"error": f"failed_to_parse_smoke_result: {e}"}

import json as json_module
fail_reasons_list = json_module.loads(r'''${FAIL_REASONS_JSON}''')

baseline = None
try:
    baseline_p95_str = '${BASELINE_P95}'
    if baseline_p95_str not in ('null', '0', ''):
        baseline = {
            "p95": float(baseline_p95_str),
            "error_rate": float('${BASELINE_ERROR_RATE}')
        }
except:
    pass

manifest = {
    "timestamp": "${TIMESTAMP}",
    "iso_timestamp": "${ISO_TIMESTAMP}",
    "git_sha": "${GIT_SHA}",
    "target": "${TARGET}",
    "baseline_name": "${BASELINE_NAME}",
    "result": "ROLLBACK",
    "sla_passed": False,
    "fail_reasons": fail_reasons_list,
    "N": ${N},
    "C": ${C},
    "WARMUP": ${WARMUP},
    "TIMEOUT": ${TIMEOUT},
    "p50": ${P50} if "${P50}" != "null" else None,
    "p95": ${P95} if "${P95}" != "null" else None,
    "avg": ${AVG} if "${AVG}" != "null" else None,
    "error_rate": ${ERROR_RATE},
    "metrics": metrics,
    "baseline": baseline
}

print(json.dumps(manifest, indent=2))
PYTHON_SCRIPT
    
    echo "📝 Manifest written to: $MANIFEST_FILE"
    echo ""
    echo "🔄 Auto-rollback will be triggered by trap..."
    exit 1
fi

# SLA passed
echo ""
echo "✅ SLA CHECK PASSED"
echo "   P95: ${P95}ms (threshold: ${THRESHOLD}ms)"
echo "   Error rate: ${ERROR_RATE_PCT}% (threshold: 1%)"
echo ""

# Create success manifest
python3 <<PYTHON_SCRIPT > "$MANIFEST_FILE"
import json
import datetime

try:
    metrics = json.loads(r'''${SMOKE_RESULT}''')
except Exception as e:
    metrics = {"error": f"failed_to_parse_smoke_result: {e}"}

baseline = None
try:
    baseline_p95_str = '${BASELINE_P95}'
    if baseline_p95_str not in ('null', '0', ''):
        baseline = {
            "p95": float(baseline_p95_str),
            "error_rate": float('${BASELINE_ERROR_RATE}')
        }
except:
    pass

manifest = {
    "timestamp": "${TIMESTAMP}",
    "iso_timestamp": "${ISO_TIMESTAMP}",
    "git_sha": "${GIT_SHA}",
    "target": "${TARGET}",
    "baseline_name": "${BASELINE_NAME}",
    "result": "PASS",
    "sla_passed": True,
    "N": ${N},
    "C": ${C},
    "WARMUP": ${WARMUP},
    "TIMEOUT": ${TIMEOUT},
    "p50": ${P50} if "${P50}" != "null" else None,
    "p95": ${P95} if "${P95}" != "null" else None,
    "avg": ${AVG} if "${AVG}" != "null" else None,
    "error_rate": ${ERROR_RATE},
    "metrics": metrics,
    "baseline": baseline
}

print(json.dumps(manifest, indent=2))
PYTHON_SCRIPT

echo "📝 Manifest written to: $MANIFEST_FILE"
echo ""
echo "=================================================="
echo "✅ Cutover SUCCESS"
echo "=================================================="
echo ""
echo "Summary:"
echo "  Status: PASS"
echo "  P95: ${P95}ms"
echo "  Error rate: ${ERROR_RATE_PCT}%"
echo "  Target: ${TARGET}"
echo "  Baseline: ${BASELINE_NAME}"
echo "  Manifest: $MANIFEST_FILE"
