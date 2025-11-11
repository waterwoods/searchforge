#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
JOB="${JOB:-}"

if [[ -z "${JOB}" ]]; then
  echo "Usage: JOB=<job_id> $0"
  exit 1
fi

function expect_keys() {
  local json_payload="$1"
  shift
  local keys=("$@")
  JSON_PAYLOAD="${json_payload}" python3 - "${keys[@]}" <<'PY'
import json
import os
import sys
payload = json.loads(os.environ["JSON_PAYLOAD"])
required = sys.argv[1:]
missing = [key for key in required if key not in payload or payload[key] in (None, "")]
if missing:
    sys.stderr.write(f"missing keys: {', '.join(missing)}\n")
    sys.exit(1)
PY
}

echo "▶️  status (${BASE}/api/v1/experiment/status/${JOB})"
status_json="$(curl -fsS "${BASE}/api/v1/experiment/status/${JOB}")"
expect_keys "${status_json}" job_id status poll logs
echo "${status_json}" | jq '.status, .poll, .logs'
echo

echo "▶️  logs (${BASE}/api/v1/experiment/logs/${JOB}?tail=20)"
logs_json="$(curl -fsS "${BASE}/api/v1/experiment/logs/${JOB}?tail=20")"
expect_keys "${logs_json}" job_id
echo "${logs_json}" | jq '.lines, (.tail | split("\n") | .[0:3])'
echo
echo "▶️  review (${BASE}/api/v1/experiment/review?job_id=${JOB}&suggest=1)"
review_json="$(curl -fsS "${BASE}/api/v1/experiment/review?job_id=${JOB}&suggest=1")"
JSON_PAYLOAD="${review_json}" python3 - <<'PY'
import json
import os
import sys
payload = json.loads(os.environ["JSON_PAYLOAD"])
summary = payload.get("summary") or {}
required = ("p95_ms", "err_rate", "recall_at_10", "cost_tokens")
missing = [key for key in required if key not in summary]
if missing:
    sys.stderr.write(f"review.summary missing: {', '.join(missing)}\n")
    sys.exit(1)
PY
echo "${review_json}" | jq '.summary, .baseline?.summary'
echo

echo "▶️  apply (${BASE}/api/v1/experiment/apply)"
apply_json="$(curl -fsS -X POST \
  "${BASE}/api/v1/experiment/apply" \
  -H 'content-type: application/json' \
  --data "{\"job_id\":\"${JOB}\",\"preset\":\"smoke-fast\"}")"
expect_keys "${apply_json}" job_id poll logs
echo "${apply_json}" | jq '.job_id, .poll, .logs'
echo

echo "✅ smoke-contract checks passed"

