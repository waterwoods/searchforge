#!/usr/bin/env bash
# Human-readable intake vs full-stack readiness summary (no secrets).
#
# Usage: bash scripts/summarize_readiness_posture.sh
#        bash scripts/summarize_readiness_posture.sh --probe http://127.0.0.1:8001

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

PROBE_URL=""
if [[ "${1:-}" == "--probe" && -n "${2:-}" ]]; then
  PROBE_URL="${2%/}"
fi

echo "=== Unified Intake readiness (from env) ==="
PYTHONPATH=. python3 - <<'PY'
from services.fiqa_api.deployment_profile import (
    deployment_operator_warnings,
    humanize_operator_warnings,
    intake_readiness_posture_dict,
    is_unified_intake_product_only,
)

posture = intake_readiness_posture_dict()
mode = posture.get("readiness_mode", "?")
print(f"  Mode:           {mode}")
print(f"  Product-only:   {'yes' if posture.get('product_only') else 'no (lab/dev — set UNIFIED_INTAKE_PRODUCT_ONLY=1 for pilot)'}")
print(f"  Demo mode:      {'yes' if posture.get('demo_mode') else 'no'}")
print(f"  Qdrant blocks /readyz: {'yes' if posture.get('qdrant_blocks_readyz') else 'no (vectors optional)'}")
print(f"  Intake triage needs Qdrant: no")
print(f"  Note: {posture.get('operator_note', '')}")

warnings = deployment_operator_warnings()
if warnings:
    print("")
    print(f"  Env warnings ({len(warnings)}):")
    for line in humanize_operator_warnings(warnings):
        print(f"    - {line}")
else:
    print("  Env warnings:   none")
PY

if [[ -n "$PROBE_URL" ]]; then
  echo ""
  echo "=== Live probe: $PROBE_URL ==="
  if curl -sf --max-time 8 "$PROBE_URL/readyz" | PYTHONPATH=. python3 -c "
import json, sys
d = json.load(sys.stdin)
mode = d.get('readiness_mode', '?')
ok = d.get('ok')
ipr = d.get('intake_path_ready')
qdrant = (d.get('clients') or {}).get('qdrant_connected')
print(f'  /readyz ok:              {ok}')
print(f'  intake_path_ready:       {ipr}')
print(f'  readiness_mode:          {mode}')
print(f'  qdrant_connected:        {qdrant}')
if ipr is True:
    print('  → Intake can run (vectors optional when intake_core)')
elif ok is True:
    print('  → Full-stack ready')
else:
    print('  → Check Postgres + API keys; see OPERATOR_CHEAT_SHEET.md')
"; then
    :
  else
    echo "  SKIP or FAIL (API not reachable — start: bash scripts/run_demo_local.sh)"
  fi
fi

echo ""
echo "=== What to check (operators) ==="
echo "  Liveness:  GET /health/live     (NOT bare /healthz on Cloud Run)"
echo "  Intake:    GET /readyz           → intake_path_ready matters more than ok"
echo "  Support:   GET /api/inbox/support/deployment-manifest  (support API key)"
echo "  Ignore:    GET /ready           (legacy RAG — needs Qdrant)"
echo "  Ignore list: docs/runbooks/OPERATOR_IGNORE_LIST.md"
echo ""
echo "  Paid pilot deploy: bash scripts/deploy_paid_pilot.sh"
echo "  Local pilot posture: UNIFIED_INTAKE_PRODUCT_ONLY=1 (see demo.env.example)"
echo "  More: docs/runbooks/OPERATOR_CHEAT_SHEET.md"
