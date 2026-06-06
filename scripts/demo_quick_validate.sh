#!/bin/bash
# Unified Intake validation (product default) or legacy RAG Q1–Q5 (lab only)
# ========================================================================
# Product path (default): inbox triage API smoke when backend is up.
# Lab path (RUN_DEMO_LAB=1 or platform_full): broker_regression_all5 via /api/query.
#
# Usage: bash scripts/demo_quick_validate.sh [--port PORT]
#   --port: backend port (default 8001 = run_demo_local path; use 8000 for Docker rag-api)
#
# Demo path: run_demo_local.sh → 8001. Docker lab → 8000 with RUN_DEMO_LAB=1.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${PORT:-8001}"
BASE="http://127.0.0.1:$PORT"

while [[ $# -gt 0 ]]; do
  case $1 in
    --port) PORT="$2"; BASE="http://127.0.0.1:$PORT"; shift 2 ;;
    *) shift ;;
  esac
done

TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
OUT_DIR="$REPO_DIR/results/demo_quick_validate/$TIMESTAMP"
mkdir -p "$OUT_DIR"

cd "$REPO_DIR"

# Load env for product_only detection
for f in .env .env.cloudrun; do
  [ -f "$f" ] && set -a && source "$f" 2>/dev/null && set +a
done
if [ "${RUN_DEMO_LAB:-0}" != "1" ]; then
  export UNIFIED_INTAKE_PRODUCT_ONLY="${UNIFIED_INTAKE_PRODUCT_ONLY:-1}"
fi
LAB_MODE=false
case "${UNIFIED_INTAKE_PRODUCT_ONLY:-0}" in 1|true|yes|on) ;; *) LAB_MODE=true ;; esac
if [ "${RUN_DEMO_LAB:-0}" = "1" ]; then
  LAB_MODE=true
fi

# Health check (write report on failure with fix suggestion)
echo "[0] Health check $BASE/healthz..."
if ! curl -sf "$BASE/healthz" > /dev/null 2>&1; then
  echo "  FAIL: Backend not responding at $BASE"
  mkdir -p "$OUT_DIR"
  {
    echo "# Demo Quick Validate Report"
    echo ""
    echo "## Summary"
    echo ""
    echo "**Overall: FAIL (Backend unreachable)**"
    echo ""
    echo "## Why"
    echo ""
    echo "The backend at $BASE did not respond to /healthz. Quick validate requires a running backend."
    echo ""
    echo "## Minimal fix"
    echo ""
    echo "1. **Start backend + UI:**"
    echo '   ```bash'
    echo "   bash scripts/run_demo_local.sh"
    echo '   ```'
    echo "   Wait until workbench URL is printed."
    echo ""
    echo "2. **In another terminal, run validate:**"
    echo '   ```bash'
    echo "   bash scripts/demo_quick_validate.sh"
    echo '   ```'
    echo ""
    if [ "$LAB_MODE" = true ]; then
      echo "3. **Lab/RAG offline:** Open http://localhost:5173/demo — click 5 sample questions."
    else
      echo "3. **Intake guardrail (no server):** bash scripts/guardrail_inbox_triage.sh"
    fi
  } > "$OUT_DIR/REPORT.md"
  echo ""
  echo "=========================================="
  echo "Report: $OUT_DIR/REPORT.md"
  echo "=========================================="
  exit 1
fi
echo "  OK"
echo ""

if [ "$LAB_MODE" = true ]; then
  echo "[1] Lab mode: validating Q1–Q5 RAG scenarios (broker_regression_all5)..."
  echo "    (Product-only default uses intake API — omit RUN_DEMO_LAB / set PRODUCT_ONLY=1)"
  python3 "$SCRIPT_DIR/broker_regression_all5.py" --port "${PORT}" --out "$OUT_DIR/results.json" --report "$OUT_DIR/REPORT.md"
  EXIT=$?

  if [ $EXIT -eq 0 ]; then
    echo ""
    echo "[2] Refreshing offline pack (demo_fallback.json)..."
    if python3 "$SCRIPT_DIR/snapshot_demo_answers.py" --port "${PORT}"; then
      echo "  OK: Offline pack updated"
    else
      echo "  WARN: Snapshot failed (offline pack unchanged)"
    fi
  fi
else
  echo "[1] Intake mode: validating inbox triage API..."
  {
    echo "# Demo Quick Validate Report (Unified Intake)"
    echo ""
    echo "## Summary"
    echo ""
  } > "$OUT_DIR/REPORT.md"
  if PYTHONPATH=. python3 "$SCRIPT_DIR/test_inbox_triage_api.py" --url "$BASE" 2>&1 | tee "$OUT_DIR/intake_api.log"; then
    echo "" >> "$OUT_DIR/REPORT.md"
    echo "**Overall: PASS** (inbox triage API)" >> "$OUT_DIR/REPORT.md"
    echo "" >> "$OUT_DIR/REPORT.md"
    echo "Validated: POST /api/inbox/triage (product surface)." >> "$OUT_DIR/REPORT.md"
    echo "Lab RAG Q1–Q5: use RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh then re-run this script." >> "$OUT_DIR/REPORT.md"
    EXIT=0
  else
    echo "" >> "$OUT_DIR/REPORT.md"
    echo "**Overall: FAIL** (inbox triage API)" >> "$OUT_DIR/REPORT.md"
    EXIT=1
  fi
  echo ""
  echo "[2] Readiness posture..."
  bash "$SCRIPT_DIR/summarize_readiness_posture.sh" --probe "$BASE" 2>&1 | tee "$OUT_DIR/readiness.log" || true
fi

echo ""
echo "=========================================="
echo "Report: $OUT_DIR/REPORT.md"
echo "=========================================="
exit $EXIT
