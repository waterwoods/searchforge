#!/usr/bin/env bash

set -euo pipefail

LOG_FILE="${LOG_FILE:-.runs/build.log}"
mkdir -p .runs

SCRIPT_TS="${SCRIPT_TS:-$(date -Iseconds)}"
echo "[${SCRIPT_TS}] fallback builder start svc=${1:-rag-api}" | tee -a "$LOG_FILE"

ENV_FILE="${ENV_FILE:-.env.current}"
GIT_SHA="${GIT_SHA:-$(git rev-parse --short HEAD)}"
SERVICE="${1:-rag-api}"

run_buildkit() {
  local output
  set +e
  output=$(DOCKER_BUILDKIT=1 docker compose --env-file "$ENV_FILE" build --build-arg GIT_SHA="$GIT_SHA" --no-cache --pull=false "$@" 2>&1)
  local code=$?
  set -e
  echo "$output" | tee -a "$LOG_FILE"
  echo "$output"
  return $code
}

run_classic() {
  local output
  set +e
  output=$(DOCKER_BUILDKIT=0 docker compose --env-file "$ENV_FILE" build --build-arg GIT_SHA="$GIT_SHA" --no-cache --pull=false "$@" 2>&1)
  local code=$?
  set -e
  echo "$output" | tee -a "$LOG_FILE"
  echo "$output"
  return $code
}

is_registry_error() {
  local text="$1"
  # match typical BuildKit/Hub DNS/manifest timeouts
  if [[ "${SIMULATE_REGISTRY_TIMEOUT:-0}" == "1" ]]; then
    return 0
  fi
  echo "$text" | grep -E "registry-1\.docker\.io|lookup.*i/o timeout|manifest.*denied|net/http" -qi
}

echo "[build] try BuildKit=1 for service=$SERVICE GIT_SHA=$GIT_SHA" | tee -a "$LOG_FILE"
set +e
out=$(run_buildkit "$SERVICE")
code=$?
set -e

if [[ "${FORCE_CLASSIC:-0}" == "1" ]] || ( [[ "$code" -ne 0 ]] && is_registry_error "$out" ); then
  echo "[WARN] buildkit failed, fallback classic…" | tee -a "$LOG_FILE"
  run_classic "$SERVICE"
else
  if [[ "$code" -eq 0 ]]; then
    echo "[OK] buildkit" | tee -a "$LOG_FILE"
  else
    echo "[ERROR] buildkit failed with non-registry error" | tee -a "$LOG_FILE"
    exit "$code"
  fi
fi

echo "[DONE] fallback builder svc=$SERVICE GIT_SHA=$GIT_SHA" | tee -a "$LOG_FILE"
