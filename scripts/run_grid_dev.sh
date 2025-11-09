#!/usr/bin/env bash
# run_grid_dev.sh - 并行提交小批量实验（2-3 并行槽）
# 【守门人】默认走快路：sample=30, top_k∈{10,20,30}, fast_mode=true

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
PARALLEL="${PARALLEL:-2}"
MAX_POLL="${MAX_POLL:-180}"
POLL_INTERVAL="${POLL_INTERVAL:-5}"

echo "🔬 Grid Dev - 并行小批实验"
echo "   API Base: $API_BASE"
echo "   Parallel Slots: $PARALLEL"
echo ""

# 定义实验配置（top_k ∈ {10,20,30}）
declare -a experiments=(
  "10:exp1"
  "20:exp2"
  "30:exp3"
)

# 存储 job IDs
declare -a job_ids=()

# 1. 并行提交实验
echo "📤 Step 1: 并行提交 ${#experiments[@]} 个实验..."
for exp in "${experiments[@]}"; do
    top_k="${exp%%:*}"
    name="${exp##*:}"
    
    echo "   提交实验 $name (top_k=$top_k)..."
    
    response=$(curl -fsS -X POST "$API_BASE/api/experiment/run" \
      -H 'content-type: application/json' \
      -d "{
        \"sample\": 30,
        \"top_k\": $top_k,
        \"fast_mode\": true,
        \"rerank\": false,
        \"repeats\": 1,
        \"dataset_name\": \"fiqa_10k_v1\",
        \"qrels_name\": \"fiqa_qrels_10k_v1\"
      }" 2>/dev/null)
    
    job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
    job_ids+=("$job_id:$top_k:$name")
    echo "     ✓ $name submitted: $job_id"
    
    # 简单的并行控制：每提交 $PARALLEL 个，等待一下
    if [ "${#job_ids[@]}" -ge "$PARALLEL" ]; then
        sleep 2
    fi
done

echo ""
echo "✅ 所有实验已提交: ${#job_ids[@]} 个"
echo ""

# 2. 轮询所有作业直到完成
echo "⏳ Step 2: 轮询所有作业直到完成..."
declare -A job_status
for job_entry in "${job_ids[@]}"; do
    job_id="${job_entry%%:*}"
    job_status[$job_id]="RUNNING"
done

for i in $(seq 1 "$MAX_POLL"); do
    sleep "$POLL_INTERVAL"
    
    all_done=true
    for job_entry in "${job_ids[@]}"; do
        job_id="${job_entry%%:*}"
        
        # 跳过已完成的作业
        if [[ "${job_status[$job_id]}" == "SUCCEEDED" ]] || [[ "${job_status[$job_id]}" == "FAILED" ]]; then
            continue
        fi
        
        status_response=$(curl -fsS "$API_BASE/api/experiment/status/$job_id" 2>/dev/null)
        status=$(echo "$status_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job', {}).get('status', 'UNKNOWN'))" 2>/dev/null)
        
        job_status[$job_id]=$status
        
        if [[ "$status" != "SUCCEEDED" ]] && [[ "$status" != "FAILED" ]]; then
            all_done=false
        fi
    done
    
    # 显示当前状态
    echo "   [$i/$MAX_POLL] Status:"
    for job_entry in "${job_ids[@]}"; do
        job_id="${job_entry%%:*}"
        remaining="${job_entry#*:}"
        top_k="${remaining%%:*}"
        name="${remaining##*:}"
        echo "     $name (top_k=$top_k): ${job_status[$job_id]}"
    done
    
    if [ "$all_done" = true ]; then
        echo ""
        echo "✅ 所有作业完成！"
        break
    fi
    
    if [ "$i" -eq "$MAX_POLL" ]; then
        echo ""
        echo "❌ 超时：部分作业未完成"
        exit 1
    fi
done

echo ""

# 3. 收集结果并生成 winners_dev.json
echo "📊 Step 3: 收集结果并生成胜者报告..."
mkdir -p reports

results="[]"
for job_entry in "${job_ids[@]}"; do
    job_id="${job_entry%%:*}"
    remaining="${job_entry#*:}"
    top_k="${remaining%%:*}"
    name="${remaining##*:}"
    
    status="${job_status[$job_id]}"
    
    if [ "$status" = "SUCCEEDED" ]; then
        # 读取 metrics.json
        metrics_json=$(docker compose -f /home/andy/searchforge/docker-compose.yml -f /home/andy/searchforge/docker-compose.dev.yml exec -T rag-api cat "/app/.runs/$job_id/metrics.json" 2>/dev/null || echo '{}')
        
        recall=$(echo "$metrics_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('metrics', {}).get('recall_at_10', 0))" 2>/dev/null)
        p95=$(echo "$metrics_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('metrics', {}).get('p95_ms', 0))" 2>/dev/null)
        
        echo "   $name: recall@10=$recall, p95_ms=$p95"
        
        # 追加到结果
        new_result=$(python3 -c "import json; print(json.dumps({'job_id': '$job_id', 'name': '$name', 'top_k': $top_k, 'recall_at_10': $recall, 'p95_ms': $p95}))")
        results=$(echo "$results" | python3 -c "import sys, json; d=json.load(sys.stdin); d.append($new_result); print(json.dumps(d))")
    else
        echo "   $name: FAILED"
    fi
done

# 找到最佳配置（最高 recall@10）
winner=$(echo "$results" | python3 -c "
import sys, json
results = json.load(sys.stdin)
if results:
    winner = max(results, key=lambda x: x.get('recall_at_10', 0))
    print(json.dumps(winner, indent=2))
else:
    print(json.dumps({'error': 'no_results'}, indent=2))
")

echo ""
echo "🏆 胜者配置："
echo "$winner"

# 保存完整报告
report=$(python3 -c "
import json
report = {
    'experiments': $results,
    'winner': $winner,
    'ts': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
}
print(json.dumps(report, indent=2))
")

echo "$report" > reports/winners_dev.json
echo ""
echo "✅ 报告已保存到 reports/winners_dev.json"

