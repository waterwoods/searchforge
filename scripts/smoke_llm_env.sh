#!/usr/bin/env bash

set -euo pipefail

BASE="${BASE:-http://localhost:8000}"

echo "== Debug LLM env =="
curl -s "$BASE/api/steward/debug/llm-env" | jq '{model, key_present, max_tokens, budget_usd, source, api_key_masked, input_per_mtok, output_per_mtok}'

JOB="${JOB_ID:-e44bd0f971e2}"  # replace with any existing job id

echo "== Review with suggest =="
curl -s "$BASE/api/steward/review?job_id=$JOB&suggest=1" | jq '{job_id, meta, reflection, suggestion}'

