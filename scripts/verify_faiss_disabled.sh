#!/bin/bash
# verify_faiss_disabled.sh - 验证 FAISS 已完全禁用
# ==========================================================
# 验证通过 DISABLE_FAISS=true 禁用 FAISS 后的行为
#
# Usage:
#   export DISABLE_FAISS=true PREWARM_FAISS=false
#   # Restart API
#   ./scripts/verify_faiss_disabled.sh

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
echo "FAISS DISABLE VERIFICATION"
echo "======================================================================"
echo

# Test 1: Check routing/status reports faiss_enabled=false
echo "[1/5] Checking routing status..."
ROUTING_STATUS=$(curl -4 -s --max-time 2 "$BASE_URL/ops/routing/status")

FAISS_ENABLED=$(echo "$ROUTING_STATUS" | jq -r '.faiss.enabled')
if [ "$FAISS_ENABLED" = "false" ]; then
    check_pass "faiss_enabled = false"
else
    check_fail "faiss_enabled = $FAISS_ENABLED (expected false)"
fi

FAISS_READY=$(echo "$ROUTING_STATUS" | jq -r '.faiss.ready')
if [ "$FAISS_READY" = "false" ]; then
    check_pass "faiss_ready = false"
else
    check_fail "faiss_ready = $FAISS_READY (expected false)"
fi

echo

# Test 2: Send search request with Lab headers
echo "[2/5] Sending search request with Lab headers..."
SEARCH_RESPONSE=$(curl -4 -s --max-time 5 -X POST "$BASE_URL/search" \
    -H "Content-Type: application/json" \
    -H "X-Lab-Exp: verify_faiss_disabled" \
    -H "X-Lab-Phase: A" \
    -H "X-TopK: 10" \
    -d '{"query":"investment portfolio","top_k":10,"collection":"fiqa"}' \
    -D /tmp/search_headers.txt)

SEARCH_OK=$(echo "$SEARCH_RESPONSE" | jq -r '.ok')
if [ "$SEARCH_OK" = "true" ]; then
    check_pass "Search request successful"
else
    check_fail "Search request failed"
    echo "$SEARCH_RESPONSE" | jq '.'
fi

# Test 3: Check X-Search-Route header
echo "[3/5] Checking X-Search-Route header..."
ROUTE_HEADER=$(grep -i "X-Search-Route" /tmp/search_headers.txt | awk '{print $2}' | tr -d '\r')

if [[ "$ROUTE_HEADER" != *"faiss"* ]]; then
    check_pass "X-Search-Route = $ROUTE_HEADER (not faiss)"
else
    check_fail "X-Search-Route = $ROUTE_HEADER (should not be faiss)"
fi

# Test 4: Check Redis metrics were recorded
echo "[4/5] Checking Redis metrics..."
sleep 1
REDIS_COUNT=$(redis-cli LLEN "lab:exp:verify_faiss_disabled:raw" 2>/dev/null || echo "0")

if [ "$REDIS_COUNT" -gt "0" ]; then
    check_pass "Redis recorded $REDIS_COUNT samples"
    
    # Check sample content
    SAMPLE=$(redis-cli --raw LINDEX "lab:exp:verify_faiss_disabled:raw" 0)
    SAMPLE_ROUTE=$(echo "$SAMPLE" | jq -r '.route')
    
    if [[ "$SAMPLE_ROUTE" != "faiss" ]]; then
        check_pass "Sample route = $SAMPLE_ROUTE (not faiss)"
    else
        check_fail "Sample route = $SAMPLE_ROUTE (should not be faiss)"
    fi
else
    check_fail "No Redis samples recorded (expected > 0)"
fi

# Test 5: Runtime disable test
echo "[5/5] Testing runtime faiss_enabled control..."
DISABLE_RESULT=$(curl -4 -s --max-time 2 -X POST "$BASE_URL/ops/routing/flags" \
    -H "Content-Type: application/json" \
    -d '{"faiss_enabled": false, "manual_backend": "milvus"}')

FAISS_ENABLED_AFTER=$(echo "$DISABLE_RESULT" | jq -r '.faiss_enabled')
if [ "$FAISS_ENABLED_AFTER" = "false" ]; then
    check_pass "Runtime faiss_enabled control works"
else
    check_fail "Runtime control failed (faiss_enabled=$FAISS_ENABLED_AFTER)"
fi

echo
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}ALL PASS ✅${NC}"
    echo "FAISS is successfully disabled. All requests route to Qdrant/Milvus."
    exit 0
else
    echo -e "${YELLOW}SOME CHECKS FAILED ⚠${NC}"
    exit 1
fi

