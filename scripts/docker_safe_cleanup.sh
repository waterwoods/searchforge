#!/usr/bin/env bash
set -euo pipefail

DRY="${1:-}"   # pass --dry-run to preview
run() { if [[ "$DRY" == "--dry-run" ]]; then echo "DRY: $*"; else eval "$@"; fi }

echo "== BEFORE =="
docker system df

echo ""
echo "== Active containers =="
docker ps --format '  - {{.Names}} ({{.ID}})'

echo ""
echo "== Volumes currently in use by any container =="
docker ps -aq | xargs -I{} docker inspect {} --format '{{ .Name }} -> {{ range .Mounts }}{{ if .Name }}{{ .Name }} {{ end }}{{ end }}' | sed '/->\s*$/d' || true

echo ""
echo "== Step 1: prune build cache (safe) =="
run "docker builder prune -af"

echo ""
echo "== Step 2: remove dangling/unused images (safe) =="
# 仅删除"未被任何容器引用"的镜像
run "docker image prune -af"

echo ""
echo "== Step 3: remove stopped containers (safe) =="
run "docker container prune -f"

echo ""
echo "== Step 4: remove unused networks (safe) =="
run "docker network prune -f"

echo ""
echo "== Step 5: remove unused volumes (safe) =="
# 只会删除"不被任何容器引用"的卷；运行中的 qdrant/redis 所用卷不会被删
run "docker volume prune -f"

echo ""
echo "== AFTER =="
docker system df

echo ""
echo "✅ Done. 如果需要预演：scripts/docker_safe_cleanup.sh --dry-run"

# End of file

