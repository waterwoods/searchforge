#!/bin/bash
# One-command local demo launcher for ChenKui
# ===========================================
# Default demo path: backend 8001, UI 5173. Vite proxy targets 8001.
# (Docker rag-api uses 8000; use --port 8000 for validation scripts when using Docker.)
# Starts backend (8001) + UI dev server. Prints Demo URL even if backend fails.
# If backend is down, DemoPage uses Offline Fallback (pre-saved answers).
# Ctrl+C stops both gracefully.
#
# Usage: bash scripts/run_demo_local.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HEALTH_URL="http://127.0.0.1:8001/healthz"
DEMO_URL="http://localhost:5173/demo"
MAX_WAIT=60

cd "$REPO_DIR"

# Load env
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

# Use local Qdrant when USE_LOCAL_QDRANT=1 (avoids Qdrant Cloud 404 when cluster paused)
if [ "${USE_LOCAL_QDRANT:-0}" = "1" ]; then
  export USE_LOCAL_QDRANT=1
  unset QDRANT_URL
  unset QDRANT_API_KEY
  export QDRANT_HOST="${QDRANT_HOST:-localhost}"
  export QDRANT_PORT="${QDRANT_PORT:-6333}"
  echo "[INFO] USE_LOCAL_QDRANT=1: using local Qdrant at $QDRANT_HOST:$QDRANT_PORT (ensure 'docker compose up -d qdrant' and collection auto_insurance_demo_core is seeded)"
fi

echo "=========================================="
echo "Demo Launcher (Backend 8001 + UI 5173)"
echo "=========================================="
echo ""

# Cleanup on exit
BACKEND_PID=""
UI_PID=""
cleanup() {
  echo ""
  echo "[Cleanup] Stopping services..."
  if [ -n "$UI_PID" ] && kill -0 "$UI_PID" 2>/dev/null; then
    kill "$UI_PID" 2>/dev/null || true
    echo "  UI stopped (PID $UI_PID)"
  fi
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    echo "  Backend stopped (PID $BACKEND_PID)"
  fi
  exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend (best-effort; do not fail if it doesn't start)
echo "[1] Starting backend on 8001..."
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
echo ""

# Health check loop (non-fatal; proceed to UI even if backend fails)
echo "[2] Waiting for backend health (max ${MAX_WAIT}s)..."
ELAPSED=0
BACKEND_OK=false
while [ $ELAPSED -lt $MAX_WAIT ]; do
  if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "  OK: Backend healthy at $HEALTH_URL"
    BACKEND_OK=true
    break
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
  echo "  ... waiting (${ELAPSED}s)"
done
if [ "$BACKEND_OK" = false ]; then
  echo "  NOTE: Backend did not become healthy. Demo will use Offline Fallback."
  echo "        Click the 5 sample questions to load pre-saved answers."
  kill "$BACKEND_PID" 2>/dev/null || true
  BACKEND_PID=""
fi
echo ""

# Start UI (always)
echo "[3] Starting UI dev server..."
cd "$REPO_DIR/ui"
npm run dev &
UI_PID=$!
echo "  UI PID: $UI_PID"
cd "$REPO_DIR"
echo ""

# Give UI a moment to bind
sleep 3
echo "=========================================="
echo "Demo ready"
echo "=========================================="
echo ""
echo "  Demo URL: $DEMO_URL"
echo ""
if [ "$BACKEND_OK" = true ]; then
  echo "  Mode: Live (backend connected)"
else
  echo "  Mode: Offline (backend down - use 5 sample questions for pre-saved answers)"
fi
echo ""
echo "  Press Ctrl+C to stop."
echo ""

# Wait for UI (or user interrupt)
wait $UI_PID 2>/dev/null || true
