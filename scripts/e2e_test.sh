#!/bin/bash
# === One-Click E2E: sync → rebuild → health → run 2 jobs → verify metrics → collect winners ===

set -euo pipefail

# ---- 0) 基本变量（按需改） ----

LOCAL="${LOCAL:-$PWD}"
REMOTE="${REMOTE:-andy-wsl}"
RBASE="${RBASE:-~/searchforge}"
API_BASE="${API_BASE:-http://andy-wsl:8000}"
DATASET="${DATASET:-fiqa_10k_v1}"     # 先用 10k 跑得快；改成 fiqa_50k_v1 也可
QRELS="${QRELS:-fiqa_qrels_10k_v1}"
TOPK1="${TOPK1:-10}"
TOPK2="${TOPK2:-20}"

die(){ echo -e "\n❌ $*\n"; exit 1; }
say(){ echo -e "\n➡ $*\n"; }

# ---- 1) 同步必要文件到远端（最小覆盖面）----

say "1) rsync 关键目录到 $REMOTE:$RBASE"
rsync -avz --exclude '.git' --exclude 'node_modules' \
  "$LOCAL/experiments/" "$REMOTE:$RBASE/experiments/"
rsync -avz --exclude '.git' --exclude 'node_modules' \
  "$LOCAL/services/fiqa_api/" "$REMOTE:$RBASE/services/fiqa_api/"
rsync -avz "$LOCAL/services/rag_api/Dockerfile" "$REMOTE:$RBASE/services/rag_api/Dockerfile"
rsync -avz --exclude '.git' --exclude 'node_modules' \
  "$LOCAL/scripts/" "$REMOTE:$RBASE/scripts/"
rsync -avz --exclude '.git' --exclude 'node_modules' \
  "$LOCAL/configs/" "$REMOTE:$RBASE/configs/"
rsync -avz --exclude '.git' --exclude 'node_modules' \
  "$LOCAL/tools/" "$REMOTE:$RBASE/tools/"
rsync -avz "$LOCAL/Makefile" "$REMOTE:$RBASE/Makefile"
rsync -avz "$LOCAL/docker-compose.yml" "$REMOTE:$RBASE/docker-compose.yml"

# ---- 2) 重建 & 启动 ----

say "2) 远端重建 rag-api（no-cache）并启动"
ssh "$REMOTE" "cd $RBASE && docker compose build --no-cache rag-api && docker compose up -d rag-api" || die "容器构建/启动失败"

# ---- 3) 健康体检（无 CUDA、嵌入模型一致、单 worker）----

say "3) 健康体检：guard-no-cuda / embed-doctor / 单 worker 校验"
ssh "$REMOTE" "cd $RBASE && (make guard-no-cuda || true) && (make embed-doctor || true)"
ssh "$REMOTE" "cd $RBASE && docker compose exec -T rag-api sh -lc 'ps aux | grep -i \"uvicorn .*app_main\" | grep -v grep; ss -lntp 2>/dev/null || netstat -lntp 2>/dev/null'"

# API 健康检查
say "   调用 /api/health/embeddings"
curl -fsS "$API_BASE/api/health/embeddings" || die "健康检查失败"

# ---- 4) 提交两单最小实验（baseline_k10 & fast_k20）----

say "4) 提交两单最小实验（baseline_k${TOPK1}, fast_k${TOPK2}）"
J1="$(curl -fsS -H 'content-type: application/json' \
  -d "{\"sample\":50,\"repeats\":1,\"fast_mode\":false,\"top_k\":$TOPK1,\"dataset_name\":\"$DATASET\",\"qrels_name\":\"$QRELS\"}" \
  "$API_BASE/api/experiment/run" | python3 -c 'import sys,json;print(json.load(sys.stdin)["job_id"])')"
echo "baseline_k$TOPK1 → JOB=$J1"

J2="$(curl -fsS -H 'content-type: application/json' \
  -d "{\"sample\":50,\"repeats\":1,\"fast_mode\":true,\"top_k\":$TOPK2,\"dataset_name\":\"$DATASET\",\"qrels_name\":\"$QRELS\"}" \
  "$API_BASE/api/experiment/run" | python3 -c 'import sys,json;print(json.load(sys.stdin)["job_id"])')"
echo "fast_k$TOPK2 → JOB=$J2"

# ---- 5) 轮询状态（最多 5 分钟）----

poll_job(){ 
  local id="$1"; 
  for i in $(seq 1 150); do
    S="$(curl -fsS "$API_BASE/api/experiment/status/$id" | python3 -c 'import sys,json;d=json.load(sys.stdin);print((d.get("job") or {}).get("status","unknown"))')"
    echo "[$i] JOB $id status = $S"
    test "$S" = "SUCCEEDED" && return 0
    test "$S" = "FAILED" && return 2
    sleep 2
  done
  return 3
}

say "5) 轮询 JOB 状态…"
poll_job "$J1" || die "JOB $J1 未成功（失败或超时）"
poll_job "$J2" || die "JOB $J2 未成功（失败或超时）"

# ---- 6) 校验 metrics.json 落盘 + 详情回填 ----

verify_metrics(){
  local id="$1"
  say "   校验 $id: 容器内 metrics.json 与 API 回填"
  ssh "$REMOTE" "cd $RBASE && docker compose exec -T rag-api sh -lc 'ls -la /app/.runs/$id || true; test -s /app/.runs/$id/metrics.json && head -c 500 /app/.runs/$id/metrics.json || (echo NO_METRICS && false)'" \
    || die "容器内 /app/.runs/$id/metrics.json 缺失"
  curl -fsS "$API_BASE/api/experiment/detail/$id" | python3 - <<'PY' || exit 1
import sys,json
d=json.load(sys.stdin)
m=d.get("metrics") or {}
need=["recall_at_10","p95_ms","qps"]
miss=[k for k in need if k not in (m.get("overall") or {}) and k not in m]
if miss: 
  print("API metrics 回填缺失字段：",miss); 
  sys.exit(2)
print("API metrics ok:", json.dumps(m)[:300], "…")
PY
}

say "6) 校验 metrics.json & 详情回填"
verify_metrics "$J1"
verify_metrics "$J2"

# ---- 7) 汇总 winners.json ----

say "7) 生成 winners.json"
ssh "$REMOTE" "cd $RBASE && docker compose exec -T rag-api sh -lc 'cd /app && python3 scripts/collect_metrics.py --runs-dir /app/.runs --out /app/reports/winners.json && test -s /app/reports/winners.json && head -c 800 /app/reports/winners.json'" \
  || die "winners.json 生成失败"

# ---- 8) 最后打印摘要 & 提示 ----

say "✅ 完成！摘要："
echo "API_BASE = $API_BASE"
echo "JOBS      = $J1  ,  $J2"
echo "winners   = ssh $REMOTE 'cat $RBASE/reports/winners.json | python3 -m json.tool | head -n 80'"

echo -e "\n接下来：\n- 前端 Job History 刷新应可见这两单；\n- 若想跑 50k，把 DATASET/QRELS 改为 fiqa_50k_v1/fiqa_qrels_50k_v1；\n- 批量实验可运行 scripts/run_phase_a_experiments.sh（若已存在）。\n"

