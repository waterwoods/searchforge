#!/usr/bin/env bash
# Read-only check: live Cloud Run fiqa-api matches proven-good runtime + strict DB-primary flags.
# Does not print secrets (only whitelisted UNIFIED_INTAKE_* keys, not DATABASE_URL / API keys).
#
# Usage:
#   bash scripts/guardrail_cloudrun_runtime.sh
#   SERVICE_NAME=my-api REGION=us-central1 bash scripts/guardrail_cloudrun_runtime.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SERVICE_NAME="${SERVICE_NAME:-fiqa-api}"
REGION="${REGION:-us-west1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"

EXPECTED_MEM="${EXPECTED_CLOUD_RUN_MEMORY:-1Gi}"
EXPECTED_CC="${EXPECTED_CLOUD_RUN_CONCURRENCY:-30}"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project (set PROJECT_ID or gcloud config set project)"
    exit 1
fi

if ! command -v gcloud &>/dev/null; then
    echo "❌ gcloud not found"
    exit 1
fi

if ! gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" &>/dev/null; then
    echo "❌ Service not found or not accessible: $SERVICE_NAME ($REGION) project=$PROJECT_ID"
    exit 1
fi

ACTUAL_MEM=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" \
    --format='value(spec.template.spec.containers[0].resources.limits.memory)')
ACTUAL_CC=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" \
    --format='value(spec.template.spec.containerConcurrency)')

FAIL=0
if [ "$ACTUAL_MEM" != "$EXPECTED_MEM" ]; then
    echo "❌ Memory drift: actual=$ACTUAL_MEM expected=$EXPECTED_MEM"
    FAIL=1
else
    echo "✅ Memory: $ACTUAL_MEM"
fi

if [ "$ACTUAL_CC" != "$EXPECTED_CC" ]; then
    echo "❌ Concurrency drift: actual=$ACTUAL_CC expected=$EXPECTED_CC"
    FAIL=1
else
    echo "✅ Concurrency: $ACTUAL_CC"
fi

# Whitelist only non-secret intake flags (values are 0/1)
JSON=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format=json)
readarray -t _RUNMETA < <(echo "$JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('status', {}).get('url', '') or '')
ann = (d.get('spec', {}).get('template', {}).get('metadata', {}).get('annotations') or {})
ms = ann.get('autoscaling.knative.dev/minScale')
if ms is None:
    sc = (d.get('spec', {}).get('template', {}).get('scaling') or {})
    v = sc.get('minInstanceCount')
    ms = str(v) if v is not None else ''
print(ms if ms else '0')
")
STATUS_URL="${_RUNMETA[0]:-}"
MIN_INST="${_RUNMETA[1]:-0}"
if [ -n "$STATUS_URL" ]; then
    echo "   status.url=$STATUS_URL  (align Vercel VITE_API_BASE_URL with this or an equivalent *.run.app alias)"
else
    echo "   status.url=(missing from describe — unusual)"
fi
echo "   minInstances=$MIN_INST  (0 = scale-to-zero; cold-start risk on first request)"

AO=$(echo "$JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
env = d.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [{}])[0].get('env') or []
for e in env:
    if e.get('name') == 'ALLOWED_ORIGINS':
        print(e.get('value', '') or '')
        break
")
if [ -n "$AO" ]; then
    echo "   ALLOWED_ORIGINS=$AO"
else
    echo "   ALLOWED_ORIGINS=(unset — app uses permissive demo CORS fallback)"
fi

for KEY in UNIFIED_INTAKE_DB_PRIMARY_READS UNIFIED_INTAKE_DB_PRIMARY_WRITES UNIFIED_INTAKE_JSON_CASE_WRITES UNIFIED_INTAKE_JSON_READ_FALLBACK UNIFIED_INTAKE_PG_DUAL_WRITE; do
    VAL=$(echo "$JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
key = sys.argv[1]
env = d.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [{}])[0].get('env') or []
for e in env:
    if e.get('name') == key:
        print(e.get('value', ''))
        break
" "$KEY")
    if [ -n "$VAL" ]; then
        echo "   $KEY=$VAL"
    fi
done

echo ""
echo "Expected strict DB-primary pilot (when Neon/Postgres is wired):"
echo "  UNIFIED_INTAKE_DB_PRIMARY_READS=1 UNIFIED_INTAKE_DB_PRIMARY_WRITES=1"
echo "  UNIFIED_INTAKE_JSON_CASE_WRITES=0 UNIFIED_INTAKE_JSON_READ_FALLBACK=0"
echo "(If unset, service may be JSON-only — intentional for some demos.)"

if [ "$FAIL" -ne 0 ]; then
    echo ""
    echo "Fix: align scripts/deploy_rag_demo.sh defaults or set CLOUD_RUN_MEMORY / CLOUD_RUN_CONCURRENCY in .env.cloudrun, then redeploy."
    exit 1
fi

exit 0
