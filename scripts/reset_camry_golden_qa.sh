#!/usr/bin/env bash
# P24G — One-command Camry Golden QA Reset
#
# Usage:
#   bash scripts/reset_camry_golden_qa.sh --qa --reseed     # QA Cloud SQL (Founder default)
#   bash scripts/reset_camry_golden_qa.sh --local --reseed  # Local JSON store
#   bash scripts/reset_camry_golden_qa.sh --qa --dry-run
#   bash scripts/reset_camry_golden_qa.sh --qa --no-reseed  # remove only
#
# After success: prints Case ID, Token, Preview + QR instructions.
# SSOT: docs/product/p24f_golden_production_qa_flow.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

TARGET="qa"
RESEED=1
DRY_RUN=0
SKIP_VERIFY=0

for arg in "$@"; do
  case "$arg" in
    --qa|--cloud) TARGET="qa" ;;
    --local) TARGET="local" ;;
    --reseed) RESEED=1 ;;
    --no-reseed) RESEED=0 ;;
    --dry-run) DRY_RUN=1 ;;
    --skip-verify) SKIP_VERIFY=1 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

ARGS=(reset --target "$TARGET")
if [[ "$RESEED" == "1" ]]; then
  ARGS+=(--reseed)
else
  ARGS+=(--no-reseed)
fi
if [[ "$DRY_RUN" == "1" ]]; then
  ARGS+=(--dry-run)
fi
if [[ "$SKIP_VERIFY" == "1" ]]; then
  ARGS+=(--skip-verify)
fi

echo "=========================================="
echo "Camry Golden QA Reset"
echo "  target=${TARGET} reseed=${RESEED} dry_run=${DRY_RUN}"
echo "=========================================="

PYTHONPATH=. python3 scripts/camry_golden_qa.py "${ARGS[@]}"
