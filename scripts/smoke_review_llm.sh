#!/usr/bin/env bash
set -euo pipefail

JOB_ID="${JOB_ID:-${JOB:-}}"
PRESET="${PRESET:-smoke-fast}"
API_BASE="${API_BASE:-http://localhost:8000}"

if [[ -z "${JOB_ID}" ]]; then
  echo "Usage: JOB_ID=<job-id> $0"
  echo "   or: JOB=<job-id> $0"
  exit 1
fi

function curl_json() {
  local url="$1"
  shift || true
  curl -sS -H 'accept: application/json' "$url" "$@"
}

echo "▶️  LLM env (${API_BASE}/api/steward/debug/llm-env)"
curl_json "${API_BASE}/api/steward/debug/llm-env" | jq .
echo

echo "▶️  Review (job=${JOB_ID})"
curl_json "${API_BASE}/api/steward/review?job_id=${JOB_ID}&suggest=1" | jq '.summary, .baseline, .meta.reflection_source'
echo

echo "▶️  Apply (preset=${PRESET})"
curl_json "${API_BASE}/api/steward/apply" \
  -X POST \
  -H 'content-type: application/json' \
  --data "{\"job_id\":\"${JOB_ID}\",\"preset\":\"${PRESET}\"}" | jq .
