#!/usr/bin/env bash
# P26H-UI — Mini Program Golden UI Journey (click / render / complete).
# Uses the repo Mini Program Page() test harness (not a product feature).
#
# Usage:
#   bash scripts/run_golden_customer_ui_flow.sh --local
#   bash scripts/run_golden_customer_ui_flow.sh --qa
#   bash scripts/run_golden_customer_ui_flow.sh --local --dry-run
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE=""
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --local) MODE="local" ;;
    --qa) MODE="qa" ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      echo "Usage: bash scripts/run_golden_customer_ui_flow.sh --local|--qa [--dry-run]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 64
      ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Usage: bash scripts/run_golden_customer_ui_flow.sh --local|--qa [--dry-run]" >&2
  exit 64
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "PASS"
  echo "Dry run: UI journey command wiring only."
  exit 0
fi

if [[ "$MODE" == "qa" ]]; then
  echo "== P26H-UI Golden Customer UI Flow (QA) =="
  PYTHONPATH=. python3 scripts/golden_customer_ui_flow_qa.py
  exit $?
fi

echo "== P26H-UI Golden Customer UI Flow (local) =="
cd "$ROOT/miniapp"
node --import tsx --test tests/goldenUiJourney.test.ts
echo ""
echo "PASS"
echo "Golden UI Journey local gate complete."
echo "READY FOR FOUNDER QA requires: unified release gate --qa after deploy."
