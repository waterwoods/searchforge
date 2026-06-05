#!/usr/bin/env bash
# Reset P16 supervised demo state for AC03 / AC05 / AC07.
#
# Usage:
#   bash scripts/reset_p16_supervised_demo.sh              # local JSON store + instructions
#   bash scripts/reset_p16_supervised_demo.sh --local-api  # also hit local :8001 delete (if up)
#
# Browser session (required for customer "same active case"):
#   DevTools → Application → Local Storage → remove keys:
#     unified_intake_session_id, unified_intake_active_case_id_*

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

LOCAL_API="${LOCAL_API:-http://127.0.0.1:8001}"
DO_LOCAL_API=0
if [[ "${1:-}" == "--local-api" ]]; then
  DO_LOCAL_API=1
fi

echo "=========================================="
echo "P16 Supervised Demo Reset"
echo "=========================================="

# 1) Local JSON case store (founder laptop)
if [[ -f ".env.cloudrun" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.cloudrun
  set +a
fi
export UNIFIED_INTAKE_CASES_PATH="${UNIFIED_INTAKE_CASES_PATH:-data/unified_intake_cases.json}"
PYTHONPATH=. python3 scripts/prepare_unified_intake_founder_demo.py >/dev/null || true
echo "[OK] Local case store reset + demo queue seeded ($(basename "$UNIFIED_INTAKE_CASES_PATH"))"

# 2) Optional: delete recent test cases on local API (keeps demo queue cases)
if [[ "$DO_LOCAL_API" == "1" ]]; then
  KEY="${UNIFIED_INTAKE_INTAKE_API_KEY:-}"
  HDR=()
  if [[ -n "$KEY" ]]; then
    HDR=(-H "X-Unified-Intake-Api-Key: $KEY")
  fi
  if curl -sf "${LOCAL_API}/health/live" >/dev/null 2>&1; then
    echo "[INFO] Local API up — listing cases for optional cleanup"
    CASES=$(curl -sf "${HDR[@]}" "${LOCAL_API}/api/inbox/cases?limit=50" 2>/dev/null || echo '{"cases":[]}')
    python3 - <<'PY' "$CASES" "$LOCAL_API" "${KEY}"
import json, os, sys, urllib.request
cases_json, base, key = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(cases_json or "{}")
removed = 0
for c in (data.get("cases") or []):
    cid = (c.get("case_id") or "").strip()
    src = (c.get("source_text") or "")[:80]
    # Remove add-car demo runs (AC03/05/07 keywords) — keep founder demo queue seeds
    markers = ("Honda Accord", "Tesla Model Y", "Honda Civic", "想加保", "Model Y")
    if cid and any(m in src for m in markers):
        req = urllib.request.Request(
            f"{base}/api/inbox/cases/{cid}",
            method="DELETE",
            headers={"X-Unified-Intake-Api-Key": key} if key else {},
        )
        try:
            urllib.request.urlopen(req, timeout=5)
            removed += 1
        except Exception:
            pass
print(f"[OK] Removed {removed} add-car demo case(s) from local API")
PY
  else
    echo "[SKIP] Local API not running (${LOCAL_API})"
  fi
fi

cat <<'EOF'

Browser reset (required for AC05 return-later):
  1. Open incognito window, OR
  2. DevTools → Application → Local Storage → delete:
       unified_intake_session_id
       unified_intake_active_case_id_* (all client variants)

Preview / Cloud: no server-side case wipe — use incognito per demo part.

Demo URL:
  https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake

Local full UI (all tabs):
  http://localhost:5173/workbench/unified-intake

EOF

echo "Done."
