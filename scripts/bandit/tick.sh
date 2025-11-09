#!/usr/bin/env bash
set -euo pipefail

BASE="${BANDIT_HEALTH_BASE_URL:-http://localhost:8000}"
export BANDIT_HEALTH_BASE_URL="${BASE}"

echo "[TICK] base=${BASE}"

scripts/bandit/preflight.sh

SELECT_JSON="$(mktemp /tmp/bandit_select.XXXX.json)"
trap 'rm -f "$SELECT_JSON"' EXIT
python3 scripts/bandit/select.py \
  --algo "${BANDIT_SELECT_ALGO:-ucb1}" \
  --eps "${BANDIT_SELECT_EPS:-0.1}" \
  --eps-decay "${BANDIT_SELECT_EPS_DECAY:-0.98}" \
  --min-samples "${BANDIT_SELECT_MIN_SAMPLES:-15}" \
  --print-json > "${SELECT_JSON}"

echo "[SELECT] $(cat "${SELECT_JSON}")"

ARM="$(python3 -c "import json;print(json.load(open('${SELECT_JSON}'))['picked'])")"

echo "[APPLY] arm=${ARM}"
python3 scripts/bandit/apply.py --arm "${ARM}" --base "${BASE}" --print-json

echo "[TICK] done."

