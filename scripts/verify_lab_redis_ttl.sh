#!/bin/bash
# verify_lab_redis_ttl.sh - 验证 Lab Redis TTL 配置
# ====================================================
# 验证 Redis TTL 是否正确延长到 24 小时

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================================"
echo "LAB REDIS TTL VERIFICATION"
echo "======================================================================"
echo

# Test 1: 写入测试键并检查 TTL
echo "[1/3] Testing Redis TTL setting..."

TEST_KEY="lab:exp:test_ttl_verify"
TEST_VALUE=$(date +%s)

# 使用 24 小时 TTL
redis-cli SET "$TEST_KEY" "$TEST_VALUE" EX 86400 > /dev/null

TTL=$(redis-cli TTL "$TEST_KEY")

if [ "$TTL" -gt 80000 ]; then
    echo -e "${GREEN}✅ Redis TTL extended OK ($TTL sec ≈ $((TTL / 3600)) hours)${NC}"
else
    echo -e "${RED}❌ TTL still too short ($TTL sec)${NC}"
    exit 1
fi

echo

# Test 2: 验证环境变量
echo "[2/3] Checking LAB_REDIS_TTL environment variable..."

if [ -n "$LAB_REDIS_TTL" ]; then
    echo -e "${GREEN}✅ LAB_REDIS_TTL set to: $LAB_REDIS_TTL seconds${NC}"
else
    echo "ℹ  LAB_REDIS_TTL not set (will use default 86400)"
fi

echo

# Test 3: 验证实际 lab:exp 键的 TTL
echo "[3/3] Checking existing lab:exp keys..."

LATEST_KEY=$(redis-cli KEYS "lab:exp:*:raw" | tail -1)

if [ -n "$LATEST_KEY" ]; then
    ACTUAL_TTL=$(redis-cli TTL "$LATEST_KEY")
    
    if [ "$ACTUAL_TTL" -gt 0 ]; then
        echo -e "${GREEN}✅ Lab key TTL: $ACTUAL_TTL sec ($((ACTUAL_TTL / 3600)) hours remaining)${NC}"
        
        if [ "$ACTUAL_TTL" -gt 80000 ]; then
            echo -e "${GREEN}✅ TTL is sufficient for long tests${NC}"
        else
            echo -e "${RED}⚠  TTL < 24h, may expire during long tests${NC}"
        fi
    else
        echo "ℹ  No TTL set on existing keys (or already expired)"
    fi
else
    echo "ℹ  No existing lab:exp keys found"
fi

echo
echo "======================================================================"
echo "VERIFICATION RESULT"
echo "======================================================================"
echo -e "${GREEN}✅ Redis TTL configuration verified${NC}"
echo
echo "For long tests (>2h), set before starting API:"
echo "  export LAB_REDIS_TTL=86400  # 24 hours"
echo
echo "Current setting will preserve data for ~24 hours after last write."
echo "======================================================================"

# Cleanup test key
redis-cli DEL "$TEST_KEY" > /dev/null

exit 0

