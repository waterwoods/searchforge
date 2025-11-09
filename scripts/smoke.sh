#!/usr/bin/env bash
# smoke.sh - 提交最小实验并验证指标
# 【守门人】默认走快路：sample=30, fast_mode=true, rerank=false

set -euo pipefail

# 守门人：检查 FULL 或 PROD 模式标记
if [ "${FULL:-0}" = "1" ] || [ "${PROD:-0}" = "1" ]; then
    echo ""
    echo "🔴 警告：FULL=1 或 PROD=1 已设置，将运行完整/生产模式！"
    echo "   如需快速开发，请移除该环境变量。"
    echo ""
    sleep 2
fi

API_BASE="${API_BASE:-http://localhost:8000}"
MAX_POLL="${MAX_POLL:-120}"
POLL_INTERVAL="${POLL_INTERVAL:-3}"

echo "🧪 Smoke Test - 最小实验闭环"
echo "   API Base: $API_BASE"
echo ""

# 1. 提交实验
echo "📤 Step 1: 提交实验 (sample=30, top_k=10, fast_mode=true, rerank=false)..."
submit_response=$(curl -fsS -X POST "$API_BASE/api/experiment/run" \
  -H 'content-type: application/json' \
  -d '{
    "sample": 30,
    "top_k": 10,
    "fast_mode": true,
    "rerank": false,
    "repeats": 1,
    "dataset_name": "fiqa_10k_v1",
    "qrels_name": "fiqa_qrels_10k_v1"
  }' 2>/dev/null)

echo "$submit_response" | python3 -m json.tool

job_id=$(echo "$submit_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo ""
echo "✅ Job submitted: $job_id"
echo ""

# 2. 轮询直到完成
echo "⏳ Step 2: 轮询状态直到完成 (最多 ${MAX_POLL}次)..."
for i in $(seq 1 "$MAX_POLL"); do
    sleep "$POLL_INTERVAL"
    status_response=$(curl -fsS "$API_BASE/api/experiment/status/$job_id" 2>/dev/null)
    status=$(echo "$status_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job', {}).get('status', 'UNKNOWN'))" 2>/dev/null)
    
    echo "   [$i/$MAX_POLL] Status: $status"
    
    if [ "$status" = "SUCCEEDED" ]; then
        echo ""
        echo "✅ Job completed successfully!"
        break
    elif [ "$status" = "FAILED" ]; then
        echo ""
        echo "❌ Job failed!"
        echo "$status_response" | python3 -m json.tool
        exit 1
    fi
    
    if [ "$i" -eq "$MAX_POLL" ]; then
        echo ""
        echo "❌ Timeout waiting for job completion"
        exit 1
    fi
done

# 3. 验证 metrics.json
echo ""
echo "🔍 Step 3: 验证 metrics.json..."
echo ""

# 通过 Docker 读取容器内的 metrics.json
metrics_json=$(docker compose -f /home/andy/searchforge/docker-compose.yml -f /home/andy/searchforge/docker-compose.dev.yml exec -T rag-api cat "/app/.runs/$job_id/metrics.json" 2>/dev/null || echo '{}')

if [ "$metrics_json" = "{}" ]; then
    echo "❌ metrics.json not found or empty"
    exit 1
fi

echo "📊 metrics.json 内容："
echo "$metrics_json" | python3 -m json.tool

# 4. 校验关键指标
echo ""
echo "✔️  Step 4: 校验关键指标..."

source_check=$(echo "$metrics_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('source', '') == 'runner')" 2>/dev/null)
recall_at_10=$(echo "$metrics_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('metrics', {}).get('recall_at_10', 0))" 2>/dev/null)
p95_ms=$(echo "$metrics_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('metrics', {}).get('p95_ms', 0))" 2>/dev/null)

echo "   source='runner': $source_check"
echo "   recall_at_10: $recall_at_10"
echo "   p95_ms: $p95_ms"
echo ""

# 验证逻辑
if [ "$source_check" != "True" ]; then
    echo "❌ source != 'runner'"
    exit 1
fi

recall_valid=$(python3 -c "print($recall_at_10 > 0)" 2>/dev/null)
p95_valid=$(python3 -c "print($p95_ms > 0)" 2>/dev/null)

if [ "$recall_valid" != "True" ] || [ "$p95_valid" != "True" ]; then
    echo "❌ 指标验证失败 (recall_at_10 或 p95_ms <= 0)"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 烟测通过！"
echo ""
echo "📋 Summary:"
echo "   Job ID: $job_id"
echo "   recall_at_10: $recall_at_10"
echo "   p95_ms: $p95_ms"
echo "   source: runner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
