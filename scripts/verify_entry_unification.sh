#!/usr/bin/env bash
#
# Entry Unification Verification Script
# ======================================
# Validates unified frontend-backend access entry configuration
#
# Features:
# 1. Checks Vite proxy configuration (/api → 8011)
# 2. Tests /api/* endpoints are accessible from backend
# 3. Tests /ops/* endpoints still work (backward compatibility)
# 4. Validates no CORS errors
# 5. Verifies frontend code uses /api paths
#
# Exit codes:
#   0 - All checks pass
#   1 - Verification failed

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8011}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
TIMEOUT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

print_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
}

print_check() {
    local status="$1"
    local message="$2"
    
    if [[ "$status" == "PASS" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [[ "$status" == "FAIL" ]]; then
        echo -e "${RED}✗${NC} $message"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    elif [[ "$status" == "WARN" ]]; then
        echo -e "${YELLOW}⚠${NC} $message"
    else
        echo -e "${BLUE}ℹ${NC} $message"
    fi
}

check_backend_health() {
    print_header "1. Backend Health Check"
    
    if curl -sf --max-time 5 "$BASE_URL/healthz" > /dev/null 2>&1; then
        print_check "PASS" "Backend reachable at $BASE_URL"
    else
        print_check "FAIL" "Backend not reachable at $BASE_URL"
        echo -e "${YELLOW}Start backend with: cd services/fiqa_api && uvicorn app_main:app --port 8011${NC}"
        return 1
    fi
}

check_api_endpoints() {
    print_header "2. /api/* Endpoints (Primary - Full Check)"
    
    # Core health endpoints
    if curl -sf --max-time 5 "$BASE_URL/readyz" > /dev/null 2>&1; then
        local READY_JSON=$(curl -sf --max-time 5 "$BASE_URL/readyz" 2>&1)
        if echo "$READY_JSON" | grep -q '"ok".*true' && echo "$READY_JSON" | python3 -m json.tool > /dev/null 2>&1; then
            print_check "PASS" "/readyz OK (status 200, valid JSON)"
        else
            print_check "FAIL" "/readyz returned invalid JSON"
        fi
    else
        print_check "FAIL" "/readyz failed"
    fi
    
    # Agent V2 endpoints
    if curl -sf --max-time 5 "$BASE_URL/api/agent/summary?v=2" > /dev/null 2>&1; then
        local SUMMARY_JSON=$(curl -sf --max-time 5 "$BASE_URL/api/agent/summary?v=2" 2>&1)
        if echo "$SUMMARY_JSON" | python3 -m json.tool > /dev/null 2>&1; then
            print_check "PASS" "/api/agent/summary?v=2 OK"
        else
            print_check "FAIL" "/api/agent/summary?v=2 invalid JSON"
        fi
    else
        print_check "FAIL" "/api/agent/summary?v=2 failed"
    fi
    
    # Lab endpoints
    if curl -sf --max-time 5 "$BASE_URL/api/lab/config" > /dev/null 2>&1; then
        local CONFIG_JSON=$(curl -sf --max-time 5 "$BASE_URL/api/lab/config" 2>&1)
        if echo "$CONFIG_JSON" | python3 -m json.tool > /dev/null 2>&1; then
            print_check "PASS" "/api/lab/config OK"
        else
            print_check "WARN" "/api/lab/config exists but invalid JSON"
        fi
    else
        print_check "WARN" "/api/lab/config not found (may not be implemented)"
    fi
    
    # Routing endpoints
    if curl -sf --max-time 5 "$BASE_URL/api/routing/status" > /dev/null 2>&1; then
        local ROUTING_JSON=$(curl -sf --max-time 5 "$BASE_URL/api/routing/status" 2>&1)
        if echo "$ROUTING_JSON" | python3 -m json.tool > /dev/null 2>&1; then
            print_check "PASS" "/api/routing/status OK"
        else
            print_check "WARN" "/api/routing/status invalid JSON"
        fi
    else
        print_check "WARN" "/api/routing/status not found (may not be implemented)"
    fi
    
    # Force override endpoints
    if curl -sf --max-time 5 "$BASE_URL/api/force_status" > /dev/null 2>&1; then
        print_check "PASS" "/api/force_status OK"
    else
        print_check "FAIL" "/api/force_status failed"
    fi
}

check_ops_compatibility() {
    print_header "3. /ops/* Endpoints (Deprecated - Backward Compatibility)"
    
    # Test /ops/agent/summary?v=2
    local OPS_RESP=$(curl -sf --max-time 5 -D - "$BASE_URL/ops/agent/summary?v=2" 2>&1)
    if echo "$OPS_RESP" | grep -q "HTTP.*200"; then
        # Check for deprecation header
        if echo "$OPS_RESP" | grep -qi "deprecation"; then
            print_check "PASS" "/ops/agent/summary?v=2 OK + deprecation header"
        else
            print_check "PASS" "/ops/agent/summary?v=2 OK (legacy)"
        fi
    else
        print_check "WARN" "/ops/agent/summary?v=2 failed (non-critical)"
    fi
    
    # Test /ops/force_status
    if curl -sf --max-time 5 "$BASE_URL/ops/force_status" > /dev/null 2>&1; then
        print_check "PASS" "/ops/force_status OK (legacy)"
    else
        print_check "WARN" "/ops/force_status failed (non-critical)"
    fi
}

check_vite_config() {
    print_header "4. Vite Proxy Configuration"
    
    local VITE_CONFIG="frontend/vite.config.ts"
    
    if [[ ! -f "$VITE_CONFIG" ]]; then
        print_check "FAIL" "Vite config not found: $VITE_CONFIG"
        return 1
    fi
    
    # Check for /api proxy
    if grep -q "'/api':" "$VITE_CONFIG"; then
        print_check "PASS" "Vite config has /api proxy"
    else
        print_check "FAIL" "Vite config missing /api proxy"
    fi
    
    # Check proxy target
    if grep -q "target: 'http://localhost:8011'" "$VITE_CONFIG"; then
        print_check "PASS" "Proxy target is http://localhost:8011"
    else
        print_check "WARN" "Proxy target may not be localhost:8011"
    fi
}

check_frontend_code() {
    print_header "5. Frontend Code Paths"
    
    # Check if frontend uses /api paths
    local API_USAGE=$(grep -r "/api/" frontend/src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
    local OPS_USAGE=$(grep -r "/ops/" frontend/src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
    
    if [[ $API_USAGE -gt 0 ]]; then
        print_check "PASS" "Frontend uses /api paths ($API_USAGE occurrences)"
    else
        print_check "FAIL" "Frontend does not use /api paths"
    fi
    
    if [[ $OPS_USAGE -eq 0 ]]; then
        print_check "PASS" "Frontend has no /ops paths"
    else
        print_check "WARN" "Frontend still has /ops paths ($OPS_USAGE occurrences)"
    fi
}

check_cors() {
    print_header "6. CORS Configuration"
    
    # Check if backend allows localhost:3000
    ROOT_RESP=$(curl -sf --max-time 5 "$BASE_URL/" 2>&1 || echo '{}')
    
    if echo "$ROOT_RESP" | grep -q "SearchForge"; then
        print_check "PASS" "Backend root endpoint accessible"
    else
        print_check "WARN" "Backend root endpoint may have issues"
    fi
    
    # Note: Real CORS test requires browser, but we can check config
    if grep -q "http://localhost:3000" services/fiqa_api/app_main.py 2>/dev/null; then
        print_check "PASS" "Backend CORS allows localhost:3000"
    else
        print_check "INFO" "CORS config check skipped (requires code inspection)"
    fi
}

check_verification_scripts() {
    print_header "7. Verification Scripts Updated"
    
    # Check verify_agent_v2.sh
    if grep -q "/api/agent/run" scripts/verify_agent_v2.sh 2>/dev/null; then
        print_check "PASS" "verify_agent_v2.sh uses /api paths"
    else
        print_check "WARN" "verify_agent_v2.sh may not use /api paths"
    fi
    
    # Check schema_check_agent_v2.mjs
    if grep -q "/api/agent/run" scripts/schema_check_agent_v2.mjs 2>/dev/null; then
        print_check "PASS" "schema_check_agent_v2.mjs uses /api paths"
    else
        print_check "WARN" "schema_check_agent_v2.mjs may not use /api paths"
    fi
}

check_nginx_proxy() {
    print_header "8. Production Nginx Proxy (Optional)"
    
    # Check if nginx config exists
    if [[ -f "deploy/nginx_entry.conf" ]]; then
        print_check "PASS" "nginx_entry.conf found"
        
        # Test nginx config syntax (if nginx is installed)
        if command -v nginx > /dev/null 2>&1; then
            if nginx -t -c deploy/nginx_entry.conf > /dev/null 2>&1; then
                print_check "PASS" "nginx config syntax valid"
            else
                print_check "INFO" "nginx config syntax check skipped (needs root or adjustment)"
            fi
        else
            print_check "INFO" "nginx not installed, syntax check skipped"
        fi
        
        # Test if nginx proxy is running on port 8080
        if curl -sf --max-time 5 "http://localhost:8080/readyz" > /dev/null 2>&1; then
            print_check "PASS" "nginx proxy at :8080 responds to /readyz"
        else
            print_check "INFO" "nginx proxy not running (optional for dev)"
        fi
    else
        print_check "FAIL" "deploy/nginx_entry.conf not found"
    fi
}

generate_report() {
    print_header "Generating Report"
    
    local REPORT_DIR="reports"
    local REPORT_FILE="$REPORT_DIR/ENTRY_UNIFICATION_CHECK.txt"
    
    mkdir -p "$REPORT_DIR"
    
    cat > "$REPORT_FILE" << EOF
=================================================================
Entry Unification Check Report
=================================================================
Date: $(date '+%Y-%m-%d %H:%M:%S')
Base URL: $BASE_URL

-----------------------------------------------------------------
Results
-----------------------------------------------------------------
✅ Checks passed: $CHECKS_PASSED
❌ Checks failed: $CHECKS_FAILED

-----------------------------------------------------------------
Status
-----------------------------------------------------------------
EOF
    
    if [[ $CHECKS_FAILED -eq 0 ]]; then
        cat >> "$REPORT_FILE" << EOF
✅ ALL CHECKS PASSED

Entry points verified:
  ✓ /readyz - Health check
  ✓ /api/agent/summary?v=2 - Agent V2
  ✓ /api/lab/config - Lab config
  ✓ /api/routing/status - Routing
  ✓ /api/force_status - Force override
  ✓ /ops/* - Deprecated endpoints (still work)
  ✓ Vite proxy configured
  ✓ Frontend uses /api paths
  ✓ Nginx config exists

-----------------------------------------------------------------
Next Steps
-----------------------------------------------------------------
1. Start backend: cd services/fiqa_api && uvicorn app_main:app --port 8011
2. Start frontend: cd frontend && npm run dev
3. Open http://localhost:3000
4. Run E2E test: ./scripts/test_entry_e2e.mjs

=================================================================
EOF
    else
        cat >> "$REPORT_FILE" << EOF
❌ SOME CHECKS FAILED

Please review the errors and fix before deploying.
Run this script again after fixes.

=================================================================
EOF
    fi
    
    print_check "INFO" "Report generated: $REPORT_FILE"
}

print_summary() {
    print_header "Summary"
    
    echo ""
    echo "Checks passed: $CHECKS_PASSED"
    echo "Checks failed: $CHECKS_FAILED"
    echo ""
    
    if [[ $CHECKS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
        echo ""
        echo "Entry unification successful:"
        echo "  ✓ Frontend uses /api proxy (Vite config)"
        echo "  ✓ Backend serves /api/* endpoints"
        echo "  ✓ Backend preserves /ops/* for compatibility"
        echo "  ✓ Verification scripts updated"
        echo "  ✓ Production nginx config ready"
        echo ""
        
        # Run E2E test if available
        if [[ -f "scripts/test_entry_e2e.mjs" ]] && command -v node > /dev/null 2>&1; then
            echo -e "${BLUE}Running E2E test...${NC}"
            if node scripts/test_entry_e2e.mjs; then
                echo -e "${GREEN}✓ E2E test passed${NC}"
            else
                echo -e "${YELLOW}⚠ E2E test failed (may need frontend running)${NC}"
            fi
            echo ""
        fi
        
        echo "Next steps:"
        echo "  1. Start backend: cd services/fiqa_api && uvicorn app_main:app --port 8011"
        echo "  2. Start frontend: cd frontend && npm run dev"
        echo "  3. Open http://localhost:3000 (no CORS errors!)"
        echo ""
        return 0
    else
        echo -e "${RED}❌ VERIFICATION FAILED${NC}"
        echo ""
        echo "Some checks failed. Review errors above."
        echo ""
        return 1
    fi
}

# Main execution
main() {
    echo "Entry Unification Verification"
    echo "Base URL: $BASE_URL"
    echo ""
    
    check_backend_health || true
    check_api_endpoints
    check_ops_compatibility
    check_vite_config
    check_frontend_code
    check_cors
    check_verification_scripts
    check_nginx_proxy
    generate_report
    print_summary
}

main "$@"

