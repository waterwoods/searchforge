#!/bin/bash
# verify_reporter_alignment.sh - 验证报告器对齐
# ====================================================
# 验证 /api/lab/report 能正确从 Redis 读取数据

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="http://127.0.0.1:8011"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

echo "======================================================================"
echo "REPORTER ALIGNMENT VERIFICATION"
echo "======================================================================"
echo

# Test 1: 查找最近的实验数据
echo "[1/5] Checking for experiment data in Redis..."
cd "$PROJECT_ROOT"

LATEST_KEY=$(redis-cli KEYS "lab:exp:*:raw" | tail -1)

if [ -z "$LATEST_KEY" ]; then
    check_fail "No experiment data in Redis"
    echo
    echo "Please run a test first:"
    echo "  ./scripts/demo_combo_quick.sh"
    exit 1
fi

# 提取实验 ID
EXP_ID=$(echo "$LATEST_KEY" | cut -d: -f3)
RAW_COUNT=$(redis-cli LLEN "$LATEST_KEY")

if [ "$RAW_COUNT" -gt 100 ]; then
    check_pass "Found experiment data: $EXP_ID ($RAW_COUNT samples)"
else
    check_fail "Insufficient data: $RAW_COUNT samples (need >100)"
fi

echo

# Test 2: 测试 /api/lab/report?mini=1 端点
echo "[2/5] Testing /api/lab/report?mini=1..."

MINI_RESPONSE=$(curl -4 -s --max-time 3 "$BASE_URL/api/lab/report?mini=1&exp_id=$EXP_ID")

if echo "$MINI_RESPONSE" | jq -e '.ok' >/dev/null 2>&1; then
    OK=$(echo "$MINI_RESPONSE" | jq -r '.ok')
    
    if [ "$OK" = "true" ]; then
        check_pass "/api/lab/report?mini=1 returned ok=true"
    else
        MESSAGE=$(echo "$MINI_RESPONSE" | jq -r '.message')
        check_fail "/api/lab/report?mini=1 returned ok=false: $MESSAGE"
    fi
else
    check_fail "/api/lab/report?mini=1 failed to parse response"
    echo "$MINI_RESPONSE" | head -3
fi

echo

# Test 3: 验证必需字段
echo "[3/5] Validating required fields..."

HAS_DELTA_P95=$(echo "$MINI_RESPONSE" | jq 'has("delta_p95_pct")')
HAS_DELTA_QPS=$(echo "$MINI_RESPONSE" | jq 'has("delta_qps_pct")')
HAS_ERROR_RATE=$(echo "$MINI_RESPONSE" | jq 'has("error_rate_pct")')

if [ "$HAS_DELTA_P95" = "true" ]; then
    check_pass "Has delta_p95_pct"
else
    check_fail "Missing delta_p95_pct"
fi

if [ "$HAS_DELTA_QPS" = "true" ]; then
    check_pass "Has delta_qps_pct"
else
    check_fail "Missing delta_qps_pct"
fi

if [ "$HAS_ERROR_RATE" = "true" ]; then
    check_pass "Has error_rate_pct"
else
    check_fail "Missing error_rate_pct"
fi

echo

# Test 4: 测试无 agg 时从 raw 聚合
echo "[4/5] Testing aggregation from raw data..."

# 清除可能的 agg 数据
redis-cli DEL "lab:exp:${EXP_ID}:agg" >/dev/null 2>&1 || true

# 重新请求
MINI_RESPONSE_2=$(curl -4 -s --max-time 3 "$BASE_URL/api/lab/report?mini=1&exp_id=$EXP_ID")
OK_2=$(echo "$MINI_RESPONSE_2" | jq -r '.ok')

if [ "$OK_2" = "true" ]; then
    check_pass "Can aggregate from raw when no agg exists"
else
    check_fail "Failed to aggregate from raw"
fi

echo

# Test 5: 验证响应时间
echo "[5/5] Testing response time..."

START_TIME=$(date +%s.%N)
curl -4 -s --max-time 3 "$BASE_URL/api/lab/report?mini=1" >/dev/null
END_TIME=$(date +%s.%N)
ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)
ELAPSED_MS=$(echo "$ELAPSED * 1000" | bc | cut -d. -f1)

if [ "$ELAPSED_MS" -lt 150 ]; then
    check_pass "Response time: ${ELAPSED_MS}ms (< 150ms)"
else
    check_fail "Response time: ${ELAPSED_MS}ms (>= 150ms)"
fi

echo
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ REPORTER ALIGN PASS${NC}"
    echo
    echo "Reporter can read Redis data and generate reports!"
    echo "Ready for long-running tests."
    exit 0
else
    echo -e "${YELLOW}❌ REPORTER ALIGN FAILED${NC}"
    echo
    echo "Some checks failed. Review the output above."
    exit 1
fi

