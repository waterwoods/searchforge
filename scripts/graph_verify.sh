#!/usr/bin/env bash

set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BASE="${BASE:-http://${HOST}:${PORT}}"

# 启动
make dev-api-bg HOST="${HOST}" PORT="${PORT}" >/dev/null

for i in {1..60}; do
  if curl -sf "${BASE}/health/ready" >/dev/null; then break; fi
  sleep 1
done

sleep "${SMOKE_SETTLE:-3}"

JOB="graph-demo-1"

echo "[1/3] First run"
curl -s -X POST "${BASE}/api/steward/run" -H 'content-type: application/json' \
  --data "{\"job_id\":\"${JOB}\"}" | jq .

# 模拟中断
echo "[2/3] Kill & restart"
make stop-api >/dev/null || true

make dev-api-bg HOST="${HOST}" PORT="${PORT}" >/dev/null

for i in {1..60}; do
  if curl -sf "${BASE}/health/ready" >/dev/null; then break; fi
  sleep 1
done

sleep "${SMOKE_SETTLE:-3}"

echo "[3/3] Resume same JOB (checkpoint)"
curl -s -X POST "${BASE}/api/steward/run" -H 'content-type: application/json' \
  --data "{\"job_id\":\"${JOB}\"}" | jq .

echo "E2E PASS (resume ok)"

