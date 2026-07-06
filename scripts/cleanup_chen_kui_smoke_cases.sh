#!/usr/bin/env bash
# Hide historical Chen Kui smoke/test cases from Workbench demo queue.
#
# Usage:
#   bash scripts/cleanup_chen_kui_smoke_cases.sh --qa --dry-run
#   bash scripts/cleanup_chen_kui_smoke_cases.sh --qa --apply
#
# Never truncates tables. Only archives explicit smoke case IDs / smoke external_userid prefixes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

TARGET="qa"
APPLY=0
for arg in "$@"; do
  case "$arg" in
    --qa) TARGET="qa" ;;
    --local) TARGET="local" ;;
    --apply) APPLY=1 ;;
    --dry-run) APPLY=0 ;;
  esac
done

ARGS=(--target "$TARGET")
if [[ "$APPLY" == "1" ]]; then
  ARGS+=(--apply)
fi

echo "=========================================="
echo "Chen Kui Smoke Cleanup (target=${TARGET})"
echo "=========================================="
PYTHONPATH=. python3 scripts/cleanup_chen_kui_smoke_cases.py "${ARGS[@]}"
