#!/usr/bin/env bash
# Read-only operator check: live API health + (optional) Cloud Run env wiring for
# Unified Intake data-truth posture. Does not print secret values.
#
# Usage:
#   BASE_URL="https://fiqa-api-…run.app" bash scripts/check_unified_intake_prod_posture.sh
#   bash scripts/check_unified_intake_prod_posture.sh "https://fiqa-api-…run.app"
#
# Exit codes:
#   0 — Reached API; /health shows DB URL present; no contradictory prod posture from /health
#   1 — Unreachable, missing BASE_URL, or clearly unsafe / inconsistent posture
#
# Optional: set SERVICE_NAME, REGION, PROJECT_ID, or rely on gcloud default project.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BASE_URL="${1:-${BASE_URL:-}}"
if [ -z "$BASE_URL" ]; then
  echo "Usage: BASE_URL=<https://…> $0   or   $0 <https://…>" >&2
  exit 1
fi
BASE_URL="${BASE_URL%/}"

fail() {
  echo "❌ $*" >&2
  exit 1
}

ok() { echo "✅ $*"; }

echo "== Unified Intake production posture (read-only) =="
echo "   target: $BASE_URL"
echo ""

tmp="$(mktemp)"
cleanup() { rm -f "$tmp.ver" "$tmp.rd" "$tmp.health" || true; }
trap cleanup EXIT

code=$(curl -sS -o "$tmp.ver" -w '%{http_code}' --max-time 25 "$BASE_URL/version" || echo "000")
[ "$code" = "200" ] || fail "GET /version → HTTP $code"
ok "GET /version → HTTP 200"
code=$(curl -sS -o "$tmp.rd" -w '%{http_code}' --max-time 25 "$BASE_URL/readyz" || echo "000")
[ "$code" = "200" ] || fail "GET /readyz → HTTP $code"
ok "GET /readyz → HTTP 200"
code=$(curl -sS -o "$tmp.health" -w '%{http_code}' --max-time 25 "$BASE_URL/health" || echo "000")
[ "$code" = "200" ] || fail "GET /health → HTTP $code"
ok "GET /health → HTTP 200"

echo ""
echo "--- /version ---"
python3 -m json.tool <"$tmp.ver" 2>/dev/null || head -c 500 "$tmp.ver"
echo ""
echo ""
echo "--- /health (unified_intake_case_persistence) ---"
python3 - <<PY
import json
with open("$tmp.health", "r", encoding="utf-8") as f:
    d = json.load(f)
p = d.get("unified_intake_case_persistence") or {}
if not p:
    print("(no unified_intake_case_persistence in response)")
    raise SystemExit(1)
for k in (
    "unified_intake_case_persistence_mode",
    "has_service_record_database_url",
    "is_production_mode",
    "db_primary_writes",
    "db_primary_reads",
    "json_case_writes",
    "dual_write",
    "postgres_case_persistence_primary",
    "json_read_fallback_allowed",
):
    if k in p:
        print(f"  {k}: {p[k]}")

# Exit non-zero for unsafe / inconsistent
if not p.get("has_service_record_database_url"):
    print("❌ unsafe: has_service_record_database_url is false")
    raise SystemExit(1)
if p.get("is_production_mode") and p.get("json_case_writes"):
    print("❌ unsafe: is_production_mode and json_case_writes both true")
    raise SystemExit(1)
print("✅ /health snapshot self-consistent for minimum safety")

dp = d.get("deployment_profile") or {}
if not dp.get("unified_intake_product_only"):
    print("❌ unsafe: unified_intake_product_only is false on live /health")
    raise SystemExit(1)
auth = dp.get("auth_posture") or {}
intake = dp.get("intake_perimeter") or {}
if auth.get("support_export_surface") != "api_key_required":
    print("❌ unsafe: support_export_surface is not api_key_required")
    raise SystemExit(1)
if intake.get("intake_http_surface") != "api_key_required":
    print("❌ unsafe: intake_http_surface is not api_key_required")
    raise SystemExit(1)
hints = dp.get("operator_runtime_hints") or {}
ow = hints.get("operator_warnings") or []
for code in (
    "production_like_runtime_without_intake_api_key_v1",
    "production_like_runtime_without_support_api_key_v1",
    "platform_full_api_surface_in_production_like_mode_v1",
    "production_like_without_db_primary_writes_v1",
):
    if code in ow:
        print(f"❌ unsafe operator warning present: {code}")
        raise SystemExit(1)
print("✅ deployment_profile product_only + keyed perimeters OK")
PY

SERVICE_NAME="${SERVICE_NAME:-fiqa-api}"
REGION="${REGION:-us-west1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"

if command -v gcloud &>/dev/null && [ -n "$PROJECT_ID" ]; then
  echo ""
  echo "--- gcloud run services describe $SERVICE_NAME ($REGION) — flags (no secret values) ---"
  if gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" &>/dev/null; then
    _CR_JSON=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format=json)
    echo "$_CR_JSON" | python3 -c 'import json,sys
d = json.load(sys.stdin)
env = d.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("env") or []
keys = (
    "ENV", "DEMO_MODE", "UNIFIED_INTAKE_PRODUCT_ONLY",
    "UNIFIED_INTAKE_PG_DUAL_WRITE", "UNIFIED_INTAKE_DB_PRIMARY_WRITES",
    "UNIFIED_INTAKE_DB_PRIMARY_READS", "UNIFIED_INTAKE_JSON_CASE_WRITES",
    "UNIFIED_INTAKE_JSON_READ_FALLBACK", "GIT_SHA", "SOURCE_REV",
)
rev = d.get("status", {}).get("latestReadyRevisionName", "")
if rev:
    print("  latestReadyRevision:", rev)
for e in env:
    n = (e.get("name") or "")
    if n in keys and e.get("value") is not None:
        print("  %s=%s" % (n, e.get("value")))
    if n == "SERVICE_RECORD_DATABASE_URL":
        sref = (e.get("valueFrom") or {}).get("secretKeyRef") or {}
        if sref.get("name"):
            print("  SERVICE_RECORD_DATABASE_URL=secretRef:%s" % sref.get("name"))
        elif e.get("value"):
            print("  SERVICE_RECORD_DATABASE_URL=(set, value not shown)")
    if n == "DATABASE_URL" and (e.get("value") or e.get("valueFrom")):
        print("  DATABASE_URL=(set, value not shown)")
    if n in ("UNIFIED_INTAKE_INTAKE_API_KEY", "UNIFIED_INTAKE_SUPPORT_API_KEY"):
        if e.get("valueFrom", {}).get("secretKeyRef", {}).get("name"):
            print("  %s=secretRef:%s" % (n, e["valueFrom"]["secretKeyRef"]["name"]))
        elif e.get("value"):
            print("  %s=(set, value not shown)" % n)
'
  else
    echo "  (could not describe service — check gcloud auth/project)"
  fi
else
  echo ""
  echo "(gcloud describe skipped: not available or no PROJECT_ID)"
fi

echo ""
ok "check complete (read-only)"
exit 0
