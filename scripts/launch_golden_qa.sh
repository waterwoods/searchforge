#!/usr/bin/env bash
# P25 — One-command Launch Golden QA (reset + Preview prep)
#
# Usage:
#   bash scripts/launch_golden_qa.sh --qa
#   bash scripts/launch_golden_qa.sh --local
#   bash scripts/launch_golden_qa.sh --status
#   bash scripts/launch_golden_qa.sh --clear-preview

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

ARGS=()
if [[ $# -eq 0 ]]; then
  ARGS=(--qa)
else
  ARGS=("$@")
fi

echo "=========================================="
echo "Launch Golden QA"
echo "=========================================="

PYTHONPATH=. python3 scripts/launch_golden_qa.py "${ARGS[@]}"
