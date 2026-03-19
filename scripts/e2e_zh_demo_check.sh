#!/bin/bash
# E2E Chinese verification for auto-insurance demo
# Verifies: Chinese query -> translation -> retrieval from auto_insurance_demo_core -> Chinese output with citations
#
# Usage: bash scripts/e2e_zh_demo_check.sh [--port PORT]
# Requires:
#   - Backend running (must connect to Qdrant Cloud for auto_insurance_demo_core; Docker backend uses local Qdrant)
#   - Start backend: set -a; source .env.cloudrun; set +a
#   - TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
#
# Default port 8001 = run_demo_local path. Use --port 8000 for Docker backend.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${PORT:-8001}"
BASE="http://127.0.0.1:$PORT"

# Parse --port
while [[ $# -gt 0 ]]; do
  case $1 in
    --port) PORT="$2"; BASE="http://127.0.0.1:$PORT"; shift 2 ;;
    *) shift ;;
  esac
done

# Create timestamped output dir
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
OUT_DIR="$REPO_DIR/results/e2e_zh_demo/$TIMESTAMP"
mkdir -p "$OUT_DIR"

cd "$REPO_DIR"

# Load env (do not override if already set)
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi
if [ -f ".env.cloudrun" ]; then
  set -a
  source .env.cloudrun
  set +a
fi

echo "=========================================="
echo "E2E Chinese Demo Verification"
echo "=========================================="
echo "  Base URL: $BASE"
echo "  Output:   $OUT_DIR"
echo ""

# Step 1: Health check
echo "[1] Health check..."
if ! curl -sf "$BASE/healthz" > /dev/null 2>&1; then
  echo "  FAIL: Backend not responding at $BASE/healthz"
  echo ""
  echo "  Start backend:"
  echo "    set -a; source .env.cloudrun; set +a"
  echo "    TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port $PORT"
  echo ""
  exit 1
fi
echo "  OK"
echo ""

# Test queries (Chinese)
declare -a QUERIES=(
  "加州汽车保险最低要求是什么？"
  "责任险bodily injury和property damage最低保额是多少？"
  "新车买保险需要准备哪些信息？"
  "如果车辆注册被暂停，怎么恢复？需要交多少钱？"
  "全险一般包含哪些内容？碰撞险和综合险有什么区别？"
  "USAA 和 GEICO 的责任险一般怎么选？（给出比较角度）"
)

# Step 2: Run 6 curl requests
echo "[2] Running 6 Chinese queries..."
for i in {1..6}; do
  q="${QUERIES[$((i-1))]}"
  echo "  Q$i: ${q:0:40}..."
  payload=$(jq -n --arg q "$q" '{question: $q, mode: "demo", translation_mode: "auto"}')
  curl -sS -X POST "$BASE/api/query" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    -o "$OUT_DIR/q$i.json" \
    -w "" 2>/dev/null || true
done
echo "  Done"
echo ""

# Step 3: Validate and generate report
echo "[3] Validating responses and generating report..."
OUT_DIR="$OUT_DIR" python3 "$SCRIPT_DIR/e2e_zh_demo_validate.py"

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "E2E verification complete"
echo "=========================================="
echo "  Report: $OUT_DIR/E2E_REPORT.md"
echo "  Raw:    $OUT_DIR/q1.json .. q6.json"
echo ""

exit $EXIT_CODE
