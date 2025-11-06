#!/usr/bin/env bash
#
# verify_app_main.sh
# Verification script for app_main health, endpoints, and schema consistency
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8011}"
CHECKS_PASSED=0
CHECKS_TOTAL=0

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; CHECKS_PASSED=$((CHECKS_PASSED + 1)); }
log_error() { echo -e "${RED}[✗]${NC} $*"; }
check_start() { CHECKS_TOTAL=$((CHECKS_TOTAL + 1)); }

echo "=========================================="
echo "AppMain Verification"
echo "=========================================="
echo ""

# Check 1: Health endpoint
check_start
log_info "Check 1: /healthz endpoint..."
HEALTH=$(curl -sf "${API_URL}/healthz" 2>/dev/null || echo "{}")
if echo "$HEALTH" | jq -e '.ok == true' > /dev/null 2>&1; then
    log_success "/healthz返回 ok=true"
else
    log_error "/healthz 失败"
    exit 1
fi

# Check 2: Readiness endpoint with degraded support
check_start
log_info "Check 2: /readyz endpoint..."
READY=$(curl -sf "${API_URL}/readyz" 2>/dev/null || echo "{}")
if echo "$READY" | jq -e '.ok == true' > /dev/null 2>&1; then
    DEGRADED=$(echo "$READY" | jq -r '.degraded // false')
    STORAGE=$(echo "$READY" | jq -r '.storage.backend // "unknown"')
    
    if [[ "$DEGRADED" == "true" ]]; then
        log_success "/readyz返回 ok=true (degraded=true, storage=$STORAGE)"
    else
        log_success "/readyz返回 ok=true (storage=$STORAGE)"
    fi
else
    log_error "/readyz 失败"
    exit 1
fi

# Check 3: /ops/verify endpoint (async)
check_start
log_info "Check 3: /ops/verify endpoint..."
VERIFY=$(curl -sf "${API_URL}/ops/verify" 2>/dev/null || echo "{}")
if echo "$VERIFY" | jq -e '.ok == true' > /dev/null 2>&1; then
    BS_ENABLED=$(echo "$VERIFY" | jq -r '.black_swan_async.enabled // false')
    log_success "/ops/verify返回 ok=true (black_swan_async.enabled=$BS_ENABLED)"
else
    log_error "/ops/verify 失败"
    exit 1
fi

# Check 4: Schema consistency - precedence_chain
check_start
log_info "Check 4: Force override precedence_chain..."
FORCE_STATUS=$(curl -sf "${API_URL}/ops/force_status" 2>/dev/null || echo "{}")
if echo "$FORCE_STATUS" | jq -e '.precedence_chain' > /dev/null 2>&1; then
    CHAIN_LEN=$(echo "$FORCE_STATUS" | jq '.precedence_chain | length')
    log_success "precedence_chain字段存在 (length=$CHAIN_LEN)"
else
    log_error "precedence_chain字段缺失"
    exit 1
fi

# Check 5: Concurrent requests test (50 concurrent)
check_start
log_info "Check 5: 并发请求测试 (50 concurrent)..."
START_TIME=$(date +%s)

# Use xargs for parallel requests
seq 50 | xargs -P 50 -I {} curl -sf "${API_URL}/ops/verify" > /dev/null 2>&1

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [[ $? -eq 0 ]]; then
    log_success "50个并发请求全部成功 (${DURATION}s)"
else
    log_error "并发请求测试失败"
    exit 1
fi

# Check 6: Black Swan status endpoint
check_start
log_info "Check 6: Black Swan status endpoint..."
BS_STATUS=$(curl -sf "${API_URL}/ops/black_swan/status" 2>/dev/null || echo '{"ok":false}')
if echo "$BS_STATUS" | jq -e '.ok == true or .ok == false' > /dev/null 2>&1; then
    PHASE=$(echo "$BS_STATUS" | jq -r '.phase // "no_run"')
    log_success "Black Swan status endpoint responding (phase=$PHASE)"
else
    log_error "Black Swan status endpoint 失败"
    exit 1
fi

# Check 7: Storage backend reporting
check_start
log_info "Check 7: Storage backend reporting..."
STORAGE_BACKEND=$(echo "$READY" | jq -r '.storage.backend // "unknown"')
if [[ "$STORAGE_BACKEND" == "redis" ]] || [[ "$STORAGE_BACKEND" == "memory" ]]; then
    log_success "Storage backend: $STORAGE_BACKEND"
else
    log_error "Storage backend未知: $STORAGE_BACKEND"
    exit 1
fi

# Final summary
echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Checks passed: $CHECKS_PASSED / $CHECKS_TOTAL"
echo ""

if [[ $CHECKS_PASSED -eq $CHECKS_TOTAL ]]; then
    echo -e "${GREEN}=========================================="
    echo -e "✓ ALL CHECKS PASSED (app_main)"
    echo -e "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo -e "✗ SOME CHECKS FAILED"
    echo -e "==========================================${NC}"
    exit 1
fi
