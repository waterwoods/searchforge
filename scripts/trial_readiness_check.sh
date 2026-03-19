#!/bin/bash
# Real Broker Trial Package — Readiness Check
# ============================================
# Validates that the trial package is coherent and key scenarios pass.
# Run before approaching a broker for trial.
#
# Usage: bash scripts/trial_readiness_check.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "=== Real Broker Trial Package — Readiness Check ==="
echo ""

echo "[1] Trial package docs exist..."
for f in docs/trial/REAL_BROKER_TRIAL_PACKAGE_BLUEPRINT.md \
         docs/trial/TRIAL_SCOPE_DEFINITION_SPEC.md \
         docs/trial/TRIAL_SCENARIO_PACK_SPEC.md \
         docs/trial/TRIAL_METRICS_SUCCESS_CRITERIA_SPEC.md \
         docs/trial/BROKER_TRIAL_WORKFLOW_SPEC.md \
         docs/trial/FOUNDER_TRIAL_NOTES.md \
         docs/trial/TRIAL_EXECUTION_BLUEPRINT.md \
         docs/trial/LAST_MILE_RISK_SPEC.md \
         docs/trial/FOUNDER_BROKER_TRIAL_RUNBOOK_SPEC.md \
         docs/trial/HANDOFF_OFFICE_NEXT_ACTION_SPEC.md \
         docs/trial/TRIAL_OBSERVATION_TO_ITERATION_SPEC.md \
         docs/trial/FOUNDER_FINAL_TRIAL_NOTES.md; do
  if [ ! -f "$f" ]; then
    echo "  FAIL: $f not found"
    exit 1
  fi
done
echo "  OK (12 core docs)"

echo "[2] Standard Scenario Package defined..."
if ! grep -q "Broker Standard Package" "docs/STANDARD_SCENARIO_PACKAGE.md" 2>/dev/null; then
  echo "  FAIL: STANDARD_SCENARIO_PACKAGE.md missing package name"
  exit 1
fi
echo "  OK"

echo "[3] Core trial scenarios (SIM1–SIM5) in config..."
if [ ! -f "configs/simulation_assistant_scenarios.json" ]; then
  echo "  FAIL: simulation_assistant_scenarios.json not found"
  exit 1
fi
for id in SIM1 SIM2 SIM3 SIM5 SIM6; do
  if ! grep -q "\"id\": \"$id\"" "configs/simulation_assistant_scenarios.json"; then
    echo "  FAIL: $id not found in simulation_assistant_scenarios.json"
    exit 1
  fi
done
echo "  OK (SIM1, SIM2, SIM3, SIM5, SIM6)"

echo "[4] Guardrail (scenario pack, multi-turn, simulation assistant)..."
if ! bash "$SCRIPT_DIR/guardrail_inbox_triage.sh" 2>/dev/null; then
  echo "  FAIL: Guardrail did not pass"
  exit 1
fi
echo "  OK"

echo "[5] UI build..."
if ! (cd ui && npm run build >/dev/null 2>&1); then
  echo "  FAIL: UI build failed"
  exit 1
fi
echo "  OK"

echo ""
echo "=== Trial Readiness: PASS ==="
echo ""
echo "Next: Read docs/trial/FOUNDER_TRIAL_NOTES.md and docs/trial/BROKER_TRIAL_WORKFLOW_SPEC.md"
echo "      Run: bash scripts/run_demo_local.sh"
echo "      Open: http://localhost:5173/workbench/unified-intake"
echo ""
