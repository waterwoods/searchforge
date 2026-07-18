#!/usr/bin/env bash
# Unified claim release gate — local pre-deploy / QA post-deploy.
# Output verdict only on the last line: READY FOR QA DEPLOY | READY FOR FOUNDER QA | STOP
#
# Usage:
#   bash scripts/run_claim_release_gate.sh --local
#   bash scripts/run_claim_release_gate.sh --qa
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE=""
for arg in "$@"; do
  case "$arg" in
    --local) MODE="local" ;;
    --qa) MODE="qa" ;;
    -h|--help)
      echo "Usage: bash scripts/run_claim_release_gate.sh --local|--qa"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 64
      ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Usage: bash scripts/run_claim_release_gate.sh --local|--qa" >&2
  exit 64
fi

fail_stop() {
  echo "STOP"
  exit 1
}

if [[ "$MODE" == "local" ]]; then
  echo "== Claim release gate (local) =="
  echo "-- focused P26H / work-surface / fixture tests --"
  PYTHONPATH=. python3 -m pytest \
    tests/test_p26h_golden_customer_flow.py \
    tests/test_p26h_qa_fixture_runner.py \
    -q || fail_stop

  echo "-- miniapp build:gate --"
  (cd miniapp && npm run build:gate) || fail_stop

  echo "-- local backend Golden Flow --"
  bash scripts/run_golden_customer_flow.sh --local || fail_stop

  echo "-- local UI Golden Journey --"
  bash scripts/run_golden_customer_ui_flow.sh --local || fail_stop

  echo "READY FOR QA DEPLOY"
  exit 0
fi

echo "== Claim release gate (QA) =="
echo "-- QA health / fixture preflight --"
TRANSPORT=""
PREFLIGHT_LOG=$(mktemp)
if ! PYTHONPATH=. python3 - <<PY >"$PREFLIGHT_LOG" 2>&1
from scripts.p26h_fixture_client import FixtureClientError, open_fixture_client
try:
    client, info = open_fixture_client()
except FixtureClientError as exc:
    print(f"PREFLIGHT FAIL: {exc}")
    print(exc.detail)
    raise SystemExit(2)
status = client.status()
print(f"transport={info.transport} enabled={status.get('enabled')} production_like={status.get('production_like')}")
if not status.get("enabled"):
    print("Fixture runner not enabled on target.")
    raise SystemExit(2)
open("$PREFLIGHT_LOG.transport", "w", encoding="utf-8").write(info.transport)
print("PREFLIGHT PASS")
PY
then
  cat "$PREFLIGHT_LOG" || true
  rm -f "$PREFLIGHT_LOG" "$PREFLIGHT_LOG.transport"
  echo "STOP"
  echo "QA preflight failed. Set P26H_QA_BASE_URL + UNIFIED_INTAKE_SUPPORT_API_KEY"
  echo "and ensure QA has ENABLE_P26H_FIXTURE_RUNNER=1 UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1"
  echo "Local QA-path proof (not Founder-ready): P26H_QA_TRANSPORT=inprocess + enable flags."
  exit 2
fi
cat "$PREFLIGHT_LOG"
TRANSPORT=$(cat "$PREFLIGHT_LOG.transport" 2>/dev/null || echo "")
rm -f "$PREFLIGHT_LOG" "$PREFLIGHT_LOG.transport"

echo "-- deployed backend Golden Flow --"
bash scripts/run_golden_customer_flow.sh --qa || fail_stop

echo "-- deployed UI / bootstrap Golden Journey --"
bash scripts/run_golden_customer_ui_flow.sh --qa || fail_stop

if [[ "$TRANSPORT" != "http" ]]; then
  echo "STOP"
  echo "In-process QA path passed, but READY FOR FOUNDER QA requires deployed HTTP:"
  echo "  P26H_QA_BASE_URL=https://<qa-host> UNIFIED_INTAKE_SUPPORT_API_KEY=<key>"
  echo "  QA runtime: ENABLE_P26H_FIXTURE_RUNNER=1 UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1"
  exit 2
fi

echo "READY FOR FOUNDER QA"
exit 0
