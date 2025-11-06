#!/bin/bash
# ==== 高QPS配置 ====
EXP=monitor_demo
API=http://127.0.0.1:8011
QPS_TARGET=20  # 目标QPS
DURATION=60    # 持续时间（秒）- 改为1分钟

echo "🚀 启动高QPS测试: 目标${QPS_TARGET} QPS, 持续${DURATION}秒"

echo "1) 后端健康检查"
curl -s $API/readyz | jq . || exit 1

echo "2) 生成高QPS流量..."
TOTAL_REQUESTS=$((QPS_TARGET * DURATION))
INTERVAL=$(echo "scale=3; 1/$QPS_TARGET" | bc)

echo "   总请求数: $TOTAL_REQUESTS"
echo "   请求间隔: ${INTERVAL}秒"
echo "   预计QPS: $QPS_TARGET"

for i in $(seq 1 $TOTAL_REQUESTS); do
  curl -s -X POST "$API/search" \
    -H 'Content-Type: application/json' \
    -H "X-Lab-Exp: $EXP" -H "X-Lab-Phase: A" -H "X-TopK: 10" \
    -d '{"query":"hello","top_k":10}' >/dev/null &
  
  if (( i % 50 == 0 )); then
    echo "   已发送 $i/$TOTAL_REQUESTS 请求"
  fi
  
  sleep $INTERVAL
done

echo "3) 等待所有请求完成..."
wait

echo "4) 查看结果"
echo "Redis数据量:"
redis-cli -n 0 llen lab:exp:$EXP:raw

echo "最新指标:"
curl -s "$API/api/metrics/mini?exp_id=$EXP&window_sec=180" | jq .

echo "✅ 高QPS测试完成！"
