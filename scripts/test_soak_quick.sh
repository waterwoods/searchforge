#!/usr/bin/env bash
# test_soak_quick.sh - Quick validation test (5 minutes)
# Tests the complete soak pipeline with reduced duration
# NOT a substitute for the full 60-minute test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 QUICK VALIDATION TEST (5 minutes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  This is a quick validation test, NOT a full soak test"
echo ""

# Step 1: Setup
echo "━━━ Step 1/5: Environment Setup ━━━"
if ! bash "$SCRIPT_DIR/setup_soak_env.sh"; then
  echo "❌ Setup failed"
  exit 1
fi
echo ""

sleep 2

# Step 2: Preflight
echo "━━━ Step 2/5: Preflight Checks ━━━"
if ! bash "$SCRIPT_DIR/verify_preflight.sh"; then
  echo "❌ Preflight failed"
  exit 1
fi
echo ""

# Step 3: Mini test (reduced)
echo "━━━ Step 3/5: Mini A/B Test (60s) ━━━"
if ! bash "$SCRIPT_DIR/run_mini_ab.sh" --qps 6 --window 60 --seed 42; then
  echo "❌ Mini test failed"
  exit 1
fi
echo ""

sleep 2

# Step 4: Prewarm (reduced)
echo "━━━ Step 4/5: Prewarm (30s) ━━━"
bash "$SCRIPT_DIR/run_prewarm.sh" 30 4
echo ""

sleep 2

# Step 5: Quick soak (2 min per phase)
echo "━━━ Step 5/5: Quick Soak Test (4 min total) ━━━"
if bash "$SCRIPT_DIR/run_soak_60m.sh" --qps 6 --window 120 --seed 42; then
  VERDICT="✅ PASS"
  EXIT_CODE=0
else
  VERDICT="❌ FAIL"
  EXIT_CODE=1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏁 QUICK VALIDATION COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verdict: $VERDICT"
echo ""
echo "⚠️  Note: This was a quick test (5 min). For production validation,"
echo "   run the full 60-minute test:"
echo "   bash scripts/run_soak_oneclick.sh"
echo ""

exit $EXIT_CODE

