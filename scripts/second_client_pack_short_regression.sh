#!/usr/bin/env bash
# Second-client onboarding — short regression pack (bounded, deterministic-first).
#
# Answers: pack JSON + config merge OK? Add-Car field contract + copy isolation for this client?
# Optional: local JSON case store round-trip; formal-submit truth notes (pytest slice).
#
# Usage:
#   bash scripts/second_client_pack_short_regression.sh [client_id]
#   CLIENT_ID defaults to socal_precision when arg omitted.
#
# Does NOT replace scripts/guardrail_inbox_triage.sh (full gate before release).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

CLIENT_ID="${1:-socal_precision}"
export CLIENT_ID

echo "=== Second-client short regression pack (CLIENT_ID=${CLIENT_ID}) ==="

echo "[1] Client pack minimal validation (JSON + handoff/templates + Add-Car contract probe)..."
PYTHONPATH=. python3 scripts/validate_client_pack_minimal.py "${CLIENT_ID}"

echo "[2] Cross-client A/B scenarios for this client only (LLM off)..."
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py --client "${CLIENT_ID}"

echo "[3] Add-Car Stage 1 field contract tests (pytest, client-agnostic engine)..."
PYTHONPATH=. python3 -m pytest -q tests/test_add_car_field_contract.py

echo "[4] Formal-submit truth notes (intent layer, no LLM)..."
PYTHONPATH=. python3 -m pytest -q \
  tests/test_add_car_intent.py::test_truth_notes_pre_submit_office_receipt \
  tests/test_add_car_intent.py::test_post_submit_office_receipt_no_false_claim_note

echo "[5] Local JSON case persistence round-trip (optional engine check)..."
PYTHONPATH=. python3 scripts/verify_inbox_case_persistence.py

echo ""
echo "Second-client short regression pack: PASS (${CLIENT_ID})"
