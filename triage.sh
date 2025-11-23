#!/bin/bash
# 极短·启发式 Cursor Prompt（粘贴就跑，生成一次性体检包）
# Goal: 快速排查谁在烧 CPU/内存/磁盘；不杀进程，只采样并落盘

cd ~/searchforge 2>/dev/null || cd ~

TS=$(date +%F_%H%M%S); OUT=".runs/triage/$TS"; mkdir -p "$OUT"

{
  echo "# TRIAGE $TS"
  date
  uname -a
  echo

  echo "== UPTIME / MEM / DISK =="
  uptime
  free -h
  df -h /

  echo
  echo "== TOP CPU =="
  ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 12

  echo
  echo "== TOP MEM =="
  ps -eo pid,comm,%mem,%cpu --sort=-%mem | head -n 12

  echo
  echo "== GPU (if any) =="
  nvidia-smi --query-gpu=name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "nvidia-smi N/A"

  echo
  echo "== DOCKER PS =="
  docker ps --format 'table {{.Names}}\t{{.State}}\t{{.Status}}\t{{.Image}}'

  echo
  echo "== DOCKER TOP (CPU/MEM) =="
  docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | head -n 10

  echo
  echo "== COMPOSE (if in repo) =="
  (cd ~/searchforge 2>/dev/null && docker compose ps) || true

} | tee "$OUT/summary.txt"

# 常见容器日志（若存在则抓尾巴）
for n in rag-api retrieval-proxy qdrant milvus; do
  docker ps --format '{{.Names}}' | grep -qx "$n" && docker logs --tail 200 "$n" > "$OUT/${n}.log" 2>&1 || true
done

echo "Saved triage to: $OUT"

