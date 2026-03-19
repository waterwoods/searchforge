#!/bin/bash
# Demo prepare for tomorrow: quick_validate + regenerate offline pack + report
# ==========================================================================
# 1) Runs demo_quick_validate.sh
# 2) Regenerates ui/src/assets/demo_fallback.json (if backend is up)
# 3) Writes report to results/demo_prepare/YYYY-MM-DD_HHMMSS/REPORT.md
#
# Usage: bash scripts/demo_prepare_tomorrow.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
OUT_DIR="$REPO_DIR/results/demo_prepare/$TIMESTAMP"

cd "$REPO_DIR"
mkdir -p "$OUT_DIR"

echo "=========================================="
echo "Demo Prepare for Tomorrow"
echo "=========================================="
echo ""

# 1) Quick validate (do not fail script on validate failure)
echo "[1] Running demo_quick_validate.sh..."
VALIDATE_PASS=false
bash "$SCRIPT_DIR/demo_quick_validate.sh" 2>&1 | tee "$OUT_DIR/validate_log.txt" || true
LATEST_VALIDATE=$(ls -td results/demo_quick_validate/*/REPORT.md 2>/dev/null | head -1)
if [ -n "$LATEST_VALIDATE" ] && [ -f "$LATEST_VALIDATE" ]; then
  cp "$LATEST_VALIDATE" "$OUT_DIR/validate_REPORT.md"
  grep -q "Overall: PASS" "$OUT_DIR/validate_REPORT.md" 2>/dev/null && VALIDATE_PASS=true
fi
echo ""

# 2) Regenerate offline pack (do not fail on snapshot failure)
echo "[2] Regenerating offline pack (snapshot_demo_answers.py)..."
SNAPSHOT_OK=false
if python3 "$SCRIPT_DIR/snapshot_demo_answers.py" 2>&1 | tee "$OUT_DIR/snapshot_log.txt"; then
  SNAPSHOT_OK=true
else
  echo "  NOTE: Snapshot failed (backend may be down). Using existing demo_fallback.json."
fi
echo ""

# 3) Write report
echo "[3] Writing report..."
{
  echo "# Demo Prepare Report"
  echo ""
  echo "**Timestamp:** $TIMESTAMP"
  echo ""
  echo "## Summary"
  echo ""
  echo "| Step | Status |"
  echo "|------|--------|"
  if [ "$VALIDATE_PASS" = true ]; then
    echo "| Quick validate | PASS |"
  else
    echo "| Quick validate | FAIL (see validate_REPORT.md) |"
  fi
  if [ "$SNAPSHOT_OK" = true ]; then
    echo "| Offline pack | Regenerated |"
  else
    echo "| Offline pack | Skipped (backend down) |"
  fi
  echo ""
  echo "## Tomorrow commands"
  echo ""
  echo "1. Start demo: \`bash scripts/run_demo_local.sh\`"
  echo "2. Demo URL: http://localhost:5173/demo"
  echo "3. If backend down: Click 5 sample questions for Offline mode."
  echo "4. Validate (optional): \`bash scripts/demo_quick_validate.sh\`"
  echo ""
} > "$OUT_DIR/REPORT.md"

echo "=========================================="
echo "Report: $OUT_DIR/REPORT.md"
echo "=========================================="
