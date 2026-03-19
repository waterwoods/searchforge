#!/bin/bash
# Unified broker validation: Q1–Q5 core scenarios
# ===============================================
# Runs broker_regression_all5.py to validate all 5 broker questions.
# Writes report to results/demo_quick_validate/YYYY-MM-DD_HHMMSS/REPORT.md
#
# Usage: bash scripts/demo_quick_validate.sh [--port PORT]
#   --port: backend port (default 8001 = run_demo_local path; use 8000 for Docker rag-api)
#
# Demo path: run_demo_local.sh → 8001. Docker → 8000.

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
    echo "The backend at $BASE did not respond to /healthz. Quick validate requires a running backend to test the 5 broker scenarios."
    echo ""
    echo "## Minimal fix"
    echo ""
    echo "1. **Start backend + UI:**"
    echo '   ```bash'
    echo "   bash scripts/run_demo_local.sh"
    echo '   ```'
    echo "   Wait until \"Demo ready\" and Demo URL is printed."
    echo ""
    echo "2. **In another terminal, run validate:**"
    echo '   ```bash'
    echo "   bash scripts/demo_quick_validate.sh"
    echo '   ```'
    echo ""
    echo "3. **If backend still fails:** Demo works in Offline mode. Open the Demo URL, click the 5 sample questions to load pre-saved answers. No backend needed."
  } > "$OUT_DIR/REPORT.md"
  echo ""
  echo "=========================================="
  echo "Report: $OUT_DIR/REPORT.md"
  echo "=========================================="
  exit 1
fi
echo "  OK"
echo ""

# Run unified 5-question broker regression
echo "[1] Validating Q1–Q5 (broker_regression_all5)..."
python3 "$SCRIPT_DIR/broker_regression_all5.py" --port "${PORT}" --out "$OUT_DIR/results.json" --report "$OUT_DIR/REPORT.md"
EXIT=$?

# On PASS: refresh offline pack so demo_fallback.json stays aligned with validated scenarios
if [ $EXIT -eq 0 ]; then
  echo ""
  echo "[2] Refreshing offline pack (demo_fallback.json)..."
  if python3 "$SCRIPT_DIR/snapshot_demo_answers.py" --port "${PORT}"; then
    echo "  OK: Offline pack updated"
  else
    echo "  WARN: Snapshot failed (offline pack unchanged)"
  fi
fi

echo ""
echo "=========================================="
echo "Report: $OUT_DIR/REPORT.md"
echo "=========================================="
exit $EXIT
