#!/usr/bin/env bash
# Deployment QA Gate v2 — fail-closed deploy/config safety before Founder QA.
#
# NOT a product feature. Catches: wrong revision/traffic, CORS, broken Office Queue,
# Smart Claim Start (customer start-claim) not reachable on the serving revision.
#
# Usage (Cloud QA defaults — Founder QA bookmark):
#   bash scripts/run_deployment_qa_gate.sh
#
# Overrides:
#   CLOUD_RUN_URL=https://fiqa-api-qa-….run.app \
#   FRONTEND_ORIGIN=https://ui-….vercel.app \
#   SERVICE_NAME=fiqa-api-qa REGION=us-west1 PROJECT_ID=… \
#   bash scripts/run_deployment_qa_gate.sh
#
# Docs: docs/runbooks/DEPLOYMENT_QA_GATE.md
#
# Reuses patterns from unified_intake_release_gate.sh (CORS) and deploy_cloud_run_core.sh
# (revision/traffic). Does not replace claim release gate or product guardrails.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Cloud QA Founder defaults (SSOT: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md)
SERVICE_NAME="${SERVICE_NAME:-fiqa-api-qa}"
REGION="${REGION:-us-west1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo optimal-disk-472305-e2)}"
CLOUD_RUN_URL="${CLOUD_RUN_URL:-https://fiqa-api-qa-g7zatxrycq-uw.a.run.app}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-https://ui-waterwoods-andys-projects-1f411b73.vercel.app}"

CLOUD_RUN_URL="${CLOUD_RUN_URL%/}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN%/}"

# Optional intake key for Office Queue (never printed). Prefer env; else .env.cloudrun.qa.
if [ -z "${UNIFIED_INTAKE_INTAKE_API_KEY:-}" ] && [ -f "$REPO_ROOT/.env.cloudrun.qa" ]; then
  # Only pull the key line — do not source entire file (may override PROJECT_ID etc.).
  _KEY_LINE=$(grep -E '^[[:space:]]*UNIFIED_INTAKE_INTAKE_API_KEY=' "$REPO_ROOT/.env.cloudrun.qa" | tail -1 || true)
  if [ -n "$_KEY_LINE" ]; then
    _KEY_VAL="${_KEY_LINE#*=}"
    _KEY_VAL="${_KEY_VAL%\"}"
    _KEY_VAL="${_KEY_VAL#\"}"
    _KEY_VAL="${_KEY_VAL%\'}"
    _KEY_VAL="${_KEY_VAL#\'}"
    export UNIFIED_INTAKE_INTAKE_API_KEY="$_KEY_VAL"
  fi
  unset _KEY_LINE _KEY_VAL
fi

AUTH_HDR=()
if [ -n "${UNIFIED_INTAKE_INTAKE_API_KEY:-}" ]; then
  AUTH_HDR=(-H "X-Unified-Intake-Api-Key: ${UNIFIED_INTAKE_INTAKE_API_KEY}")
fi

fail() {
  local check="$1"
  local reason="$2"
  local fix="$3"
  echo ""
  echo "=========================================="
  echo "FAILED"
  echo "=========================================="
  echo "Check:      $check"
  echo "Reason:     $reason"
  echo "How to Fix: $fix"
  echo "=========================================="
  exit 1
}

echo "=========================================="
echo "Deployment QA Gate v2"
echo "=========================================="
echo "Service:  $SERVICE_NAME ($REGION / $PROJECT_ID)"
echo "API:      $CLOUD_RUN_URL"
echo "Origin:   $FRONTEND_ORIGIN"
echo ""

# ---------------------------------------------------------------------------
# 1) Cloud Run is serving LATEST Ready revision (100% traffic)
# ---------------------------------------------------------------------------
echo "1) Cloud Run serving LATEST revision ..."
if ! command -v gcloud >/dev/null 2>&1; then
  fail "1. Latest revision" \
    "gcloud CLI not found" \
    "Install Google Cloud SDK and authenticate: gcloud auth login && gcloud config set project $PROJECT_ID"
fi

if ! gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  fail "1. Latest revision" \
    "Cannot describe Cloud Run service '$SERVICE_NAME' in $REGION (project=$PROJECT_ID)" \
    "Confirm SERVICE_NAME/REGION/PROJECT_ID and gcloud auth. Cloud QA service must be fiqa-api-qa."
fi

LATEST_READY=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" \
  --format='value(status.latestReadyRevisionName)' 2>/dev/null || true)
LATEST_LISTED=$(gcloud run revisions list \
  --service "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" \
  --limit 1 --format='value(metadata.name)' 2>/dev/null || true)
# Prefer service status.latestReadyRevisionName; fall back to newest listed revision.
LATEST_REV="${LATEST_READY:-$LATEST_LISTED}"

TRAFFIC_JSON=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" \
  --format=json 2>/dev/null || echo '{}')

read -r ACTIVE_REV ACTIVE_PCT <<< "$(python3 -c "
import json, sys
d = json.loads(sys.argv[1] or '{}')
traffic = d.get('status', {}).get('traffic') or []
if not traffic:
    print('', '0')
    raise SystemExit(0)
# Prefer the revision with highest percent; sum if split.
best = max(traffic, key=lambda t: int(t.get('percent') or 0))
print(str(best.get('revisionName') or ''), str(int(best.get('percent') or 0)))
" "$TRAFFIC_JSON")"

if [ -z "$LATEST_REV" ]; then
  fail "1. Latest revision" \
    "Could not resolve latest Ready revision for $SERVICE_NAME" \
    "Run: gcloud run revisions list --service $SERVICE_NAME --region $REGION --project $PROJECT_ID"
fi
if [ -z "$ACTIVE_REV" ]; then
  fail "1. Latest revision" \
    "No traffic target revision found on $SERVICE_NAME" \
    "gcloud run services update-traffic $SERVICE_NAME --region $REGION --project $PROJECT_ID --to-latest"
fi
if [ "$ACTIVE_REV" != "$LATEST_REV" ]; then
  fail "1. Latest revision" \
    "Traffic is on '$ACTIVE_REV' but latest Ready revision is '$LATEST_REV'" \
    "gcloud run services update-traffic $SERVICE_NAME --region $REGION --project $PROJECT_ID --to-latest"
fi
if [ "${ACTIVE_PCT:-0}" != "100" ]; then
  fail "1. Latest revision" \
    "Latest revision '$LATEST_REV' is active but only ${ACTIVE_PCT}% traffic (need 100%)" \
    "gcloud run services update-traffic $SERVICE_NAME --region $REGION --project $PROJECT_ID --to-revisions ${LATEST_REV}=100"
fi
echo "   OK — serving $ACTIVE_REV (100%)"
echo ""

# ---------------------------------------------------------------------------
# 2) Current Vercel origin allowed by CORS
# ---------------------------------------------------------------------------
echo "2) Vercel origin allowed by CORS ..."
if ! curl -sf --max-time 15 "${CLOUD_RUN_URL}/health/live" >/dev/null; then
  fail "2. CORS (precondition: API live)" \
    "GET ${CLOUD_RUN_URL}/health/live failed" \
    "Confirm CLOUD_RUN_URL. Do not use bare /healthz on Cloud Run edge. Redeploy Cloud QA if service is down."
fi

HDRS=$(mktemp)
trap 'rm -f "$HDRS"' EXIT
CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 -D "$HDRS" -X OPTIONS \
  "${CLOUD_RUN_URL}/api/inbox/cases?limit=1" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -H "Access-Control-Request-Method: GET" || echo "000")
ACA=$(tr -d '\r' <"$HDRS" | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2; exit}')

if [ "$CODE" != "200" ]; then
  fail "2. CORS" \
    "OPTIONS /api/inbox/cases returned HTTP $CODE for Origin=$FRONTEND_ORIGIN" \
    "Add $FRONTEND_ORIGIN to ALLOWED_ORIGINS on $SERVICE_NAME (.env.cloudrun.qa), redeploy via bash scripts/deploy_cloud_qa.sh, then --to-latest."
fi
if [ "$ACA" != "$FRONTEND_ORIGIN" ]; then
  fail "2. CORS" \
    "OPTIONS 200 but Access-Control-Allow-Origin='$ACA' (expected '$FRONTEND_ORIGIN')" \
    "Update ALLOWED_ORIGINS on $SERVICE_NAME to include the exact Vercel origin (no trailing slash). If env looks correct, traffic may still be on an old revision — run check 1 fix (--to-latest)."
fi
echo "   OK — ACA=$ACA"
echo ""

# ---------------------------------------------------------------------------
# 3) Office Queue loads successfully
# ---------------------------------------------------------------------------
echo "3) Office Queue loads ..."
QUEUE_BODY=$(mktemp)
QUEUE_HDR=$(mktemp)
trap 'rm -f "$HDRS" "$QUEUE_BODY" "$QUEUE_HDR"' EXIT
QUEUE_CODE=$(curl -sS -o "$QUEUE_BODY" -w '%{http_code}' --max-time 30 -D "$QUEUE_HDR" \
  "${CLOUD_RUN_URL}/api/inbox/cases?limit=5" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -H "Accept: application/json" \
  "${AUTH_HDR[@]}" || echo "000")
QUEUE_ACA=$(tr -d '\r' <"$QUEUE_HDR" | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2; exit}')

if [ "$QUEUE_CODE" = "401" ] || [ "$QUEUE_CODE" = "403" ]; then
  fail "3. Office Queue" \
    "GET /api/inbox/cases returned HTTP $QUEUE_CODE (auth)" \
    "Export UNIFIED_INTAKE_INTAKE_API_KEY (or set it in .env.cloudrun.qa) matching the key on $SERVICE_NAME. Do not print the key. Vercel Preview must bake the same key the API expects."
fi
if [ "$QUEUE_CODE" != "200" ]; then
  fail "3. Office Queue" \
    "GET /api/inbox/cases returned HTTP $QUEUE_CODE" \
    "Check Cloud Run logs and UNIFIED_INTAKE_* / DB secrets on $SERVICE_NAME. Confirm serving latest revision."
fi
if [ "$QUEUE_ACA" != "$FRONTEND_ORIGIN" ]; then
  fail "3. Office Queue" \
    "Queue HTTP 200 but ACA='$QUEUE_ACA' (browser would still block). Expected '$FRONTEND_ORIGIN'" \
    "Same as CORS fix: ALLOWED_ORIGINS must include exact origin; promote latest revision to 100%."
fi

python3 - "$QUEUE_BODY" <<'PY' || fail "3. Office Queue" \
  "Response was not a usable Office Queue payload" \
  "Inspect ${CLOUD_RUN_URL}/api/inbox/cases — expect JSON with cases list (or total_count). Fix backend/env on the serving revision."
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    data = json.load(f)
if isinstance(data, list):
    sys.exit(0)
if isinstance(data, dict) and ("cases" in data or "total_count" in data or "total" in data):
    sys.exit(0)
sys.exit(1)
PY
echo "   OK — /api/inbox/cases HTTP 200 (browser-origin ACA matched)"
echo ""

# ---------------------------------------------------------------------------
# 4) Smart Claim Start opens successfully (live Start Claim surface on serving rev)
# ---------------------------------------------------------------------------
echo "4) Smart Claim Start opens ..."
# Shell: Founder Workbench page must load (empty/broken Vercel deploy = FAIL).
UI_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 25 \
  "${FRONTEND_ORIGIN}/workbench/document-intake" || echo "000")
if [ "$UI_CODE" != "200" ]; then
  fail "4. Smart Claim Start (Workbench shell)" \
    "GET ${FRONTEND_ORIGIN}/workbench/document-intake returned HTTP $UI_CODE" \
    "Redeploy QA Vercel Preview (cd ui && vercel --yes) targeting Cloud QA API. Confirm bookmark host matches FRONTEND_ORIGIN."
fi

# CORS on the Start Claim path (same Origin the browser/MP client stack must allow).
SC_OPT_HDR=$(mktemp)
trap 'rm -f "$HDRS" "$QUEUE_BODY" "$QUEUE_HDR" "$SC_OPT_HDR"' EXIT
SC_OPT_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 -D "$SC_OPT_HDR" -X OPTIONS \
  "${CLOUD_RUN_URL}/api/h5/customer/start-claim" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" || echo "000")
SC_OPT_ACA=$(tr -d '\r' <"$SC_OPT_HDR" | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2; exit}')
if [ "$SC_OPT_CODE" != "200" ]; then
  fail "4. Smart Claim Start" \
    "OPTIONS /api/h5/customer/start-claim returned HTTP $SC_OPT_CODE for Origin=$FRONTEND_ORIGIN" \
    "Add $FRONTEND_ORIGIN to ALLOWED_ORIGINS on $SERVICE_NAME, redeploy, --to-latest."
fi
if [ "$SC_OPT_ACA" != "$FRONTEND_ORIGIN" ]; then
  fail "4. Smart Claim Start" \
    "Start Claim OPTIONS ACA='$SC_OPT_ACA' (expected '$FRONTEND_ORIGIN')" \
    "Fix ALLOWED_ORIGINS / traffic --to-latest (same as check 2)."
fi

# Start Claim command route must exist on serving revision (validation error ≠ missing route).
# Empty body must NOT create a case — expect 4xx validation / identity rejection.
SC_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 \
  -X POST "${CLOUD_RUN_URL}/api/h5/customer/start-claim" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -H "Content-Type: application/json" \
  -d '{}' || echo "000")
if [ "$SC_CODE" = "404" ] || [ "$SC_CODE" = "000" ]; then
  fail "4. Smart Claim Start" \
    "POST /api/h5/customer/start-claim returned HTTP $SC_CODE — Start Claim route missing or API unreachable" \
    "Deploy latest backend to $SERVICE_NAME (bash scripts/deploy_cloud_qa.sh) and promote traffic to latest Ready revision."
fi
case "$SC_CODE" in
  2*|4*) ;;
  *)
    fail "4. Smart Claim Start" \
      "POST /api/h5/customer/start-claim returned unexpected HTTP $SC_CODE" \
      "Inspect Cloud Run logs. Fix env/DB on $SERVICE_NAME; do not hand Founder QA a broken Start Claim path."
    ;;
esac

echo "   OK — Workbench shell 200; start-claim CORS OK; route live (HTTP $SC_CODE)"
echo ""

echo "=========================================="
echo "READY FOR FOUNDER QA"
echo "=========================================="
echo "Serving:  $ACTIVE_REV @ 100%"
echo "API:      $CLOUD_RUN_URL"
echo "Origin:   $FRONTEND_ORIGIN"
echo "Workbench:${FRONTEND_ORIGIN}/workbench/document-intake"
echo ""
echo "Next: Founder QA only — docs/FOUNDER_QA_PLAYBOOK.md"
echo "      (Do not skip Mini Program build:gate / Golden path when doing product QA.)"
exit 0
