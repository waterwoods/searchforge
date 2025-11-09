#!/usr/bin/env bash
set -euo pipefail

LOG_PREFIX="[BANDIT_PREFLIGHT]"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BASE_URL="${BANDIT_HEALTH_BASE_URL:-http://localhost:8000}"
POLICY_FILE="${REPO_ROOT}/configs/policies.json"

echo "${LOG_PREFIX} starting preflight checks"

all_good=true

declare -a ENDPOINTS=("/api/health/embeddings" "/ready")
for endpoint in "${ENDPOINTS[@]}"; do
    url="${BASE_URL}${endpoint}"
    if curl --fail --silent --show-error --max-time 5 "${url}" > /dev/null; then
        echo "${LOG_PREFIX} endpoint ${endpoint} ok:true"
    else
        echo "${LOG_PREFIX} endpoint ${endpoint} ok:false" >&2
        all_good=false
    fi
done

export LOG_PREFIX
export POLICY_FILE
if python3 - <<'PY'
import json
import os
import pathlib
import sys

log = os.environ["LOG_PREFIX"]
path = pathlib.Path(os.environ["POLICY_FILE"])

if not path.exists():
    print(f"{log} policies_exists:false", flush=True)
    sys.exit(1)

try:
    data = json.loads(path.read_text())
except Exception as exc:  # noqa: BLE001
    print(f"{log} policies_parse:false error={exc}", flush=True)
    sys.exit(2)

required_arms = {"fast_v1", "balanced_v1", "quality_v1"}
policies = data.get("policies", {})
present = {arm for arm in required_arms if arm in policies}

missing = required_arms - present
if missing:
    print(f"{log} policies_valid:false missing={sorted(missing)}", flush=True)
    sys.exit(3)

print(
    f"{log} policies_valid:true arms={sorted(required_arms)} default={data.get('default_policy')}",
    flush=True,
)
PY
then
    :
else
    all_good=false
fi

if [[ "${all_good}" == true ]]; then
    echo "${LOG_PREFIX} preflight status: ok"
    exit 0
else
    echo "${LOG_PREFIX} preflight status: failed"
    exit 1
fi


