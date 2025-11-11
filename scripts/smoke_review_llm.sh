#!/usr/bin/env bash
set -euo pipefail

JOB_ID="${JOB_ID:-${JOB:-}}"
PRESET="${PRESET:-smoke-fast}"
API_BASE="${API_BASE:-http://localhost:8000}"
MODE="${MODE:-both}"

if [[ -z "${JOB_ID}" ]]; then
  echo "Usage: JOB_ID=<job-id> $0"
  echo "   or: JOB=<job-id> $0"
  exit 1
fi

RUN_REVIEW="1"
RUN_APPLY="1"
case "${MODE}" in
  review) RUN_APPLY="0" ;;
  apply) RUN_REVIEW="0" ;;
  both) ;;
  *) echo "Invalid MODE=${MODE}. Expected review|apply|both." >&2; exit 1 ;;
esac

function curl_json() {
  local url="$1"
  shift || true
  curl -sS -H 'accept: application/json' "$url" "$@"
}

echo "▶️  LLM env (${API_BASE}/api/steward/debug/llm-env)"
curl_json "${API_BASE}/api/steward/debug/llm-env" | jq .
echo

if [[ "${RUN_REVIEW}" == "1" ]]; then
  echo "▶️  Review (job=${JOB_ID})"
  curl_json "${API_BASE}/api/v1/experiment/review?job_id=${JOB_ID}&suggest=1" | jq '.summary, .baseline, .meta'
  echo
fi

if [[ "${RUN_APPLY}" == "1" ]]; then
  echo "▶️  Apply (preset=${PRESET})"
  curl_json "${API_BASE}/api/v1/experiment/apply" \
    -X POST \
    -H 'content-type: application/json' \
    --data "{\"job_id\":\"${JOB_ID}\",\"preset\":\"${PRESET}\"}" | jq .
fi
