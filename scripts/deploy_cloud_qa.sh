#!/usr/bin/env bash
# scripts/deploy_cloud_qa.sh — Cloud QA Cloud Run deploy entry (P36)
#
# Loads .env.cloudrun.qa only. Never touches Production fiqa-api / caseiq.
# QA Harness flags stay opt-in (set in .env.cloudrun.qa if needed; never default ON).
#
# Does NOT create infrastructure. Does NOT provision databases/secrets.
# Pre-deploy: isolation verifier + deploy safety check (fail-closed).
#
# Usage:
#   cp configs/cloud_qa.env.example .env.cloudrun.qa   # fill frozen QA names + secrets
#   PYTHONPATH=. python3 scripts/p36_verify_cloud_qa_isolation.py
#   bash scripts/deploy_cloud_qa.sh
#
# Safety-only (no gcloud):
#   DEPLOY_SAFETY_CHECK_ONLY=1 bash scripts/deploy_cloud_qa.sh
#
# SSOT: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export DEPLOY_ENTRY=cloud_qa
export CLOUD_RUN_ENV_FILE="${CLOUD_RUN_ENV_FILE:-$REPO_ROOT/.env.cloudrun.qa}"

# Paid-pilot-like product posture for Cloud QA — harness flags NOT set here.
export ENV="${ENV:-qa}"
export PILOT_DEPLOY_STRICT=1
export UNIFIED_INTAKE_PRODUCT_ONLY=1
export UNIFIED_INTAKE_DB_PRIMARY_READS=1
export UNIFIED_INTAKE_DB_PRIMARY_WRITES=1
export UNIFIED_INTAKE_JSON_CASE_WRITES=0
export UNIFIED_INTAKE_JSON_READ_FALLBACK=0
export UNIFIED_INTAKE_PG_DUAL_WRITE=0
export UNIFIED_INTAKE_INTAKE_CORE_READINESS=1
unset DEMO_MODE

# Explicitly do not enable QA Harness from this wrapper (opt-in via env file only).
# Leaving them unset preserves file values if operator set them in .env.cloudrun.qa.

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Cloud QA deploy — service fiqa-api-qa / env .env.cloudrun.qa"
echo "  Isolation verifier + deploy safety check required (fail-closed)"
echo "  QA Harness flags: opt-in only (never default ON)"
echo "SSOT: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f "$CLOUD_RUN_ENV_FILE" ]; then
  echo "❌ Missing Cloud QA env file: $CLOUD_RUN_ENV_FILE"
  echo "   cp configs/cloud_qa.env.example .env.cloudrun.qa"
  exit 1
fi

# Fail-closed isolation gate before shared deploy impl (skip only for explicit escape hatch).
case "${SKIP_P36_ISOLATION_VERIFIER:-0}" in
  1|true|TRUE|yes|YES|on|ON)
    echo "⚠️  SKIP_P36_ISOLATION_VERIFIER set — isolation verifier skipped (not for real deploy)"
    ;;
  *)
    echo "🔒 P36 isolation verifier (Cloud QA must not share Production mutable data)..."
    if ! PYTHONPATH=. python3 "$SCRIPT_DIR/p36_verify_cloud_qa_isolation.py" \
      --qa-env-file "$CLOUD_RUN_ENV_FILE" \
      --prod-env-file "$REPO_ROOT/.env.cloudrun"; then
      echo "❌ Isolation verifier FAIL — refusing Cloud QA deploy"
      exit 1
    fi
    ;;
esac

exec bash "$SCRIPT_DIR/deploy_cloud_run_core.sh" "$@"
