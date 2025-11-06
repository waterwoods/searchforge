#!/usr/bin/env bash
set -euo pipefail

echo "== Docker space report =="

command -v docker >/dev/null || { echo "docker not found"; exit 1; }

echo "-- docker system df --"
docker system df

echo

echo "-- dangling images --"
docker images -f dangling=true --format '{{.ID}} {{.Repository}}:{{.Tag}}' || true

echo

echo "-- stopped containers --"
docker ps -a -f status=exited --format '{{.ID}} {{.Names}}' || true

echo

KEEP_VOLUMES_REGEX=${KEEP_VOLUMES_REGEX:-"(qdrant|milvus|minio|redis|postgres)"}
echo "-- dangling volumes (will keep: ${KEEP_VOLUMES_REGEX}) --"
docker volume ls -qf dangling=true | grep -Ev "${KEEP_VOLUMES_REGEX}" || true

echo

echo "-- builder cache --"
docker buildx du 2>/dev/null || docker system df | grep -i "build" || echo "buildx not available"

echo

echo "-- filesystem usage --"
df -h | head -n 20

