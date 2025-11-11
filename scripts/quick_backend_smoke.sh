#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"

READY_TIMEOUT="${SMOKE_READY_TIMEOUT:-60}"
for i in $(seq 1 "${READY_TIMEOUT}"); do
  if curl -sf "${BASE}/health/live" >/dev/null 2>&1 && \
     curl -sf "${BASE}/health/ready" >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq "${READY_TIMEOUT}" ]; then
    echo "[smoke] health checks failed after ${READY_TIMEOUT}s" >&2
    exit 7
  fi
  sleep 1
done
sleep "${SMOKE_SETTLE:-3}"

echo "SMOKE OK"

