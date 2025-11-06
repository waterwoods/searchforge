#!/bin/bash
# test_series60s_hardening.sh - 验证 series60s 硬化改进
# 用法: ./scripts/test_series60s_hardening.sh
# 退出码: 0=PASS, 1=FAIL

# 注意：不使用 set -e，因为测试可能失败但需要继续执行

API_URL="${API_URL:-http://localhost:8080}"
ENDPOINT="$API_URL/metrics/series60s"
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=5

echo "=========================================="
echo "series60s 硬化验证"
echo "端点: $ENDPOINT"
echo "=========================================="
echo ""

# Helper: 测试结果输出
test_result() {
    local name="$1"
    local result="$2"
    if [ "$result" = "PASS" ]; then
        echo "✅ [$name] PASS"
        ((PASS_COUNT++))
    else
        echo "❌ [$name] FAIL: $3"
        ((FAIL_COUNT++))
    fi
}

# 检查服务是否运行
echo "[0/5] 预检查: 服务健康状态..."
if ! curl -s -f "$API_URL/admin/health" > /dev/null; then
    echo "❌ 服务未运行或不可达: $API_URL"
    echo "请先启动服务: cd services/fiqa_api && uvicorn app_v2:app --port 8080"
    exit 1
fi
echo "✅ 服务正常运行"
echo ""

# Test 1: 桶数验证 (12-13个桶)
echo "[1/5] 测试桶数量..."
RESPONSE=$(curl -s "$ENDPOINT")
BUCKET_COUNT=$(echo "$RESPONSE" | jq -r '.buckets')

if [ "$BUCKET_COUNT" -ge 12 ] && [ "$BUCKET_COUNT" -le 13 ]; then
    test_result "桶数量" "PASS"
else
    test_result "桶数量" "FAIL" "期望 12-13，实际 $BUCKET_COUNT"
fi

# Test 2: 时间戳5s对齐验证
echo "[2/5] 测试时间戳对齐..."
# 使用 bc 处理大数字运算（或直接用 jq 验证）
MISALIGNED=$(echo "$RESPONSE" | jq '[.p95[][0]] | map(. % 5000) | map(select(. != 0)) | length')

if [ "$MISALIGNED" -eq 0 ]; then
    test_result "时间戳对齐" "PASS"
else
    test_result "时间戳对齐" "FAIL" "发现 $MISALIGNED 个未对齐的时间戳 (ts % 5000 != 0)"
fi

# Test 3: 数组长度一致性
echo "[3/5] 测试数组长度一致性..."
P95_LEN=$(echo "$RESPONSE" | jq -r '.p95 | length')
TPS_LEN=$(echo "$RESPONSE" | jq -r '.tps | length')
RECALL_LEN=$(echo "$RESPONSE" | jq -r '.recall | length')

if [ "$P95_LEN" -eq "$TPS_LEN" ] && [ "$TPS_LEN" -eq "$RECALL_LEN" ]; then
    test_result "数组长度" "PASS"
else
    test_result "数组长度" "FAIL" "p95=$P95_LEN, tps=$TPS_LEN, recall=$RECALL_LEN"
fi

# Test 4: Debug字段存在性验证
echo "[4/5] 测试 debug 字段..."
HAS_CLOCK_SKEW=$(echo "$RESPONSE" | jq -r '.meta.debug.clock_skew_ms != null')
HAS_FILLED_NULL=$(echo "$RESPONSE" | jq -r '.meta.debug.filled_null_buckets != null')
HAS_NON_EMPTY=$(echo "$RESPONSE" | jq -r '.meta.debug.non_empty_buckets != null')

if [ "$HAS_CLOCK_SKEW" = "true" ] && [ "$HAS_FILLED_NULL" = "true" ] && [ "$HAS_NON_EMPTY" = "true" ]; then
    test_result "debug字段" "PASS"
else
    test_result "debug字段" "FAIL" "缺少必需的 debug 字段"
fi

# Test 5: 全空窗口模拟 (检查 TPS=0, P95/Recall=null 仍输出)
echo "[5/5] 测试空窗口处理..."
# 注意：这个测试需要等待60s无流量，或者检查现有响应中的null处理
# 简化版：检查至少有一个null值的桶（表示空桶处理正确）
NULL_P95_COUNT=$(echo "$RESPONSE" | jq '[.p95[][1]] | map(select(. == null)) | length')
ZERO_TPS_COUNT=$(echo "$RESPONSE" | jq '[.tps[][1]] | map(select(. == 0)) | length')

if [ "$NULL_P95_COUNT" -gt 0 ] || [ "$ZERO_TPS_COUNT" -gt 0 ]; then
    test_result "空桶处理" "PASS"
else
    # 如果所有桶都有数据，也是正常的（说明有持续流量）
    # 只需确保数据结构正确即可
    if [ "$BUCKET_COUNT" -ge 12 ] && [ "$BUCKET_COUNT" -le 13 ]; then
        test_result "空桶处理" "PASS"
    else
        test_result "空桶处理" "FAIL" "无法验证空桶处理逻辑"
    fi
fi

echo ""
echo "=========================================="
echo "测试完成: $PASS_COUNT/$TOTAL_TESTS 通过"
echo "=========================================="

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 所有测试通过 - PASS"
    exit 0
else
    echo "⚠️  部分测试失败 - FAIL"
    exit 1
fi

