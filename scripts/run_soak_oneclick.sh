#!/usr/bin/env bash
# run_soak_oneclick.sh - One-click 60-minute soak test
# Runs complete pipeline: setup → preflight → mini test → prewarm → 60-min soak

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

QPS=${QPS:-6}
WINDOW=${WINDOW:-1800}  # 30 min per phase
SEED=${SEED:-42}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 60-MINUTE SOAK TEST - ONE-CLICK RUNNER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "QPS: $QPS | Window: ${WINDOW}s/phase | Seed: $SEED"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: Environment Setup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━ Step 1/5: Environment Setup ━━━"
if ! bash "$SCRIPT_DIR/setup_soak_env.sh"; then
  echo "❌ Environment setup failed"
  exit 1
fi
echo ""

# Wait a moment for env to stabilize
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: Preflight Checks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━ Step 2/5: Preflight Checks ━━━"
if ! bash "$SCRIPT_DIR/verify_preflight.sh"; then
  echo "❌ Preflight checks failed"
  echo "Please fix issues and retry"
  exit 1
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: Mini A/B Test (3 minutes)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━ Step 3/5: Mini A/B Test (3 min) ━━━"
if ! bash "$SCRIPT_DIR/run_mini_ab.sh" --qps "$QPS" --window 90 --seed "$SEED"; then
  echo "❌ Mini A/B test failed"
  echo "Check for high error rate or A/B imbalance"
  exit 1
fi
echo ""

# Wait for metrics to settle
sleep 3

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: Prewarm (2 minutes)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━ Step 4/5: Prewarm (2 min) ━━━"
bash "$SCRIPT_DIR/run_prewarm.sh" 120 4
echo ""

# Wait for warmup to settle
sleep 3

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 5: 60-Minute Soak Test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━ Step 5/5: 60-Minute Soak Test ━━━"
echo "⏰ Starting at $(date '+%H:%M:%S')"
echo "⏰ Expected finish: $(date -v+60M '+%H:%M:%S' 2>/dev/null || date -d '+60 minutes' '+%H:%M:%S')"
echo ""

if bash "$SCRIPT_DIR/run_soak_60m.sh" --qps "$QPS" --window "$WINDOW" --seed "$SEED"; then
  VERDICT="✅ PASS"
  EXIT_CODE=0
else
  VERDICT="❌ FAIL"
  EXIT_CODE=1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Final Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏁 ONE-CLICK SOAK TEST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verdict: $VERDICT"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "📄 Output Files:"
echo "  • Summary: reports/SOAK_60M_SUMMARY.txt"
echo "  • Log: /tmp/soak_60m.log"

# Check for alerts
ALERT_COUNT=$(ls -1 "$PROJECT_ROOT/reports"/ALERT_*.txt 2>/dev/null | wc -l | tr -d ' ')
if [[ "$ALERT_COUNT" -gt 0 ]]; then
  echo "  • Alerts: $ALERT_COUNT (see reports/ALERT_*.txt)"
fi

# Check for snapshots
SNAPSHOT_COUNT=$(ls -1 "$PROJECT_ROOT/reports/_snapshots"/*_snapshot.json 2>/dev/null | wc -l | tr -d ' ')
if [[ "$SNAPSHOT_COUNT" -gt 0 ]]; then
  echo "  • Snapshots: $SNAPSHOT_COUNT (see reports/_snapshots/)"
fi

echo ""
echo "📊 Quick View:"
cat "$PROJECT_ROOT/reports/SOAK_60M_SUMMARY.txt" 2>/dev/null || echo "  (Summary not found)"
echo ""

exit $EXIT_CODE

