#!/bin/bash
# Unified Intake — local founder demo launcher
# ===========================================
# Product: inbox triage + workbench (Unified Intake SaaS), not SearchForge lab.
# Default path: backend 8001, UI 5173. Vite proxy targets 8001.
# (Docker rag-api uses 8000 — legacy lab stack; see docs/runbooks/RUNTIME_PATH_STANDARD.md)
# Starts backend (8001) + UI dev server. Prints URLs even if backend fails.
# Ctrl+C stops both gracefully.
#
# Default: Unified Intake SaaS posture (matches paid pilot / trial prep).
# Lab/RAG stack: RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh
#   → platform_full API (SearchForge lab routers, /api/query, etc.)
#
# Usage: bash scripts/run_demo_local.sh
#        RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh   # explicit lab opt-in

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

# P19M-2A: QA SSOT is GCP Cloud SQL (same secret as Cloud Run), not legacy Neon in .env.cloudrun.
# Override SERVICE_RECORD_DATABASE_URL after .env.cloudrun load. JSON dev: RUN_DEMO_LOCAL_DB=json
if [ "${RUN_DEMO_LOCAL_DB:-cloud-sql}" != "json" ]; then
  if CLOUD_SQL_EXPORTS="$(PYTHONPATH=. python3 -c "
import os
from scripts.demo_db_resolve import ensure_h5_task_token_secret, shell_export_qa_postgres_env
ident, lines = shell_export_qa_postgres_env(for_write=True)
ensure_h5_task_token_secret()
if (os.getenv('H5_TASK_TOKEN_SECRET') or '').strip():
    import shlex
    lines.append('export H5_TASK_TOKEN_SECRET=' + shlex.quote(os.environ['H5_TASK_TOKEN_SECRET']))
print('\n'.join(lines))
print('# ident=' + ident.masked())
" 2>/dev/null)"; then
    eval "$(printf '%s\n' "$CLOUD_SQL_EXPORTS" | grep -v '^# ident=')"
    CLOUD_SQL_IDENT="$(printf '%s\n' "$CLOUD_SQL_EXPORTS" | grep '^# ident=' | sed 's/^# ident=//')"
    echo "[INFO] Case store: GCP Cloud SQL (QA SSOT) — ${CLOUD_SQL_IDENT:-configured}"
  else
    echo "[WARN] Cloud SQL env unavailable (gcloud auth?). Set RUN_DEMO_LOCAL_DB=json for JSON-only dev."
    echo "       Prototype QA requires Cloud SQL — see scripts/demo_db_resolve.py"
  fi
else
  echo "[WARN] RUN_DEMO_LOCAL_DB=json — local JSON case store (NOT Cloud Run / prototype QA parity)"
  unset SERVICE_RECORD_DATABASE_URL DATABASE_URL QA_SERVICE_RECORD_DATABASE_URL
  export UNIFIED_INTAKE_DB_PRIMARY_READS=0
  export UNIFIED_INTAKE_DB_PRIMARY_WRITES=0
  export UNIFIED_INTAKE_JSON_CASE_WRITES=1
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
echo "Unified Intake — Local Demo (8001 + UI 5173)"
echo "=========================================="
echo ""
echo "[NOTICE] LOCAL DEV ONLY — not the Chen Kui formal demo path."
echo "         Primary demo: https://ui-smoky-beta.vercel.app/workbench/unified-intake"
echo "         See: docs/runbooks/CHEN_KUI_DEMO_ENVIRONMENT.md"
echo "         If localhost:5173 shows ERR_EMPTY_RESPONSE, this script is not running."
echo ""

# Default to paid-pilot parity unless explicit lab opt-in (RUN_DEMO_LAB=1).
if [ "${RUN_DEMO_LAB:-0}" = "1" ]; then
  echo "[MODE] Lab opt-in (RUN_DEMO_LAB=1): platform_full API — SearchForge/RAG routers."
  echo "       Workbench intake still works; /api/query and lab routes available."
  echo ""
else
  export UNIFIED_INTAKE_PRODUCT_ONLY="${UNIFIED_INTAKE_PRODUCT_ONLY:-1}"
  export UNIFIED_INTAKE_INTAKE_CORE_READINESS="${UNIFIED_INTAKE_INTAKE_CORE_READINESS:-1}"
  echo "[MODE] Unified Intake SaaS (default). Lab stack: RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh"
  echo "       product_only=${UNIFIED_INTAKE_PRODUCT_ONLY} intake_core_readiness=${UNIFIED_INTAKE_INTAKE_CORE_READINESS}"
  echo ""
fi

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
  echo "  NOTE: Backend did not become healthy."
  if [ "${RUN_DEMO_LAB:-0}" = "1" ]; then
    echo "        RAG /demo page can use Offline Fallback (5 sample questions)."
  else
    echo "        Workbench needs backend — check logs; bash scripts/trial_launch_check.sh"
  fi
  kill "$BACKEND_PID" 2>/dev/null || true
  BACKEND_PID=""
fi
echo ""

# Start UI (always) — Vite 7 requires Node 22 (see docs/runbooks/NODE_22_SETUP.md)
echo "[3] Starting UI dev server..."
NODE22_HELPER="$SCRIPT_DIR/with_node22_path.sh"
if [ -z "${SKIP_NVM_NODE22_FOR_UI:-}" ] && [ -f "$NODE22_HELPER" ]; then
  echo "[INFO] Loading Node 22 helper…"
  # shellcheck disable=SC1090
  source "$NODE22_HELPER"
  echo "[INFO] Node version: $(node -v)"
elif [ -z "${SKIP_NVM_NODE22_FOR_UI:-}" ]; then
  echo "[WARN] Node 22 helper not found at $NODE22_HELPER"
  if command -v node >/dev/null 2>&1; then
    echo "[WARN] Using PATH node: $(node -v) — Vite 7 needs Node >= 20.19 or >= 22.12"
  else
    echo "[WARN] node not on PATH — UI dev server may fail"
  fi
else
  echo "[INFO] SKIP_NVM_NODE22_FOR_UI=1 — using PATH node: $(node -v 2>/dev/null || echo 'not found')"
fi
cd "$REPO_DIR/ui"
npm run dev &
UI_PID=$!
echo "  UI PID: $UI_PID"
cd "$REPO_DIR"
echo ""

# Give UI a moment to bind
sleep 3
echo "=========================================="
echo "Unified Intake local — ready"
echo "=========================================="
echo ""
echo "  Workbench (product): http://localhost:5173/workbench/unified-intake"
echo "  RAG demo page (optional wedge): $DEMO_URL"
echo ""
if [ "$BACKEND_OK" = true ]; then
  echo "  Mode: Live (backend connected)"
  echo "  Posture: bash scripts/summarize_readiness_posture.sh --probe http://127.0.0.1:8001"
  echo "  Validate: bash scripts/guardrail_inbox_triage.sh"
else
  echo "  Mode: Backend down — start failed or still warming"
fi
echo ""
echo "  Before broker trial: bash scripts/trial_launch_check.sh"
echo "  Safe to ignore: docs/runbooks/OPERATOR_IGNORE_LIST.md"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

# Wait for UI (or user interrupt)
wait $UI_PID 2>/dev/null || true
