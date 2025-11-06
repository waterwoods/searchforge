#!/usr/bin/env bash

set -euo pipefail

REMOTE=${REMOTE:-andy-wsl}
COMPOSE_DIR=${COMPOSE_DIR:-~/searchforge}
TAILSCALE_IP=${TAILSCALE_IP:-100.67.88.114}

pass=0
warn=0
fail=0

ok() {
  echo "✔ $1"
  pass=$((pass + 1))
}

wr() {
  echo "⚠ $1"
  warn=$((warn + 1))
}

ng() {
  echo "✖ $1"
  fail=$((fail + 1))
}

run() {
  ssh -o BatchMode=yes -o ConnectTimeout=2 "$REMOTE" "bash -lc '$1'"
}

# 1 SSH
if run 'hostname && uptime' >/dev/null 2>&1; then
  ok "SSH reachable"
else
  ng "SSH not reachable"
fi

# 2 Docker
if run 'docker info --format "{{.ServerVersion}}"' >/dev/null 2>&1; then
  ok "Docker reachable"
else
  ng "Docker not reachable"
fi

# 3 Compose 目录
# Construct command with printf to avoid local variable expansion
COMPOSE_DIR_CMD=$(printf "test -d %s" "$COMPOSE_DIR")
if run "$COMPOSE_DIR_CMD" >/dev/null 2>&1; then
  ok "Compose dir exists"
else
  ng "Compose dir missing: $COMPOSE_DIR"
fi

# 4 关键容器状态
COMPOSE_PS_CMD=$(printf "cd %s && docker compose ps" "$COMPOSE_DIR")
if run "$COMPOSE_PS_CMD" >/dev/null 2>&1; then
  ok "compose ps ok"
else
  ng "compose ps failed"
fi

# 5 API /health
if run 'curl -fsS --max-time 2 http://localhost:8000/health' >/dev/null 2>&1; then
  ok "rag-api /health ok"
else
  ng "rag-api /health fail"
fi

# 6 Qdrant /collections
if run 'curl -fsS --max-time 2 http://localhost:6333/collections | head -c 80' >/dev/null 2>&1; then
  ok "qdrant /collections ok"
else
  ng "qdrant /collections fail"
fi

# 7 卷在 ext4
# Check /var/lib/docker (volumes subdir may have permission issues)
# Use double quotes for awk to avoid quote nesting issues
if run "df -T /var/lib/docker 2>/dev/null | awk \"NR==2{print \\\$2}\" | grep -q ext4" >/dev/null 2>&1; then
  ok "volumes on ext4"
else
  ng "volumes NOT on ext4"
fi

# 8 Dozzle 仅本地绑定（警告项）
if run "docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null | grep -E 'dozzle' | grep -q '127.0.0.1'" >/dev/null 2>&1; then
  ok "Dozzle bound 127.0.0.1"
else
  wr "Dozzle not bound to 127.0.0.1"
fi

# 9 GPU 可用（警告项）
if run 'docker run --rm --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi -L' >/dev/null 2>&1; then
  ok "GPU visible"
else
  wr "GPU not detected (ok if not needed)"
fi

# 10 Portainer 9443（从 Mac 测）
if curl -kIs --connect-timeout 2 --max-time 2 "https://${TAILSCALE_IP}:9443/" >/dev/null 2>&1; then
  ok "Portainer 9443 reachable"
else
  wr "Portainer 9443 not reachable"
fi

# 11 停止本地项目容器（保留数据卷）
if docker compose down >/dev/null 2>&1; then
  ok "Local containers stopped"
else
  ng "Failed to stop local containers"
fi

# 12 验收：端口不再被占用（应为 0）
PORT_COUNT=$(lsof -i :8000 -i :6333 2>/dev/null | wc -l | tr -d ' ')
if [ "$PORT_COUNT" -eq 0 ]; then
  ok "Ports 8000, 6333 not in use locally"
else
  wr "Ports 8000, 6333 still in use locally ($PORT_COUNT processes)"
fi

# 13 确认都在打远端（使用 IP 地址，因为 curl 不读 SSH config）
if curl -fsS --max-time 2 "http://${TAILSCALE_IP}:8000/health" >/dev/null 2>&1; then
  ok "Remote rag-api /health reachable"
else
  ng "Remote rag-api /health not reachable"
fi

if curl -fsS --max-time 2 "http://${TAILSCALE_IP}:6333/collections" 2>/dev/null | head -c 120 >/dev/null 2>&1; then
  ok "Remote qdrant /collections reachable"
else
  ng "Remote qdrant /collections not reachable"
fi

echo "----- SUMMARY -----"
echo "PASS=$pass WARN=$warn FAIL=$fail"

if [ $fail -gt 0 ]; then
  exit 1
fi
