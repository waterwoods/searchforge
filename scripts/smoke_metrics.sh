#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
PRESET="${PRESET:-smoke-fast}"
SAMPLE="${SAMPLE:-50}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-240}"
POLL_INTERVAL="${POLL_INTERVAL:-3}"

echo "[metrics] starting experiment preset=${PRESET} sample=${SAMPLE}"
RUN_RESP=$(curl -sS -X POST "${API_BASE}/api/experiment/run" \
  -H 'content-type: application/json' \
  -d "{\"preset\":\"${PRESET}\",\"overrides\":{\"sample\":${SAMPLE}}}")

JOB_ID=$(echo "${RUN_RESP}" | jq -r '.job_id')
POLL_PATH=$(echo "${RUN_RESP}" | jq -r '.poll')
LOGS_PATH=$(echo "${RUN_RESP}" | jq -r '.logs')

if [[ -z "${JOB_ID}" || "${JOB_ID}" == "null" ]]; then
  echo "[metrics] failed to obtain job id: ${RUN_RESP}"
  exit 1
fi

echo "[metrics] job_id=${JOB_ID}"
POLL_URL="${API_BASE}${POLL_PATH}"
LOGS_URL="${API_BASE}${LOGS_PATH}"

deadline=$(( $(date +%s) + WAIT_TIMEOUT ))
status="UNKNOWN"

while :; do
  now=$(date +%s)
  if (( now >= deadline )); then
    echo "[metrics] timeout waiting for job ${JOB_ID}"
    exit 1
  fi
  STATUS_RESP=$(curl -sS "${POLL_URL}")
  status=$(echo "${STATUS_RESP}" | jq -r '.job.status // .status // .state // "UNKNOWN"' | tr '[:lower:]' '[:upper:]')
  echo "[metrics] status=${status}"
  if [[ "${status}" =~ ^(SUCCEEDED|FAILED|ERROR|ABORTED|CANCELLED)$ ]]; then
    break
  fi
  sleep "${POLL_INTERVAL}"
done

if [[ "${status}" != "SUCCEEDED" ]]; then
  echo "[metrics] job ${JOB_ID} ended with status ${status}"
  curl -sS "${LOGS_URL}?tail=80"
  exit 1
fi

LOG_JSON=$(curl -sS "${LOGS_URL}?tail=200")
LINES=$(echo "${LOG_JSON}" | jq '[ (.lines // [])[] | select(startswith("METRICS ")) ] | length')
if [[ "${LINES}" -ne 1 ]]; then
  echo "[metrics] Expected exactly one METRICS line, got ${LINES}"
  exit 1
fi
METRICS_LINE=$(echo "${LOG_JSON}" | jq -r '.lines[] | select(startswith("METRICS "))' | tail -n1)
if [[ -z "${METRICS_LINE}" ]]; then
  echo "[metrics] METRICS line not found in logs"
  echo "${LOG_JSON}" | jq .
  exit 1
fi

P95_VALUE=$(echo "${METRICS_LINE}" | sed -n 's/.*p95_ms=\([0-9]\+\).*/\1/p')
if [[ -z "${P95_VALUE}" || "${P95_VALUE}" -le 0 ]]; then
  echo "[metrics] invalid p95_ms in METRICS line: ${METRICS_LINE}"
  exit 1
fi

echo "[metrics] METRICS line ok: ${METRICS_LINE}"

REVIEW_RESP=$(curl -sS "${API_BASE}/api/steward/review?job_id=${JOB_ID}&suggest=0")
P95_REVIEW=$(echo "${REVIEW_RESP}" | jq -r '.summary.p95_ms // empty')
if [[ -z "${P95_REVIEW}" ]]; then
  echo "[metrics] steward review missing p95_ms:"
  echo "${REVIEW_RESP}" | jq .
  exit 1
fi

python3 - <<'PY' "${P95_REVIEW}"
import sys
try:
    val = float(sys.argv[1])
    if val <= 0:
        raise ValueError("non-positive")
except Exception:
    sys.exit(1)
PY
if [[ $? -ne 0 ]]; then
  echo "[metrics] steward review p95_ms invalid: ${P95_REVIEW}"
  echo "${REVIEW_RESP}" | jq .
  exit 1
fi

echo "[metrics] steward review p95_ms=${P95_REVIEW}"
ERR_REVIEW=$(echo "${REVIEW_RESP}" | jq -r '.summary.err_rate // empty')
if [[ -z "${ERR_REVIEW}" ]]; then
  echo "[metrics] steward review missing err_rate:"
  echo "${REVIEW_RESP}" | jq .
  exit 1
fi

RECALL_REVIEW=$(echo "${REVIEW_RESP}" | jq -r '.summary["recall@10"] // .summary.recall_at_10 // empty')
if [[ -z "${RECALL_REVIEW}" ]]; then
  echo "[metrics] steward review missing recall@10:"
  echo "${REVIEW_RESP}" | jq .
  exit 1
fi

TOKENS_REVIEW=$(echo "${REVIEW_RESP}" | jq -r '.summary.cost_tokens // 0')

python3 - <<'PY' "${ERR_REVIEW}" "${RECALL_REVIEW}" "${TOKENS_REVIEW}"
import sys
try:
    err = float(sys.argv[1])
    recall = float(sys.argv[2])
    tokens = float(sys.argv[3])
    if not (0.0 <= err <= 1.0):
        raise ValueError("err_rate")
    if not (0.0 <= recall <= 1.0):
        raise ValueError("recall")
    if tokens < 0:
        raise ValueError("tokens")
except Exception:
    sys.exit(1)
PY
if [[ $? -ne 0 ]]; then
  echo "[metrics] steward review metrics invalid: err_rate=${ERR_REVIEW}, recall=${RECALL_REVIEW}, cost_tokens=${TOKENS_REVIEW}"
  echo "${REVIEW_RESP}" | jq .
  exit 1
fi

echo "[metrics] steward review err_rate=${ERR_REVIEW} recall@10=${RECALL_REVIEW} cost_tokens=${TOKENS_REVIEW}"
echo "[metrics] smoke metrics check passed (job ${JOB_ID})"

