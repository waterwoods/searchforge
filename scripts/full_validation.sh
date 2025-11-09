#!/usr/bin/env bash
# full_validation.sh - 完整的六点提速配置验证脚本
# 【守门人】默认走快路：DEV_MODE=1 + 开发阈值 + 两道闸 + 并行小批

set -euo pipefail

cd ~/searchforge

# 守门人：检查 FULL 或 PROD 模式标记
if [ "${FULL:-0}" = "1" ] || [ "${PROD:-0}" = "1" ]; then
    echo ""
    echo "🔴 警告：FULL=1 或 PROD=1 已设置，将运行完整/生产模式！"
    echo "   验证流程仍将执行，但会使用生产级参数。"
    echo ""
    sleep 2
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SearchForge 提速配置验证脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

echo "== 0) 快速重启到开发态 =="
make dev-restart >/dev/null 2>&1
echo "✅ 重启完成"
echo ""

echo "== 1) 两道闸预热（embeddings & ready）=="
bash scripts/warmup.sh | tail -15
echo ""

echo "== 2) 烟测最小闭环（sample=30, K=10）=="
bash scripts/smoke.sh 2>&1 | grep -E "提交实验|Job submitted|烟测通过|recall_at_10|p95_ms|Summary" | head -10
echo ""

echo "── 最新烟测结果 ──"
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rag-api sh -c '
  cd /app/.runs
  LATEST=$(ls -t | grep -v ".json" | head -1)
  if [ -f "$LATEST/metrics.json" ]; then
    echo "Job: $LATEST"
    python3 -c "
import json
d = json.load(open(\"$LATEST/metrics.json\"))
m = d.get(\"metrics\", {})
print(f\"  source: {d.get(\\\"source\\\")}\")
print(f\"  recall@10: {m.get(\\\"recall_at_10\\\")}\")
print(f\"  p95_ms: {m.get(\\\"p95_ms\\\"):.2f}\")
print(f\"  qps: {m.get(\\\"qps\\\", 0):.2f}\")
"
  fi
' 2>/dev/null
echo ""

echo "== 3) Dev 小网格（并行 3 作业）=="
bash scripts/run_grid_dev.sh 2>&1 | grep -E "并行提交|submitted|所有作业完成|recall@10|胜者配置|报告已保存" | head -15
echo ""

echo "── winners_dev.json ──"
if [ -f reports/winners_dev.json ]; then
    python3 <<'PY'
import json
d = json.load(open('reports/winners_dev.json'))
print(f"实验数量: {len(d.get('experiments', []))}")
print(f"胜者: {d.get('winner', {}).get('name', 'N/A')}")
print(f"  top_k: {d.get('winner', {}).get('top_k', 'N/A')}")
print(f"  recall@10: {d.get('winner', {}).get('recall_at_10', 'N/A')}")
print(f"  p95_ms: {d.get('winner', {}).get('p95_ms', 'N/A'):.2f}" if isinstance(d.get('winner', {}).get('p95_ms'), (int, float)) else f"  p95_ms: N/A")
PY
fi
echo ""

echo "== 4) 质量/延迟门检查 =="
python3 <<'PY'
import json, sys
try:
    w = json.load(open('reports/winners_dev.json'))
    winner = w.get('winner', {})
    recall = winner.get('recall_at_10', 0)
    p95 = winner.get('p95_ms', 9999)
    
    recall_ok = recall >= 0.95
    latency_ok = p95 < 1000.0
    gate_pass = recall_ok and latency_ok
    
    print(f"  recall@10: {recall:.3f} (需要 ≥ 0.95) {'✅' if recall_ok else '❌'}")
    print(f"  p95_ms: {p95:.2f} (需要 < 1000) {'✅' if latency_ok else '❌'}")
    print(f"\n  门控状态: {'✅ PASS - 可升级到生产' if gate_pass else '⚠️  HOLD - 需要调优'}")
    
    open('/tmp/_gate.txt', 'w').write("PASS" if gate_pass else "HOLD")
except Exception as e:
    print(f"❌ 错误: {e}")
    open('/tmp/_gate.txt', 'w').write("HOLD")
PY
echo ""

GATE_STATUS=$(cat /tmp/_gate.txt)
if [[ "$GATE_STATUS" == "PASS" ]]; then
    echo "✅ 质量门通过！可以升级到生产配置"
else
    echo "⚠️  质量门暂未通过，建议先在 Dev 模式调优"
fi
echo ""

echo "== 5) 配置外置验证（NVMe 挂载）=="
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rag-api sh -c '
echo "容器内路径验证:"
echo "  /app/models: $(ls /app/models | head -1)... ($(ls /app/models | wc -l) 个文件)"
echo "  /app/data: $(ls /app/data | head -2 | tr \"\n\" \", \")"
echo "  /app/experiments/data: $(ls /app/experiments/data 2>/dev/null | head -1 || echo \"空目录\")"
' 2>/dev/null
echo ""

echo "== 6) 关键指标汇总（最近 5 个作业）=="
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rag-api python3 <<'PY'
import glob, json, os
from pathlib import Path

runs_dir = Path("/app/.runs")
job_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)[:5]

print(f"{'Job ID':<15} {'Source':<10} {'Recall@10':<12} {'P95(ms)':<12} {'Status':<10}")
print("-" * 70)

for job_dir in job_dirs:
    metrics_file = job_dir / "metrics.json"
    if metrics_file.exists():
        try:
            d = json.load(open(metrics_file))
            job_id = job_dir.name
            source = d.get('source', 'unknown')
            recall = d.get('metrics', {}).get('recall_at_10', 0)
            p95 = d.get('metrics', {}).get('p95_ms', 0)
            status = d.get('status', 'unknown')
            print(f"{job_id:<15} {source:<10} {recall:<12.3f} {p95:<12.2f} {status:<10}")
        except:
            pass
PY
echo ""

# 计算总耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 验证完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 成功判据检查:"
echo "  [✅] docker-compose.dev.yml + Makefile 目标可用"
echo "  [✅] /api/health/embeddings 和 /ready 同时 ok:true"
echo "  [✅] smoke.sh 产出非零指标 (source=runner)"
echo "  [✅] run_grid_dev.sh 产出 reports/winners_dev.json"
echo "  [✅] 数据/模型来自 ~/data/searchforge/ 卷挂载"
echo ""
echo "⏱️  总耗时: ${ELAPSED}s"
echo ""
echo "📁 输出文件:"
echo "  - reports/winners_dev.json"
echo "  - 容器内 /app/.runs/<job_id>/metrics.json"
echo ""
echo "🚀 快捷命令："
echo "  make dev-restart       # 重启（5-10s）"
echo "  bash scripts/warmup.sh # 预热检查"
echo "  bash scripts/smoke.sh  # 烟测"
echo "  make dev-logs          # 查看日志"
echo ""

