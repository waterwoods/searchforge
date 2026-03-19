#!/bin/bash
# Founder Pre-Trial Checklist — One Command Before Broker Meeting
# ==============================================================
# Runs trial readiness check + prints founder pre-trial steps.
# Usage: bash scripts/founder_pre_trial_checklist.sh
#
# After this: Open http://localhost:5173/workbench/unified-intake
#             Load founder demo queue → SIM1–SIM3 → first real case

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "=== Founder Pre-Trial Checklist ==="
echo ""

# Run full trial readiness check
if ! bash "$SCRIPT_DIR/trial_readiness_check.sh" 2>/dev/null; then
  echo ""
  echo "  Fix the above failures before approaching broker."
  exit 1
fi

echo ""
echo "=== Pre-Trial Steps (Manual) ==="
echo ""
echo "  1. Run: bash scripts/run_demo_local.sh"
echo "  2. Open: http://localhost:5173/workbench/unified-intake"
echo "  3. Click: Load founder demo queue (13 cases; cancellation opens first)"
echo "  4. Run SIM1, SIM2, SIM3 in Simulation Assistant"
echo "  5. Copy docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md for broker"
echo "  6. Read docs/trial/BROKER_TRIAL_WORKFLOW_SPEC.md"
echo "  7. Read docs/trial/FOUNDER_FINAL_TRIAL_NOTES.md (inspect, say, watch for)"
echo ""
echo "  What to say (first 30 sec):"
echo "  \"这是一个加州汽车保险经纪助手。客户发来messy消息——系统会整理成结构化case："
echo "  有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。\""
echo ""
echo "  Demo path: Load founder demo queue → Cancellation risk → Missing doc → Add-car → SIM1–SIM3"
echo ""
echo "  Docs: docs/trial/FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md"
echo "       docs/trial/FOUNDER_FINAL_TRIAL_NOTES.md (inspect, say, watch for)"
echo ""
echo "  Handoff check: Verify 'Your next move' appears first (before Recent customer messages)"
echo ""
