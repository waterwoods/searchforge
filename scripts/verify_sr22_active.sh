#!/bin/bash
# Verify SR-22 / proof-of-insurance improvements are active in running backend.
# Usage: bash scripts/verify_sr22_active.sh [--port 8001]
# Exit 0 if LT03/LT04 pass; exit 1 otherwise.
set -euo pipefail
PORT=8001
[[ "${1:-}" == "--port" ]] && [[ -n "${2:-}" ]] && PORT="$2"
BASE="http://127.0.0.1:${PORT}"
echo "Verifying SR-22 activation at $BASE ..."
OUT=$(python3 scripts/broker_regression_all5.py --port "$PORT" --longtail 2>&1)
RC=$?
echo "$OUT" | tail -8
exit $RC
