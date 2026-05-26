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

# Vite 7 requires Node 22 — see docs/runbooks/NODE_22_SETUP.md
if [ -z "${SKIP_NVM_NODE22_FOR_UI:-}" ]; then
  # shellcheck disable=SC1090
  source "$SCRIPT_DIR/with_node22_path.sh"
fi

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

echo "[3] Pilot client pack layout (chen_kui)..."
if ! PYTHONPATH=. python3 -c "
from services.fiqa_api.inbox_triage.pack_validation import validate_client_pack_layout
import sys
issues = validate_client_pack_layout('chen_kui')
for line in issues:
    print('  FAIL:', line)
sys.exit(1 if issues else 0)
" 2>&1; then
  echo "  FAIL: configs/clients/chen_kui missing required onboarding files"
  exit 1
fi
echo "  OK"

echo "[4] Core trial scenarios (SIM1–SIM5) in config..."
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

echo "[5] Guardrail (scenario pack, multi-turn, simulation assistant)..."
if ! bash "$SCRIPT_DIR/guardrail_inbox_triage.sh" 2>/dev/null; then
  echo "  FAIL: Guardrail did not pass"
  exit 1
fi
echo "  OK"

echo "[6] UI Node gate + build..."
if ! bash "$SCRIPT_DIR/check_ui_node_version.sh" --quiet 2>/dev/null; then
  echo "  FAIL: Node version (need 22.x — source scripts/with_node22_path.sh)"
  exit 1
fi
if ! (cd ui && npm run build >/dev/null 2>&1); then
  echo "  FAIL: UI build failed"
  exit 1
fi
echo "  OK"

echo "[7] Paid-pilot deploy entry + SSOT..."
for _pf in scripts/deploy_paid_pilot.sh docs/CURRENT_PRODUCT_SHAPE.md; do
  if [ ! -f "$_pf" ]; then
    echo "  FAIL: $_pf not found"
    exit 1
  fi
done
echo "  OK (deploy_paid_pilot.sh + CURRENT_PRODUCT_SHAPE.md)"

echo "[8] Pilot deploy env (when .env.cloudrun is production-like)..."
_PILOT_ENV_FILE="$REPO_DIR/.env.cloudrun"
if [ -f "$_PILOT_ENV_FILE" ]; then
  _PROD_LIKE=0
  if grep -Eq '^[[:space:]]*(ENV=prod|PILOT_DEPLOY_STRICT=1|UNIFIED_INTAKE_DB_PRIMARY_WRITES=1)' "$_PILOT_ENV_FILE" 2>/dev/null; then
    _PROD_LIKE=1
  fi
  if [ "$_PROD_LIKE" = "1" ]; then
    if ! PYTHONPATH=. python3 "$SCRIPT_DIR/validate_pilot_deploy_env.py" --env-file "$_PILOT_ENV_FILE" 2>&1; then
      echo "  FAIL: production-like .env.cloudrun does not meet minimum paid-pilot posture"
      echo "  Fix: configs/demo.env.example PILOT ONE PATH block — or unset prod flags for local-only cloudrun"
      exit 1
    fi
    echo "  OK (production-like .env.cloudrun validated)"
  else
    echo "  SKIP (.env.cloudrun present but not production-like — set PILOT_DEPLOY_STRICT=1 to require full tuple)"
  fi
else
  echo "  SKIP (no .env.cloudrun — local demo path)"
fi

echo "[9] Intake-core vs full-stack readiness (posture)..."
if ! bash "$SCRIPT_DIR/summarize_readiness_posture.sh" 2>&1 | head -20; then
  echo "  FAIL: readiness posture summary"
  exit 1
fi
if curl -sf --max-time 3 "http://127.0.0.1:8001/readyz" >/dev/null 2>&1; then
  bash "$SCRIPT_DIR/summarize_readiness_posture.sh" --probe "http://127.0.0.1:8001" 2>&1 | tail -8 || true
  echo "  OK (local API probed)"
else
  echo "  OK (env summary only — start run_demo_local.sh to probe /readyz)"
fi

echo ""
echo "=== Trial Readiness: PASS ==="
echo ""
echo "Next: Read docs/trial/FOUNDER_TRIAL_NOTES.md and docs/trial/BROKER_TRIAL_WORKFLOW_SPEC.md"
echo "      Run: bash scripts/run_demo_local.sh"
echo "      Open: http://localhost:5173/workbench/unified-intake"
echo ""
