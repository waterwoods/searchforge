#!/bin/bash
# Restore 8001 live readiness when embedding_warming never clears.
# ================================================================
# Use when: /api/query returns 503 embedding_warming (Qdrant Cloud paused or unreachable).
# Fix: Restart backend with USE_LOCAL_QDRANT=1 (requires local Qdrant + seeded collection).
#
# Prerequisites:
#   docker compose up -d qdrant
#   bash scripts/seed_local_qdrant.sh  # or ensure auto_insurance_demo_core exists
#
# Usage: bash scripts/restore_8001_readiness.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT=8001
READY_URL="http://127.0.0.1:$PORT/ready"
MAX_WAIT=90

cd "$REPO_DIR"

# 1. Kill existing process on 8001
echo "[1] Stopping any existing backend on $PORT..."
PID=$(lsof -ti :$PORT 2>/dev/null || true)
if [ -n "$PID" ]; then
  kill $PID 2>/dev/null || true
  sleep 2
  echo "  Stopped PID $PID"
else
  echo "  No process on $PORT"
fi
echo ""

# 2. Load env
if [ -f ".env" ]; then set -a; source .env; set +a; fi
if [ -f ".env.cloudrun" ]; then set -a; source .env.cloudrun; set +a; fi

# 3. Force local Qdrant
export USE_LOCAL_QDRANT=1
unset QDRANT_URL
unset QDRANT_API_KEY
export QDRANT_HOST="${QDRANT_HOST:-localhost}"
export QDRANT_PORT="${QDRANT_PORT:-6333}"
echo "[2] Starting backend with USE_LOCAL_QDRANT=1 (Qdrant at $QDRANT_HOST:$QDRANT_PORT)..."
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port $PORT 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
echo ""

# 4. Wait for /ready
echo "[3] Waiting for /ready (max ${MAX_WAIT}s)..."
ELAPSED=0
READY=false
while [ $ELAPSED -lt $MAX_WAIT ]; do
  if curl -sf "$READY_URL" >/dev/null 2>&1; then
    echo "  OK: Backend ready at $READY_URL"
    READY=true
    break
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
  echo "  ... waiting (${ELAPSED}s)"
done

if [ "$READY" = false ]; then
  echo "  FAIL: Backend did not become ready. Check logs for warmup errors."
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi
echo ""

# 5. Quick validation
echo "[4] Quick validation (Q1)..."
R=$(curl -s -X POST "http://127.0.0.1:$PORT/api/query" -H "Content-Type: application/json" \
  -d '{"question":"我刚买了辆新车（加州），最低需要买哪些保险？","mode":"demo","top_k":5,"generate_answer":true}')
if echo "$R" | grep -q '"ok":true'; then
  if echo "$R" | grep -q '经纪人下一步'; then
    echo "  OK: Live answer includes workflow-depth (客户可准备, 经纪人可进一步询问, 经纪人下一步)"
  else
    echo "  WARN: Live answer missing 经纪人下一步"
  fi
else
  echo "  FAIL: /api/query did not return ok:true"
  echo "$R" | head -c 200
  exit 1
fi
echo ""

echo "=========================================="
echo "8001 readiness restored"
echo "=========================================="
echo "  Run: python3 scripts/broker_regression_all5.py --port $PORT --report /tmp/broker_report.md"
echo "  Demo: http://localhost:5173/demo (start UI with: cd ui && npm run dev)"
echo "  Runtime path standard: docs/runbooks/RUNTIME_PATH_STANDARD.md"
echo ""
