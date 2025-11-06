#!/bin/bash
# ==== config ====
EXP=monitor_demo
API=http://127.0.0.1:8011

echo "1) 后端健康检查"; curl -s $API/readyz | jq . || exit 1

echo "2) 造数 60s 到 EXP=$EXP (高QPS模式)"
for i in $(seq 1 600); do
  curl -s -X POST "$API/search" \
    -H 'Content-Type: application/json' \
    -H "X-Lab-Exp: $EXP" -H "X-Lab-Phase: A" -H "X-TopK: 10" \
    -d '{"query":"hello","top_k":10}' >/dev/null &
  sleep 0.1
done
wait

echo "3) 查看 Redis（DB0）是否有写入"
redis-cli -n 0 llen lab:exp:$EXP:raw
echo "最近1条："; redis-cli -n 0 lrange lab:exp:$EXP:raw -1 -1 | jq -r '.[0]' | jq .

echo "4) 调 metrics 接口（同 EXP）"
curl -s "$API/api/metrics/mini?exp_id=$EXP&window_sec=180" | jq .

echo "== 提示 =="
echo "浏览器打开 http://localhost:3000/monitor"
echo "把 Experiment 从 auto 切到 manual，并输入：$EXP"
echo "点 Refresh All（或等 3 秒自动刷新）"

