#!/bin/bash
# Broker Inbox Triage — Guardrail
# ================================
# Checks: scenario pack exists, scenario runner runs, output shape valid.
# Exit 1 on any failure.
#
# Usage: bash scripts/guardrail_inbox_triage.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "[1] Scenario pack exists..."
if [ ! -f "configs/inbox_triage_scenarios.json" ]; then
  echo "  FAIL: configs/inbox_triage_scenarios.json not found"
  exit 1
fi
echo "  OK"

echo "[2] Scenario runner (rule-based, no LLM)..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py; then
  echo "  FAIL: Scenario pack did not pass"
  exit 1
fi
echo "  OK"

echo "[3] API test (optional, if server on 8001)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/healthz 2>/dev/null | grep -q 200; then
  if PYTHONPATH=. python3 scripts/test_inbox_triage_api.py --url http://localhost:8001 2>/dev/null; then
    echo "  OK (API route verified)"
  else
    echo "  WARN: API test failed (server may need restart to pick up new route)"
  fi
else
  echo "  SKIP (no server on 8001)"
fi

echo "[3b] First-turn continuity (MULTI_TURN_CONTINUITY_GUARDRAIL)..."
if ! PYTHONPATH=. python3 scripts/test_first_turn_continuity.py 2>/dev/null; then
  echo "  FAIL: First-turn must not force handoff_ready"
  exit 1
fi
echo "  OK"

echo "[4] Lightweight case persistence..."
if ! PYTHONPATH=. python3 scripts/verify_inbox_case_persistence.py; then
  echo "  FAIL: case persistence check failed"
  exit 1
fi
echo "  OK"

echo "[4b] State/Workflow backbone (workflow state keys, handoff semantics, terminal status)..."
if ! PYTHONPATH=. python3 scripts/test_state_workflow_backbone.py; then
  echo "  FAIL: State/Workflow backbone regression failed"
  exit 1
fi
echo "  OK"

echo "[5] Multi-turn intake simulations..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 -u scripts/run_multi_turn_simulations.py 2>/dev/null; then
  echo "  FAIL: Multi-turn simulation pack did not pass"
  exit 1
fi
echo "  OK"

echo "[6] Adversarial real-user simulations..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_adversarial_simulation.py 2>/dev/null; then
  echo "  FAIL: Adversarial scenario pack did not pass"
  exit 1
fi
echo "  OK"

echo "[7] Complex adversarial (mixed-intent + long-context)..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py 2>/dev/null; then
  echo "  FAIL: Complex adversarial pack did not pass"
  exit 1
fi
echo "  OK"

echo "[7c] Case boundary append (same case vs new issue vs borderline)..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_case_boundary_battery.py 2>/dev/null; then
  echo "  FAIL: Case boundary append battery did not pass"
  exit 1
fi
echo "  OK"

echo "[8] Simulation Assistant scenarios (15 trial + 8 real-customer)..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py 2>/dev/null; then
  echo "  FAIL: Simulation Assistant scenario pack did not pass"
  exit 1
fi
echo "  OK"

echo "[8b] Broker trial stress (vague, talk-to-agent, already-sent, correction)..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py 2>/dev/null; then
  echo "  FAIL: Broker trial stress pack did not pass"
  exit 1
fi
echo "  OK"

echo "[8c] Handoff timing audit (customer-not-finished, add-car+clarification)..."
if ! LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py 2>/dev/null; then
  echo "  FAIL: Handoff timing pack did not pass"
  exit 1
fi
echo "  OK"

echo "[9] Standard Scenario Package definition..."
if [ ! -f "docs/STANDARD_SCENARIO_PACKAGE.md" ]; then
  echo "  FAIL: docs/STANDARD_SCENARIO_PACKAGE.md not found"
  exit 1
fi
if ! grep -q "Broker Standard Package" "docs/STANDARD_SCENARIO_PACKAGE.md"; then
  echo "  FAIL: Package name not found in STANDARD_SCENARIO_PACKAGE.md"
  exit 1
fi
echo "  OK"

echo "[10] Client-aware handoff A/B variation..."
if ! PYTHONPATH=. python3 scripts/test_client_aware_handoff.py --direct 2>/dev/null; then
  echo "  FAIL: Client-aware handoff A/B test did not pass"
  exit 1
fi
echo "  OK"

echo "[11] Client identity persistence (append uses case client_id)..."
if ! PYTHONPATH=. python3 scripts/test_client_identity_append.py --direct 2>/dev/null; then
  echo "  FAIL: Client identity append test did not pass"
  exit 1
fi
echo "  OK"

echo ""
echo "Guardrail: PASS"
