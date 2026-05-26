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

echo "=== Readiness posture (from env) ==="
PYTHONPATH=. python3 - <<'PY'
import json
import os
from services.fiqa_api.deployment_profile import intake_readiness_posture_dict

print(json.dumps(intake_readiness_posture_dict(), indent=2))
PY

if [[ -n "$PROBE_URL" ]]; then
  echo ""
  echo "=== Live /readyz probe: $PROBE_URL/readyz ==="
  if curl -sf --max-time 5 "$PROBE_URL/readyz" | PYTHONPATH=. python3 -c "
import json, sys
d = json.load(sys.stdin)
print('  ok:', d.get('ok'))
print('  readiness_mode:', d.get('readiness_mode'))
print('  intake_path_ready:', d.get('intake_path_ready'))
print('  qdrant_connected:', (d.get('clients') or {}).get('qdrant_connected'))
"; then
    :
  else
    echo "  SKIP or FAIL (API not reachable — start: bash scripts/run_demo_local.sh)"
  fi
fi

echo ""
echo "Modes:"
echo "  intake_core — triage SaaS OK without Qdrant (DEMO_MODE or UNIFIED_INTAKE_INTAKE_CORE_READINESS=1 + PRODUCT_ONLY)"
echo "  full_stack  — /readyz requires Qdrant + embedding (RAG lab path)"
echo "Paid pilot: prefer INTAKE_CORE_READINESS over DEMO_MODE (validators forbid DEMO_MODE on prod)."
