#!/usr/bin/env bash
# P26H Golden Customer Flow Harness — test infrastructure only.
# Usage: bash scripts/run_golden_customer_flow.sh --local|--qa [--dry-run]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ $# -eq 0 ]]; then
  echo "Usage: bash scripts/run_golden_customer_flow.sh --local|--qa [--dry-run]" >&2
  exit 64
fi

PYTHONPATH=. python3 scripts/golden_customer_flow.py "$@"
