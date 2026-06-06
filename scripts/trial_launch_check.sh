#!/bin/bash
# Trial Launch Check — Single Entry Point for Real Broker Trial
# ==============================================================
# CANONICAL FOUNDER PATH: docs/FOUNDER_ONE_PATH.md
# Runs trial readiness + prints founder launch checklist.
# One command before launching the first broker trial.
#
# Usage: bash scripts/trial_launch_check.sh
#
# After PASS: Open http://localhost:5173/workbench/unified-intake
#             Load founder demo queue → SIM1–SIM3 → first real case

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "=== Trial Launch Check — Single Entry Point ==="
echo ""

# Run full trial readiness check
if ! bash "$SCRIPT_DIR/trial_readiness_check.sh" 2>/dev/null; then
  echo ""
  echo "  Fix the above failures before launching trial."
  exit 1
fi

# Verify launch-specific docs exist (P9 collapsed surface)
echo "[Launch] Launch docs exist..."
for f in docs/FOUNDER_ONE_PATH.md \
         docs/TRIAL_ONE_PATH.md \
         docs/BROKER_ONE_PAGER.md \
         docs/BROKER_TRIAL_PLAYBOOK.md \
         docs/trial/FIX_NOW_QUEUE_TEMPLATE.md \
         docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md; do
  if [ ! -f "$f" ]; then
    echo "  FAIL: $f not found"
    exit 1
  fi
done
echo "  OK (6 launch docs)"

# Verify results/trial_logs exists and is writable
if [ ! -d "results/trial_logs" ]; then
  mkdir -p results/trial_logs
  echo "  Created results/trial_logs"
fi
echo "  OK (trial_logs ready)"

echo ""
echo "=== Trial Launch Check: PASS ==="
echo ""
echo "--- Founder Launch Checklist (Manual) ---"
echo ""
echo "  1. Run: bash scripts/run_demo_local.sh"
echo "  2. Open: http://localhost:5173/workbench/unified-intake"
echo "  3. Click: Load founder demo queue (13 cases; cancellation opens first)"
echo "  4. Run SIM1, SIM2, SIM3 in Simulation Assistant"
echo "  5. Copy docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md for broker"
echo "  6. Bring docs/BROKER_ONE_PAGER.md + docs/BROKER_TRIAL_PLAYBOOK.md"
echo "  7. Read docs/TRIAL_ONE_PATH.md + docs/FOUNDER_ONE_PATH.md"
echo ""
echo "  Archived kickoff specs: docs/archive/p9_broker_surface/kickoff/ (optional depth)"
echo ""
echo "  What to say (first 30 sec):"
echo "  \"这是一个加州汽车保险经纪助手。客户发来messy消息——系统会整理成结构化case："
echo "  有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。\""
echo ""
echo "  Demo path: Load founder demo queue → Cancellation risk → Missing doc → Add-car → SIM1–SIM3"
echo "  Evidence: Click 'Copy case snapshot' on any case → paste into observation log"
echo ""
echo "  Post-trial: docs/trial/FIX_NOW_QUEUE_TEMPLATE.md → results/trial_logs/"
echo ""
echo "--- End Checklist ---"
echo ""
