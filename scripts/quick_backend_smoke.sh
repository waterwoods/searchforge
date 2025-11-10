#!/usr/bin/env bash
set -euo pipefail

PRESET="${PRESET:-smoke}"
DETAIL="${DETAIL:-lite}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
POLL_EVERY="${POLL_EVERY:-3}"

json_escape() {
  python3 -c 'import json, sys; print(json.dumps(sys.argv[1]))' "$1"
}

BASE=""
MODE=""
BASE_HOST=""

if curl -sf --max-time 2 http://localhost:5173/ready >/dev/null 2>&1; then
  BASE_HOST="http://localhost:5173"
  BASE="${BASE_HOST}/orchestrate"
  MODE="proxy"
elif curl -sf --max-time 2 http://localhost:8000/ready >/dev/null 2>&1; then
  BASE_HOST="http://localhost:8000"
  BASE="${BASE_HOST}/api/experiment"
  MODE="direct"
else
  echo "[smoke] backend not ready (5173/8000)"
  exit 1
fi

echo "[smoke] mode=${MODE} base=${BASE} preset=${PRESET} detail=${DETAIL}"

REQ_BODY=$(cat <<EOF
{"preset":"${PRESET}","overrides":{"sample_limit":50}}
EOF
)

RUN_RESP=$(curl -sS -X POST -H 'content-type: application/json' -d "${REQ_BODY}" "${BASE}/run" -w '\n%{http_code}')
HTTP_CODE="${RUN_RESP##*$'\n'}"
RUN_JSON="${RUN_RESP%$'\n'*}"

if [[ "${HTTP_CODE}" != "202" && "${HTTP_CODE}" != "200" ]]; then
  echo "[smoke] run http=${HTTP_CODE} body=${RUN_JSON}"
  exit 1
fi

JOB_ID=$(printf '%s' "${RUN_JSON}" | python3 -c 'import json, sys
try:
    data = json.loads(sys.stdin.read())
except Exception:
    data = {}
print(data.get("job_id") or data.get("jobId") or data.get("run_id") or "")'
)

POLL_FROM_JSON=$(printf '%s' "${RUN_JSON}" | python3 -c 'import json, sys
try:
    data = json.loads(sys.stdin.read())
except Exception:
    data = {}
print(data.get("poll") or "")'
)

if [[ -z "${JOB_ID}" ]]; then
  echo "[smoke] missing job_id. body=${RUN_JSON}"
  exit 1
fi

strip_host() {
  printf '%s' "$1" | sed -E 's#^https?://[^/]+##'
}

resolve_poll_path() {
  local raw="$1"
  local desired_root
  if [[ "${MODE}" == "proxy" ]]; then
    desired_root="/orchestrate"
  else
    desired_root="/api/experiment"
  fi

  if [[ -z "${raw}" ]]; then
    if [[ "${MODE}" == "proxy" ]]; then
      printf '/orchestrate/status/%s' "${JOB_ID}"
    else
      printf '/api/experiment/status/%s' "${JOB_ID}"
    fi
    return 0
  fi

  local path
  path="$(strip_host "${raw}")"
  if [[ "${MODE}" == "proxy" ]]; then
    path="$(printf '%s' "${path}" | sed -E 's#^/api/experiment#'"${desired_root}"'#')"
  else
    path="$(printf '%s' "${path}" | sed -E 's#^/orchestrate#'"${desired_root}"'#')"
  fi

  if [[ "${path}" != /* ]]; then
    path="/${path}"
  fi
  printf '%s' "${path}"
}

POLL_PATH="$(resolve_poll_path "${POLL_FROM_JSON}")"
LOGS_PATH="$(printf '%s' "${POLL_PATH}" | sed -E 's#/status/#/logs/#g')"
POLL_URL="${BASE_HOST}${POLL_PATH}"
LOGS_URL="${BASE_HOST}${LOGS_PATH}"

echo "[smoke] job_id=${JOB_ID}"
echo "[smoke] poll=${POLL_PATH}"
echo "[smoke] logs=${LOGS_PATH}"

START_TS=$(date +%s)
FINAL="UNKNOWN"
LAST_LOG_TAIL=""

deadline=$(( START_TS + TIMEOUT_SEC ))
while :; do
  NOW=$(date +%s)
  if (( NOW >= deadline )); then
    FINAL="TIMEOUT"
    break
  fi

  STAT_URL="${POLL_URL}?detail=${DETAIL}"
  RESP=$(curl -sS -X GET "${STAT_URL}" -w '\n%{http_code}')
  CODE="${RESP##*$'\n'}"
  BODY="${RESP%$'\n'*}"

  if [[ "${CODE}" != "200" && "${CODE}" != "202" ]]; then
    echo "[smoke] status http=${CODE} body=${BODY}"
    FINAL="HTTP_${CODE}"
    break
  fi

  STATUS=$(printf '%s' "${BODY}" | python3 -c 'import json, sys
body = sys.stdin.read()
try:
    data = json.loads(body)
except Exception:
    data = {}
job = data.get("job") or {}
print((data.get("state") or data.get("status") or job.get("status") or "").upper())'
)

  if [[ -z "${STATUS}" ]]; then
    STATUS="$(printf '%s' "${BODY}" | head -n 1 | tr -d '\r')"
  fi

  TS=$(date +'%H:%M:%S')
  echo "[${TS}] status=${STATUS}"

  LOG_TAIL=$(curl -sS "${LOGS_URL}?tail=30" || true)
  if [[ -n "${LOG_TAIL}" ]]; then
    printf '%s\n' "${LOG_TAIL}"
    LAST_LOG_TAIL="${LOG_TAIL}"
  fi

  case "${STATUS}" in
    SUCCEEDED|SUCCESS|DONE|COMPLETED)
      FINAL="${STATUS}"
      break
      ;;
    FAILED|ERROR|CANCELED|CANCELLED)
      FINAL="${STATUS}"
      break
      ;;
    *)
      :
      ;;
  esac

  sleep "${POLL_EVERY}"
done

END_TS=$(date +%s)
DUR=$(( END_TS - START_TS ))

SNIPPET=""
if [[ -n "${LAST_LOG_TAIL}" ]]; then
  SNIPPET=$(printf '%s' "${LAST_LOG_TAIL}" | tail -n 5 | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g' | cut -c1-240)
fi

printf '%s\n' "{
  \"job_id\": $(json_escape "${JOB_ID}"),
  \"final_status\": $(json_escape "${FINAL}"),
  \"duration_sec\": ${DUR},
  \"poll_url\": $(json_escape "${POLL_PATH}"),
  \"error_snippet\": $(json_escape "${SNIPPET}")
}"

if [[ "${FINAL}" == "TIMEOUT" ]]; then
  exit 2
fi
if [[ "${FINAL}" == "FAILED" || "${FINAL}" == "ERROR" ]]; then
  exit 3
fi
if [[ "${FINAL}" == HTTP_* ]]; then
  exit 3
fi
exit 0

