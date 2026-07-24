#!/usr/bin/env bash
# Bounded post-deploy checks for Unified Intake (Cloud Run + browser-origin CORS).
# Does not print secrets. Safe to run from CI or a laptop with gcloud already used for deploy.
#
# Usage:
#   bash scripts/unified_intake_release_gate.sh 'https://fiqa-api-....run.app' 'https://ui-smoky-beta.vercel.app'
#   CLOUD_RUN_URL='...' FRONTEND_ORIGIN='...' bash scripts/unified_intake_release_gate.sh
#
# Requires: curl, python3 (for scripts/test_inbox_triage_api.py — needs httpx).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BASE_URL="${1:-${CLOUD_RUN_URL:-}}"
ORIGIN="${2:-${FRONTEND_ORIGIN:-}}"

if [ -z "$BASE_URL" ]; then
  echo "Usage: $0 <cloud_run_https_url> [frontend_origin_url]"
  echo "   Or: CLOUD_RUN_URL=... FRONTEND_ORIGIN=... $0"
  exit 1
fi

BASE_URL="${BASE_URL%/}"
echo "== Unified Intake release gate =="
echo "   API:    $BASE_URL"
if [ -n "$ORIGIN" ]; then
  echo "   Origin: $ORIGIN"
else
  echo "   Origin: (skipped — pass 2nd arg or FRONTEND_ORIGIN for CORS preflight)"
  echo "⚠️  WARNING: CORS preflight will not run — this is not a complete automated gate." >&2
fi
echo ""

echo "1) Liveness GET /health/live ..."
if ! curl -sf --max-time 15 "${BASE_URL}/health/live" >/dev/null; then
  echo "   FAIL: /health/live not OK (do not use top-level /healthz on Cloud Run edge — see KNOWN_DEPLOYMENT_GOTCHAS.md)"
  exit 1
fi
echo "   OK"

echo "2) Triage API smoke (scripts/test_inbox_triage_api.py) ..."
if ! python3 scripts/test_inbox_triage_api.py --url "$BASE_URL"; then
  echo "   FAIL: triage API test — fix backend/config/key before customer demo"
  exit 1
fi

if [ -n "$ORIGIN" ]; then
  echo "3) CORS preflight for GET /api/inbox/cases (real page origin) ..."
  hdrs=$(mktemp)
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 -D "$hdrs" -X OPTIONS \
    "${BASE_URL}/api/inbox/cases?limit=1" \
    -H "Origin: ${ORIGIN}" \
    -H "Access-Control-Request-Method: GET" || true)
  aca=$(tr -d '\r' <"$hdrs" | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2; exit}')
  rm -f "$hdrs"
  if [ "$code" != "200" ]; then
    echo "   FAIL: OPTIONS returned HTTP $code — add this origin to Cloud Run ALLOWED_ORIGINS (or ALLOWED_ORIGIN_REGEX), then update-traffic --to-latest"
    exit 1
  fi
  if [ "$aca" != "$ORIGIN" ]; then
    echo "   FAIL: OPTIONS 200 but Access-Control-Allow-Origin='$aca' (expected '$ORIGIN')"
    echo "         Serving revision may still be pinned — gcloud run services update-traffic ... --to-latest"
    exit 1
  fi
  echo "   OK (HTTP $code, ACA=$aca)"
fi

echo ""
echo "Automated gate: PASS"
if [ -z "$ORIGIN" ]; then
  echo "⚠️  Remember: without a frontend origin, only liveness + triage API were verified — run again with origin before external demos." >&2
fi
echo "Next (manual): open workbench on the SAME origin you put in ALLOWED_ORIGINS, hard refresh, confirm list loads and one paste/triage cycle."
echo "Full release discipline (do not skip): docs/runbooks/RELEASE_CHECKLIST.md — sections C–D + green bar before \"please try this link.\""
exit 0
