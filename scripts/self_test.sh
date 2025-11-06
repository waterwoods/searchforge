#!/usr/bin/env bash
set -euo pipefail

# MAIN_PORT configuration (default: 8011)
MAIN_PORT="${MAIN_PORT:-8011}"
BASE="${BASE:-http://localhost:${MAIN_PORT}}"

# Configuration
CURL_TIMEOUT=5

# Dependency checks
command -v jq >/dev/null || { echo "❌ 错误: 请先安装 jq (e.g., brew install jq 或 apt-get install jq)"; exit 1; }
command -v curl >/dev/null || { echo "❌ 错误: 请先安装 curl"; exit 1; }

printf "### 1) 启动服务提醒 ###\n"
echo "确保 Qdrant(6333/6334) 与后端(${MAIN_PORT}) 已启动。BASE=${BASE}"
sleep 1

printf "\n### 2) 健康检查 ###\n"
HC="$(curl -sSf --max-time ${CURL_TIMEOUT} "${BASE}/api/health/qdrant" | jq '.')"
echo "${HC}" | jq -e '.http_ok==true and .grpc_ok==true' >/dev/null \
  || { echo "❌ 健康检查失败"; echo "${HC}" | jq '.'; exit 1; }
echo "✅ 健康检查通过"

printf "\n### 3) /api/query 适配器验证 ###\n"
QRES="$(curl -sSf --max-time ${CURL_TIMEOUT} -X POST "${BASE}/api/query" \
  -H 'Content-Type: application/json' \
  -d '{"question":"what is ETF?","top_k":5}')"
echo "${QRES}" | jq '.'
echo "${QRES}" | jq -e 'has("trace_id") and has("sources") and has("metrics") and has("reranker_triggered")' >/dev/null \
  || { echo "❌ /api/query 字段不完整"; exit 1; }
echo "✅ /api/query 字段校验通过"

printf "\n### 4) /api/best 写入(步骤A: 初始写入) ###\n"
B1="$(curl -sSf --max-time ${CURL_TIMEOUT} -X PUT "${BASE}/api/best" \
  -H 'Content-Type: application/json' \
  -d '{"pipeline":{"hybrid":true}, "metrics":{"recall_at_10":0.75}}')"
echo "${B1}" | jq '.'
echo "${B1}" | jq -e '.pipeline.hybrid==true and .metrics.recall_at_10==0.75' >/dev/null \
  || { echo "❌ 初始 PUT 合并失败"; exit 1; }
echo "✅ 初始写入校验通过"
echo "(预期：reports/_latest/best.yaml 应包含 pipeline.hybrid 与 metrics.recall_at_10)"

printf "\n### 5) /api/best 验证(步骤B: 深合并) ###\n"
B2="$(curl -sSf --max-time ${CURL_TIMEOUT} -X PUT "${BASE}/api/best" \
  -H 'Content-Type: application/json' \
  -d '{"metrics":{"p95_ms":3.1}}')"
echo "${B2}" | jq '.'
echo "${B2}" | jq -e '.pipeline.hybrid==true and .metrics.recall_at_10==0.75 and .metrics.p95_ms==3.1' >/dev/null \
  || { echo "❌ 深合并未保留既有字段"; exit 1; }
echo "✅ 深合并校验通过"
echo "(预期：reports/_latest/best.yaml 同时包含 hybrid、recall_at_10 与 p95_ms)"

printf "\n### 6) /api/best 读取(步骤C) ###\n"
curl -sSf --max-time ${CURL_TIMEOUT} "${BASE}/api/best" | jq '.'

printf "\n"
printf "\033[32m🎉 ALL CHECKS PASSED!\033[0m\n"

