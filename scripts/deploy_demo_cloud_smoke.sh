#!/usr/bin/env bash
# scripts/deploy_demo_cloud_smoke.sh — Legacy demo / RAG smoke Cloud Run deploy
#
# Relaxed readiness (DEMO_MODE). NOT for paid broker pilots.
# For production broker pilots use: bash scripts/deploy_paid_pilot.sh
#
# Usage:
#   cp configs/demo.env.example .env.cloudrun
#   bash scripts/deploy_demo_cloud_smoke.sh
#
# See: docs/CURRENT_PRODUCT_SHAPE.md (Local / founder demo)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prevent accidental paid-pilot tuple on demo smoke path
unset PILOT_DEPLOY_STRICT
unset UNIFIED_INTAKE_PRODUCT_ONLY
unset UNIFIED_INTAKE_DB_PRIMARY_WRITES
export DEMO_MODE=true
export DEPLOY_ENTRY=demo_smoke

if [ "${ENV:-}" = "prod" ]; then
    echo "⚠️  Warning: ENV=prod with demo cloud smoke deploy — unset ENV or use deploy_paid_pilot.sh for brokers."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Demo cloud smoke deploy (DEMO_MODE=true — NOT a paid pilot)"
echo "For paid pilot: bash scripts/deploy_paid_pilot.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exec bash "$SCRIPT_DIR/deploy_cloud_run_core.sh" "$@"
