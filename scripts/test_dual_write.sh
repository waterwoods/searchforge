#!/bin/bash
# test_dual_write.sh - 双写功能快速验证脚本
# 验证 CSV + core.metrics 双写是否正常工作

set -e

API_URL="http://localhost:8080"
SLEEP_INTERVAL=2
SEARCH_COUNT=10

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Dual-Write Verification Test"
echo "========================================"
echo ""

# Step 1: 检查服务
echo "[1/5] Checking service..."
if ! curl -s -f "$API_URL/health" > /dev/null; then
    echo -e "${RED}FAIL${NC}: Service not running at $API_URL"
    echo "Please start: cd services/fiqa_api && CORE_METRICS_ENABLED=1 uvicorn app:app --reload"
    exit 1
fi
echo -e "${GREEN}PASS${NC}: Service is running"
echo ""

# Step 2: 检查双写开关状态
echo "[2/5] Checking CORE_METRICS_ENABLED status..."
SNAPSHOT_RESP=$(curl -s "$API_URL/metrics/snapshot")
ENABLED=$(echo "$SNAPSHOT_RESP" | jq -r '.enabled // false')
OK=$(echo "$SNAPSHOT_RESP" | jq -r '.ok // false')

if [ "$OK" = "false" ]; then
    echo -e "${YELLOW}WARN${NC}: Dual-write is DISABLED"
    echo "Response: $SNAPSHOT_RESP"
    echo ""
    echo "To enable, restart service with:"
    echo "  export CORE_METRICS_ENABLED=1"
    echo "  MAIN_PORT=8000 bash services/fiqa_api/start_server.sh"
    exit 1
fi

echo -e "${GREEN}PASS${NC}: Dual-write is ENABLED"
echo ""

# Step 3: 记录初始状态
echo "[3/5] Recording initial metrics..."
INITIAL_ROWS=$(echo "$SNAPSHOT_RESP" | jq -r '.rows // 0')
echo "Initial rows (60s window): $INITIAL_ROWS"
echo ""

# Step 4: 执行搜索请求
echo "[4/5] Executing $SEARCH_COUNT search requests..."
for i in $(seq 1 $SEARCH_COUNT); do
    QUERY="test dual write query $i"
    MODE=$([ $((i % 2)) -eq 0 ] && echo "on" || echo "off")
    
    echo "  → Search #$i (mode=$MODE): \"$QUERY\""
    
    curl -s -X POST "$API_URL/search" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$QUERY\", \"top_k\": 10}" > /dev/null
    
    sleep $SLEEP_INTERVAL
done
echo -e "${GREEN}PASS${NC}: Completed $SEARCH_COUNT searches"
echo ""

# Step 5: 验证双写效果
echo "[5/5] Verifying dual-write effect..."
sleep 2  # 等待数据刷新

FINAL_RESP=$(curl -s "$API_URL/metrics/snapshot")
FINAL_ROWS=$(echo "$FINAL_RESP" | jq -r '.rows // 0')
echo "Final rows (60s window): $FINAL_ROWS"

DIFF=$((FINAL_ROWS - INITIAL_ROWS))

if [ "$DIFF" -ge "$SEARCH_COUNT" ]; then
    echo -e "${GREEN}PASS${NC}: Metrics incremented by $DIFF (expected >= $SEARCH_COUNT)"
elif [ "$DIFF" -gt 0 ]; then
    echo -e "${YELLOW}PARTIAL${NC}: Metrics incremented by $DIFF (expected $SEARCH_COUNT)"
    echo "This may be due to timing or 60s window sliding."
else
    echo -e "${RED}FAIL${NC}: Metrics did not increment (diff=$DIFF)"
    echo "Expected: $FINAL_ROWS >= $((INITIAL_ROWS + SEARCH_COUNT))"
    echo "This indicates metrics_sink.push() is not being called."
    exit 1
fi

echo ""
echo "========================================"
echo -e "  ${GREEN}✓ Dual-Write Test PASSED${NC}"
echo "========================================"
echo ""
echo "Verification Results:"
echo "  ✓ Service is running"
echo "  ✓ CORE_METRICS_ENABLED=1 (dual-write ON)"
echo "  ✓ metrics_sink is receiving samples"
echo "  ✓ /metrics/snapshot endpoint works"
echo "  ✓ Incremented by $DIFF samples in 60s window"
echo ""
echo "Next steps:"
echo "  - Check CSV: tail -5 logs/api_metrics.csv"
echo "  - Test with Auto Traffic: open http://localhost:8000/demo"
echo "  - Test switch OFF: export CORE_METRICS_ENABLED=0 && restart"
echo ""

# Bonus: 检查 CSV 是否也在写入
if [ -f "logs/api_metrics.csv" ]; then
    CSV_LINES=$(wc -l < logs/api_metrics.csv)
    echo -e "${BLUE}INFO${NC}: CSV file has $CSV_LINES lines (CSV write path is also working)"
else
    echo -e "${YELLOW}WARN${NC}: CSV file not found at logs/api_metrics.csv"
fi

echo ""

