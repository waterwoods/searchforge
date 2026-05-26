#!/usr/bin/env bash
# scripts/deploy_paid_pilot.sh — Cloud Run deploy for paid broker pilot (ONE path)
#
# Forces paid-pilot posture before calling the shared deploy implementation.
# Never injects DEMO_MODE. Always validates .env.cloudrun.
#
# Usage:
#   cp configs/demo.env.example .env.cloudrun   # fill PILOT ONE PATH block
#   PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
#   bash scripts/deploy_paid_pilot.sh
#
# See: docs/CURRENT_PRODUCT_SHAPE.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export ENV=prod
export PILOT_DEPLOY_STRICT=1
export UNIFIED_INTAKE_PRODUCT_ONLY=1
export UNIFIED_INTAKE_DB_PRIMARY_READS=1
export UNIFIED_INTAKE_DB_PRIMARY_WRITES=1
export UNIFIED_INTAKE_JSON_CASE_WRITES=0
export UNIFIED_INTAKE_JSON_READ_FALLBACK=0
export UNIFIED_INTAKE_PG_DUAL_WRITE=0
unset DEMO_MODE
export DEPLOY_ENTRY=paid_pilot

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paid-pilot Cloud Run deploy (product_only + Postgres-primary, no DEMO_MODE)"
echo "Authority: docs/CURRENT_PRODUCT_SHAPE.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exec bash "$SCRIPT_DIR/deploy_rag_demo.sh" "$@"
