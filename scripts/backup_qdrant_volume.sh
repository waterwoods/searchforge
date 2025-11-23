#!/usr/bin/env bash

set -euo pipefail

VOL_NAME="${1:-searchforge_qdrant_data}"

OUT_DIR=".backups"

TS="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$OUT_DIR"

echo "[backup] Checking volume: $VOL_NAME"

if ! docker volume inspect "$VOL_NAME" >/dev/null 2>&1; then
  echo "[backup] Volume not found, skip."
  exit 0
fi

TAR="$OUT_DIR/qdrant_volume_${VOL_NAME}_${TS}.tar.gz"

echo "[backup] Creating snapshot -> $TAR"

docker run --rm -v "$VOL_NAME":/from -v "$(pwd)/$OUT_DIR":/to alpine \
  sh -c "cd /from && tar -czf /to/$(basename "$TAR") ."

echo "[backup] Done."



