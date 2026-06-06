#!/usr/bin/env bash
# Human-readable support posture from live API (no secret values printed).
#
# Usage:
#   bash scripts/summarize_support_posture.sh http://127.0.0.1:8001
#   UNIFIED_INTAKE_SUPPORT_API_KEY=... bash scripts/summarize_support_posture.sh <URL>
#
# Reads /health (always) and deployment-manifest when support key is set.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

BASE_URL="${1:-${BASE_URL:-}}"
if [[ -z "$BASE_URL" ]]; then
  echo "Usage: $0 <api-base-url>" >&2
  echo "  Example: bash scripts/summarize_support_posture.sh http://127.0.0.1:8001" >&2
  exit 1
fi
BASE_URL="${BASE_URL%/}"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

echo "=== Unified Intake support posture ==="
echo "  URL: $BASE_URL"
echo ""

if ! curl -sf --max-time 15 "$BASE_URL/health/live" >/dev/null 2>&1; then
  echo "  Liveness: FAIL — service not reachable at /health/live"
  exit 1
fi
echo "  Liveness: OK (/health/live)"

if ! curl -sf --max-time 15 "$BASE_URL/health" -o "$TMP"; then
  echo "  /health: FAIL"
  exit 1
fi

PYTHONPATH=. python3 - "$TMP" <<'PY'
import json
import sys
from pathlib import Path

from services.fiqa_api.deployment_profile import humanize_operator_warnings

path = Path(sys.argv[1])
d = json.loads(path.read_text(encoding="utf-8"))
persist = d.get("unified_intake_case_persistence") or {}
dp = d.get("deployment_profile") or {}
hints = dp.get("operator_runtime_hints") or {}
posture = hints.get("intake_readiness_posture") or {}

print("")
print("  Deployment:")
print(f"    product_only:     {dp.get('unified_intake_product_only')}")
print(f"    readiness_mode:   {posture.get('readiness_mode', '?')}")
print(f"    demo_mode:        {hints.get('demo_mode')}")
print(f"    env:              {hints.get('env_label_raw') or '(unset)'}")

mode = persist.get("unified_intake_case_persistence_mode") or "?"
print("")
print("  Persistence:")
print(f"    mode:             {mode}")
print(f"    postgres URL set: {persist.get('has_service_record_database_url')}")
print(f"    PG primary writes:{persist.get('db_primary_writes')}")
print(f"    JSON case writes: {persist.get('json_case_writes')}")

auth = dp.get("auth_posture") or {}
intake = dp.get("intake_perimeter") or {}
print("")
print("  Perimeters:")
print(f"    intake surface:   {intake.get('intake_http_surface', '?')}")
print(f"    support export:   {auth.get('support_export_surface', '?')}")

warnings = hints.get("operator_warnings") or []
human = hints.get("operator_warnings_human") or humanize_operator_warnings(warnings)
print("")
if warnings:
    print(f"  Warnings ({len(warnings)}):")
    for line in human:
        print(f"    - {line}")
else:
    print("  Warnings: none")

ident = hints.get("deployment_identity") or {}
if ident.get("k_revision"):
    print("")
    print("  Cloud Run revision:", ident.get("k_revision"))
if ident.get("commit_sha_from_env"):
    print("  Commit (env):      ", ident.get("commit_sha_from_env")[:12])
PY

SUPPORT_KEY="${UNIFIED_INTAKE_SUPPORT_API_KEY:-}"
if [[ -n "$SUPPORT_KEY" ]]; then
  MANIFEST_TMP="$(mktemp)"
  trap 'rm -f "$TMP" "$MANIFEST_TMP"' EXIT
  code=$(curl -sS -o "$MANIFEST_TMP" -w '%{http_code}' --max-time 15 \
    -H "X-Unified-Intake-Support-Key: $SUPPORT_KEY" \
    "$BASE_URL/api/inbox/support/deployment-manifest" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo ""
    echo "  Support manifest: OK (authenticated)"
    PYTHONPATH=. python3 - "$MANIFEST_TMP" <<'PY'
import json
import sys
from pathlib import Path

m = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
git = m.get("git") or {}
print(f"    git commit:       {(git.get('commit') or '?')[:12]}")
print(f"    schema epoch:     {m.get('intake_schema_epoch', '?')}")
PY
  else
    echo ""
    echo "  Support manifest: HTTP $code (check UNIFIED_INTAKE_SUPPORT_API_KEY)"
  fi
else
  echo ""
  echo "  Support manifest: SKIP (set UNIFIED_INTAKE_SUPPORT_API_KEY to probe)"
fi

echo ""
echo "  Next: bash scripts/summarize_readiness_posture.sh --probe '$BASE_URL'"
