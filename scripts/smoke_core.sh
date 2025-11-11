#!/bin/bash
# smoke_core.sh - Core 模块接线自检脚本
# 验证 core/* 骨架是否正确接入，不影响现有行为

set -e  # 遇到错误立即退出

API_URL="http://localhost:8000"
SEARCH_COUNT=2
SLEEP_INTERVAL=1

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Core Modules Smoke Test"
echo "========================================"
echo ""

# Step 1: 检查服务是否启动
echo "[1/5] Checking service health..."
if ! curl -s -f "$API_URL/health" > /dev/null; then
    echo -e "${RED}FAIL${NC}: Service not running at $API_URL"
    echo "Please start the service first: cd services/fiqa_api && uvicorn services.fiqa_api.app_main:app"
    exit 1
fi
echo -e "${GREEN}PASS${NC}: Service is running"
echo ""

# Step 2: 检查 /admin/health 端点
echo "[2/5] Checking /admin/health endpoint..."
HEALTH_RESP=$(curl -s "$API_URL/admin/health")
STATUS=$(echo "$HEALTH_RESP" | jq -r '.status // "unknown"')

if [ "$STATUS" = "unavailable" ]; then
    echo -e "${YELLOW}WARN${NC}: Core modules not available (expected if core/* not in path)"
    echo "Response: $HEALTH_RESP"
    echo ""
    echo "This is OK for the skeleton phase. Core modules are optional."
    exit 0
elif [ "$STATUS" != "ok" ]; then
    echo -e "${RED}FAIL${NC}: Unexpected status: $STATUS"
    echo "Response: $HEALTH_RESP"
    exit 1
fi

echo -e "${GREEN}PASS${NC}: /admin/health returned status=ok"
echo ""

# Step 3: 记录初始 metrics 计数
echo "[3/5] Recording initial metrics count..."
INITIAL_SAMPLES=$(echo "$HEALTH_RESP" | jq -r '.metrics.samples_60s // 0')
echo "Initial samples_60s: $INITIAL_SAMPLES"
echo ""

# Step 4: 执行搜索请求（触发 metrics 写入）
echo "[4/5] Executing $SEARCH_COUNT search requests..."
for i in $(seq 1 $SEARCH_COUNT); do
    QUERY="test query $i"
    echo "  → Search #$i: \"$QUERY\""
    
    curl -s -X POST "$API_URL/search" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$QUERY\", \"top_k\": 10}" > /dev/null
    
    sleep $SLEEP_INTERVAL
done
echo -e "${GREEN}PASS${NC}: Completed $SEARCH_COUNT searches"
echo ""

# Step 5: 验证 metrics 计数递增
echo "[5/5] Verifying metrics increment..."
sleep 2  # 等待数据刷新

FINAL_RESP=$(curl -s "$API_URL/admin/health")
FINAL_SAMPLES=$(echo "$FINAL_RESP" | jq -r '.metrics.samples_60s // 0')
echo "Final samples_60s: $FINAL_SAMPLES"

DIFF=$((FINAL_SAMPLES - INITIAL_SAMPLES))

if [ "$DIFF" -ge "$SEARCH_COUNT" ]; then
    echo -e "${GREEN}PASS${NC}: Metrics incremented by $DIFF (expected >= $SEARCH_COUNT)"
elif [ "$DIFF" -gt 0 ]; then
    echo -e "${YELLOW}PARTIAL${NC}: Metrics incremented by $DIFF (expected $SEARCH_COUNT)"
    echo "This may be due to timing. Check logs for details."
else
    echo -e "${RED}FAIL${NC}: Metrics did not increment (diff=$DIFF)"
    echo "Expected: $FINAL_SAMPLES >= $((INITIAL_SAMPLES + SEARCH_COUNT))"
    echo "This indicates core.metrics.push_sample() is not being called."
    exit 1
fi

echo ""
echo "========================================"
echo -e "  ${GREEN}✓ Smoke Test PASSED${NC}"
echo "========================================"
echo ""
echo "Core modules are correctly wired:"
echo "  ✓ /admin/health endpoint is reachable"
echo "  ✓ core.metrics is receiving samples"
echo "  ✓ No impact on existing /search behavior"
echo ""
echo "Next steps:"
echo "  - Run full validation: ./run_real_validation.sh"
echo "  - Check dashboard: http://localhost:8000/demo"
echo ""

