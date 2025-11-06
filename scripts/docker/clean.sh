#!/usr/bin/env bash
set -euo pipefail

RUN=${RUN:-0}
AGE_HOURS=${AGE_HOURS:-240}
KEEP_VOLUMES_REGEX=${KEEP_VOLUMES_REGEX:-"(qdrant|milvus|minio|redis|postgres)"}
PRUNE_BUILDX=${PRUNE_BUILDX:-1}

command -v docker >/dev/null || { echo "docker not found"; exit 1; }

action() {
  if [[ "${RUN}" = "1" ]]; then
    eval "$1"
  else
    echo "[dry-run] $1"
  fi
}

echo "== BEFORE =="
docker system df || true
echo

echo "Age filter: ${AGE_HOURS}h  | Keep volumes matching: ${KEEP_VOLUMES_REGEX}  | Dry-run: $([[ ${RUN} = 1 ]] && echo no || echo yes)"

echo "-- prune stopped containers --"
action "docker container prune -f --filter \"until=${AGE_HOURS}h\""

echo "-- prune dangling/old images --"
action "docker image prune -a -f --filter \"until=${AGE_HOURS}h\""

echo "-- prune unused networks --"
action "docker network prune -f --filter \"until=${AGE_HOURS}h\""

if [[ "${PRUNE_BUILDX}" = "1" ]]; then
  echo "-- prune builder cache --"
  action "docker builder prune -a -f --filter \"until=${AGE_HOURS}h\""
fi

echo "-- prune dangling volumes (excluding KEEP_VOLUMES_REGEX) --"
TO_DEL=$(docker volume ls -qf dangling=true 2>/dev/null | grep -Ev "${KEEP_VOLUMES_REGEX}" | grep -v '^$' || true)
if [[ -n "${TO_DEL}" ]]; then
  while read -r v; do
    [[ -n "${v}" ]] && action "docker volume rm \"${v}\""
  done <<< "${TO_DEL}"
else
  echo "no prunable volumes"
fi

echo
echo "== AFTER =="
docker system df || true
echo "Tip: run with RUN=1 to actually delete. Example: RUN=1 AGE_HOURS=72 make docker-clean"

