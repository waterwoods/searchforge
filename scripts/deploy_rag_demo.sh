#!/usr/bin/env bash
# scripts/deploy_rag_demo.sh — DEPRECATED wrapper (kept for old docs/scripts)
#
# Use instead:
#   bash scripts/deploy_paid_pilot.sh       # paid broker pilot
#   bash scripts/deploy_demo_cloud_smoke.sh # demo cloud smoke
#
# Implementation: scripts/deploy_cloud_run_core.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "⚠️  DEPRECATED: deploy_rag_demo.sh is renamed to deploy_cloud_run_core.sh" >&2
echo "   For paid pilot use:  bash scripts/deploy_paid_pilot.sh" >&2
echo "   For demo smoke use:  bash scripts/deploy_demo_cloud_smoke.sh" >&2
echo "   See: docs/CURRENT_PRODUCT_SHAPE.md" >&2
echo "" >&2

exec bash "$SCRIPT_DIR/deploy_cloud_run_core.sh" "$@"
