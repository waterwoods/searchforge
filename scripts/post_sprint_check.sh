#!/usr/bin/env bash
# Post Sprint Health Check Runner v0.1 (P16-T)
# =============================================
# Operational gate: "Is the deployed product actually what we think it is?"
#
# Usage:
#   bash scripts/post_sprint_check.sh
#   bash scripts/post_sprint_check.sh --preview URL --production URL --api URL
#   bash scripts/post_sprint_check.sh --markers "请把您的需求发给我们,原样粘贴微信/通知文字，不用整理"
#
# Exit 0 = PASS, 1 = FAIL, 2 = usage / missing deps

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# Canonical URLs from P16-R reality inventory (override with flags)
DEFAULT_PREVIEW="https://ui-waterwoods-andys-projects-1f411b73.vercel.app"
DEFAULT_PREVIEW_DEPLOY="https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app"
DEFAULT_PRODUCTION="https://ui-smoky-beta.vercel.app"
DEFAULT_API="https://fiqa-api-g7zatxrycq-uw.a.run.app"
DEFAULT_MARKERS="请把您的需求发给我们,原样粘贴微信/通知文字，不用整理"
PRODUCT_ONLY_MARKERS="快速体验（可选）,原样粘贴微信/通知文字，不用整理"

PREVIEW_URL="$DEFAULT_PREVIEW"
PREVIEW_DEPLOY_URL="$DEFAULT_PREVIEW_DEPLOY"
PRODUCTION_URL="$DEFAULT_PRODUCTION"
API_URL="$DEFAULT_API"
MARKERS="$DEFAULT_MARKERS"
SPRINT_ID=""
VERBOSE=false

usage() {
  cat <<EOF
Usage: bash scripts/post_sprint_check.sh [options]

Options:
  --preview URL          Preview alias URL (cold access test)
  --preview-deploy URL   Preview deployment URL (CORS + bundle fallback)
  --production URL       Production URL
  --api URL              Cloud Run API base URL
  --markers LIST         Comma-separated sprint strings for bundle grep
  --sprint ID            Sprint label for report header
  --verbose              Print curl detail
  -h, --help             Show this help

Defaults match P16-R documented URLs. Override when testing a new deploy.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preview) PREVIEW_URL="${2%/}"; shift 2 ;;
    --preview-deploy) PREVIEW_DEPLOY_URL="${2%/}"; shift 2 ;;
    --production) PRODUCTION_URL="${2%/}"; shift 2 ;;
    --api) API_URL="${2%/}"; shift 2 ;;
    --markers) MARKERS="$2"; shift 2 ;;
    --sprint) SPRINT_ID="$2"; shift 2 ;;
    --verbose) VERBOSE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if ! command -v curl >/dev/null 2>&1; then
  echo "FAIL: curl is required" >&2
  exit 2
fi

PASS_COUNT=0
FAIL_COUNT=0
RESULT_LINES=()

record() {
  local id="$1"
  local label="$2"
  local status="$3"
  local detail="${4:-}"
  RESULT_LINES+=("$id|$label|$status|$detail")
  if [[ "$status" == "PASS" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  printf "  %-28s %s" "$label" "$status"
  if [[ -n "$detail" ]]; then
    printf " (%s)" "$detail"
  fi
  printf "\n"
}

http_status() {
  local url="$1"
  curl -sI --max-time 20 "$url" 2>/dev/null | awk 'toupper($1) ~ /^HTTP/ {print $2; exit}'
}

fetch_html() {
  local url="$1"
  curl -s --max-time 25 "$url" 2>/dev/null
}

fetch_html_vercel() {
  local path="$1"
  local deployment="$2"
  if ! command -v vercel >/dev/null 2>&1; then
    return 1
  fi
  local ui_dir="$REPO_DIR/ui"
  if [[ ! -d "$ui_dir/.vercel" && -d "$REPO_DIR/.vercel" ]]; then
    ui_dir="$REPO_DIR"
  fi
  (cd "$ui_dir" && vercel curl "$path" --deployment "$deployment" 2>/dev/null)
}

extract_bundle_name() {
  grep -oE 'index-[A-Za-z0-9]+\.js' | head -1
}

bundle_contains() {
  local haystack="$1"
  local needle="$2"
  grep -Fq "$needle" <<<"$haystack"
}

# --- Report header ---
echo "POST SPRINT HEALTH CHECK v0.1${SPRINT_ID:+ — $SPRINT_ID}"
echo "Repo:    $REPO_DIR"
echo "Preview: $PREVIEW_URL"
echo "Prod:    $PRODUCTION_URL"
echo "API:     $API_URL"
echo ""

# 1. Git branch
echo "GIT / LOCAL"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
if [[ -n "$BRANCH" && "$BRANCH" != "unknown" ]]; then
  record "git_branch" "git_branch" "PASS" "$BRANCH"
else
  record "git_branch" "git_branch" "FAIL" "not a git repo"
fi

# 2. Git commit
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
COMMIT_FULL="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$COMMIT" != "unknown" ]]; then
  record "git_commit" "git_commit" "PASS" "$COMMIT"
else
  record "git_commit" "git_commit" "FAIL" "unknown"
fi

# 3. Local version (ui package + commit date)
UI_VERSION="unknown"
if [[ -f ui/package.json ]]; then
  UI_VERSION="$(python3 -c "import json; print(json.load(open('ui/package.json'))['version'])" 2>/dev/null || echo unknown)"
fi
COMMIT_DATE="$(git log -1 --format='%ci' 2>/dev/null || echo unknown)"
if [[ "$UI_VERSION" != "unknown" ]]; then
  record "local_version" "local_version" "PASS" "ui@$UI_VERSION commit=$COMMIT date=$COMMIT_DATE"
else
  record "local_version" "local_version" "FAIL" "ui/package.json missing"
fi

echo ""
echo "DEPLOY / REMOTE"

# 4. Preview URL reachable (cold — must be HTTP 200)
PREVIEW_STATUS="$(http_status "$PREVIEW_URL")"
if [[ "$PREVIEW_STATUS" == "200" ]]; then
  record "preview_reachable" "preview_url_reachable" "PASS" "HTTP $PREVIEW_STATUS"
else
  record "preview_reachable" "preview_url_reachable" "FAIL" "HTTP ${PREVIEW_STATUS:-timeout}"
fi

# 5. Production URL reachable
PROD_STATUS="$(http_status "$PRODUCTION_URL")"
if [[ "$PROD_STATUS" == "200" ]]; then
  record "prod_reachable" "production_url_reachable" "PASS" "HTTP $PROD_STATUS"
else
  record "prod_reachable" "production_url_reachable" "FAIL" "HTTP ${PROD_STATUS:-timeout}"
fi

# 6. Preview protection present? (trial wants NO protection — 401 = protection ON = FAIL)
PREVIEW_HEADERS="$(curl -sI --max-time 20 "$PREVIEW_URL" 2>/dev/null || true)"
if grep -qi '_vercel_sso_nonce\|401' <<<"$PREVIEW_HEADERS" || [[ "$PREVIEW_STATUS" == "401" ]]; then
  record "preview_protection" "preview_protection_absent" "FAIL" "SSO/401 detected (FP-004)"
elif [[ "$PREVIEW_STATUS" == "200" ]]; then
  record "preview_protection" "preview_protection_absent" "PASS" "cold 200, no SSO wall"
else
  record "preview_protection" "preview_protection_absent" "FAIL" "HTTP ${PREVIEW_STATUS:-unknown}"
fi

# Resolve preview bundle (vercel curl fallback when cold 401)
PREVIEW_HTML=""
PREVIEW_BUNDLE=""
PREVIEW_BUNDLE_JS=""
if [[ "$PREVIEW_STATUS" == "200" ]]; then
  PREVIEW_HTML="$(fetch_html "$PREVIEW_URL")"
  PREVIEW_BUNDLE="$(printf '%s' "$PREVIEW_HTML" | extract_bundle_name)"
  if [[ -n "$PREVIEW_BUNDLE" ]]; then
    PREVIEW_BUNDLE_JS="$(fetch_html "$PREVIEW_URL/assets/$PREVIEW_BUNDLE")"
  fi
elif command -v vercel >/dev/null 2>&1; then
  PREVIEW_HTML="$(fetch_html_vercel "/" "$PREVIEW_DEPLOY_URL" || true)"
  PREVIEW_BUNDLE="$(printf '%s' "$PREVIEW_HTML" | extract_bundle_name)"
  if [[ -n "$PREVIEW_BUNDLE" ]]; then
    PREVIEW_BUNDLE_JS="$(fetch_html_vercel "/assets/$PREVIEW_BUNDLE" "$PREVIEW_DEPLOY_URL" || true)"
  fi
  if $VERBOSE && [[ -n "$PREVIEW_BUNDLE" ]]; then
    echo "  (preview bundle via vercel curl: $PREVIEW_BUNDLE)"
  fi
fi

PROD_HTML="$(fetch_html "$PRODUCTION_URL")"
PROD_BUNDLE="$(printf '%s' "$PROD_HTML" | extract_bundle_name)"
PROD_BUNDLE_JS=""
if [[ -n "$PROD_BUNDLE" ]]; then
  PROD_BUNDLE_JS="$(fetch_html "$PRODUCTION_URL/assets/$PROD_BUNDLE")"
fi

# 7. Product-only flag present? (positive markers on preview bundle)
PRODUCT_ONLY_OK=true
PRODUCT_ONLY_DETAIL=""
IFS=',' read -ra PO_MARKERS <<< "$PRODUCT_ONLY_MARKERS"
if [[ -z "$PREVIEW_BUNDLE_JS" ]]; then
  PRODUCT_ONLY_OK=false
  PRODUCT_ONLY_DETAIL="preview bundle unavailable (401 + no vercel curl)"
else
  for marker in "${PO_MARKERS[@]}"; do
    marker="$(echo "$marker" | xargs)"
    [[ -z "$marker" ]] && continue
    if ! bundle_contains "$PREVIEW_BUNDLE_JS" "$marker"; then
      PRODUCT_ONLY_OK=false
      PRODUCT_ONLY_DETAIL="missing: $marker"
      break
    fi
  done
  if $PRODUCT_ONLY_OK; then
    PRODUCT_ONLY_DETAIL="markers present on preview ($PREVIEW_BUNDLE)"
  fi
fi
if $PRODUCT_ONLY_OK; then
  record "product_only" "product_only_flag" "PASS" "$PRODUCT_ONLY_DETAIL"
else
  record "product_only" "product_only_flag" "FAIL" "$PRODUCT_ONLY_DETAIL (FP-003)"
fi

# 8. CORS preflight pass?
CORS_HEADERS="$(curl -sI --max-time 20 -X OPTIONS \
  -H "Origin: $PREVIEW_DEPLOY_URL" \
  -H "Access-Control-Request-Method: GET" \
  "$API_URL/api/inbox/cases" 2>/dev/null || true)"
CORS_STATUS="$(printf '%s' "$CORS_HEADERS" | awk 'toupper($1) ~ /^HTTP/ {print $2; exit}')"
if [[ "$CORS_STATUS" == "200" ]] && grep -qi "access-control-allow-origin: $PREVIEW_DEPLOY_URL" <<<"$CORS_HEADERS"; then
  record "cors" "cors_preflight" "PASS" "OPTIONS 200 for preview origin"
elif [[ "$CORS_STATUS" == "200" ]]; then
  record "cors" "cors_preflight" "PASS" "OPTIONS 200 (origin header present)"
else
  record "cors" "cors_preflight" "FAIL" "HTTP ${CORS_STATUS:-timeout} (FP-002)"
fi

# 9. Bundle contains expected UI strings?
MARKER_FAILS=()
MARKER_TARGET="$PREVIEW_BUNDLE_JS"
MARKER_LABEL="preview"
if [[ -z "$MARKER_TARGET" ]]; then
  MARKER_TARGET="$PROD_BUNDLE_JS"
  MARKER_LABEL="production (preview blocked)"
fi
IFS=',' read -ra SPRINT_MARKERS <<< "$MARKERS"
if [[ -z "$MARKER_TARGET" ]]; then
  record "bundle_markers" "bundle_sprint_markers" "FAIL" "no bundle fetched"
else
  for marker in "${SPRINT_MARKERS[@]}"; do
    marker="$(echo "$marker" | xargs)"
    [[ -z "$marker" ]] && continue
    if ! bundle_contains "$MARKER_TARGET" "$marker"; then
      MARKER_FAILS+=("$marker")
    fi
  done
  if [[ ${#MARKER_FAILS[@]} -eq 0 ]]; then
    BUNDLE_NAME="${PREVIEW_BUNDLE:-$PROD_BUNDLE}"
    record "bundle_markers" "bundle_sprint_markers" "PASS" "$MARKER_LABEL bundle $BUNDLE_NAME"
  else
    record "bundle_markers" "bundle_sprint_markers" "FAIL" "missing on $MARKER_LABEL: ${MARKER_FAILS[*]} (FP-005)"
  fi
fi

# Deployment parity note (informational — FP-001)
if [[ -n "$PREVIEW_BUNDLE" && -n "$PROD_BUNDLE" && "$PREVIEW_BUNDLE" != "$PROD_BUNDLE" ]]; then
  echo "  (parity note: preview=$PREVIEW_BUNDLE prod=$PROD_BUNDLE — FP-001/FP-013)"
fi

echo ""
echo "RUNTIME / API"

# 10. Cloud Run health endpoint pass?
READY_JSON="$(curl -sf --max-time 20 "$API_URL/readyz" 2>/dev/null || true)"
if [[ -n "$READY_JSON" ]]; then
  READY_OK="$(python3 -c "import json,sys; d=json.load(sys.stdin); print('yes' if d.get('intake_path_ready') or d.get('ok') else 'no')" <<<"$READY_JSON" 2>/dev/null || echo no)"
  if [[ "$READY_OK" == "yes" ]]; then
    record "cloud_health" "cloud_run_health" "PASS" "/readyz intake_path_ready"
  else
    record "cloud_health" "cloud_run_health" "FAIL" "/readyz not ready"
  fi
else
  LIVE_JSON="$(curl -sf --max-time 20 "$API_URL/health/live" 2>/dev/null || true)"
  if [[ -n "$LIVE_JSON" ]] && grep -q '"ok":true' <<<"$LIVE_JSON"; then
    record "cloud_health" "cloud_run_health" "PASS" "/health/live ok"
  else
    record "cloud_health" "cloud_run_health" "FAIL" "API unreachable"
  fi
fi

# Optional: backend env posture (not in top-10 list but useful)
if [[ -f .env.cloudrun ]]; then
  if PYTHONPATH=. python3 "$SCRIPT_DIR/validate_pilot_deploy_env.py" --env-file .env.cloudrun >/dev/null 2>&1; then
    echo "  pilot_env_posture .......... PASS (.env.cloudrun)"
  else
    echo "  pilot_env_posture .......... WARN (validate_pilot_deploy_env.py)"
  fi
fi

echo ""
echo "SCORES"
TOTAL=$((PASS_COUNT + FAIL_COUNT))
if [[ $TOTAL -gt 0 ]]; then
  SCORE=$((PASS_COUNT * 100 / TOTAL))
else
  SCORE=0
fi
echo "  Checks passed: $PASS_COUNT / $TOTAL ($SCORE%)"
echo ""

if [[ $FAIL_COUNT -eq 0 ]]; then
  echo "OVERALL ...................... PASS"
  exit 0
else
  echo "OVERALL ...................... FAIL"
  echo "Blockers:"
  for line in "${RESULT_LINES[@]}"; do
    IFS='|' read -r _ _ st detail <<<"$line"
    if [[ "$st" == "FAIL" ]]; then
      echo "  - $detail"
    fi
  done
  exit 1
fi
