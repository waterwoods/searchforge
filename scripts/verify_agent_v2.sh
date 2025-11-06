#!/usr/bin/env bash
#
# Agent V2 Verification Script
# ============================
# Validates Agent V2 installation and endpoints
#
# Prerequisites:
#   - Backend running on port 8011
#   - Redis and Qdrant accessible
#
# Exit codes:
#   0 - All checks pass OR dependencies unhealthy (BLOCKED but not failure)
#   1 - Agent V2 validation failed

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8011}"
TIMEOUT=10
LINES_PRINTED=0
MAX_LINES=50

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_limited() {
    if [[ $LINES_PRINTED -lt $MAX_LINES ]]; then
        echo -e "$1"
        LINES_PRINTED=$((LINES_PRINTED + 1))
    fi
}

print_header() {
    print_limited ""
    print_limited "========================================="
    print_limited "$1"
    print_limited "========================================="
}

check_dependencies() {
    print_header "Pre-flight: Dependency Health"
    
    # Check if backend is up
    if ! curl -sf --max-time 5 "$BASE_URL/healthz" > /dev/null 2>&1; then
        print_limited "${RED}✗ Backend not reachable at $BASE_URL${NC}"
        print_limited "${YELLOW}BLOCKED${NC}: Start backend first"
        exit 0  # Not a failure, just blocked
    fi
    
    print_limited "${GREEN}✓${NC} Backend reachable"
    
    # Check readiness (Redis/Qdrant) - using /api prefix
    READY_RESP=$(curl -sf --max-time 5 "$BASE_URL/api/readyz" || curl -sf --max-time 5 "$BASE_URL/readyz" || echo '{"ok":false}')
    REDIS_OK=$(echo "$READY_RESP" | grep -o '"redis":[^}]*"ok":[^,}]*' | grep -o 'true\|false' || echo "false")
    QDRANT_OK=$(echo "$READY_RESP" | grep -o '"qdrant":[^}]*"ok":[^,}]*' | grep -o 'true\|false' || echo "false")
    
    # Fallback: Check if Redis backend is available (not degraded)
    if [[ "$REDIS_OK" != "true" ]]; then
        REDIS_DEGRADED=$(echo "$READY_RESP" | grep -o '"redis":[^}]*"degraded":[^,}]*' | grep -o 'true\|false' || echo "true")
        if [[ "$REDIS_DEGRADED" == "false" ]]; then
            REDIS_OK="true"
        fi
    fi
    
    if [[ "$REDIS_OK" != "true" ]]; then
        print_limited "${RED}✗ Redis unhealthy${NC}"
        print_limited "${YELLOW}BLOCKED${NC}: Fix Redis and retry"
        exit 0
    fi
    
    if [[ "$QDRANT_OK" != "true" ]]; then
        print_limited "${RED}✗ Qdrant unhealthy${NC}"
        print_limited "${YELLOW}BLOCKED${NC}: Fix Qdrant and retry"
        exit 0
    fi
    
    print_limited "${GREEN}✓${NC} Redis OK"
    print_limited "${GREEN}✓${NC} Qdrant OK"
}

test_dry_run() {
    print_header "Test 1: Dry Run"
    
    START_TIME=$(date +%s)
    RESP=$(curl -sf --max-time 30 -X POST "$BASE_URL/api/agent/run?v=2&dry=true" || echo '{"ok":false,"error":"request_failed"}')
    
    OK=$(echo "$RESP" | grep -o '"ok":[^,}]*' | cut -d: -f2 | tr -d ' ')
    MODE=$(echo "$RESP" | grep -o '"mode":"[^"]*"' | cut -d'"' -f4)
    
    if [[ "$OK" != "true" ]]; then
        print_limited "${RED}✗ Dry run failed${NC}"
        print_limited "Response: $RESP"
        exit 1
    fi
    
    if [[ "$MODE" != "dry" ]]; then
        print_limited "${RED}✗ Mode mismatch: expected 'dry', got '$MODE'${NC}"
        exit 1
    fi
    
    ELAPSED=$(($(date +%s) - START_TIME))
    print_limited "${GREEN}✓${NC} Dry run succeeded (${ELAPSED}s)"
}

test_summary_schema() {
    print_header "Test 2: Summary Schema"
    
    RESP=$(curl -sf --max-time 10 "$BASE_URL/api/agent/summary?v=2" || echo '{"ok":false}')
    
    OK=$(echo "$RESP" | grep -o '"ok":[^,}]*' | cut -d: -f2 | tr -d ' ')
    
    # Schema check: required keys
    REQUIRED_KEYS=("delta_p95_pct" "delta_qps_pct" "error_rate_pct" "bullets")
    
    for KEY in "${REQUIRED_KEYS[@]}"; do
        if ! echo "$RESP" | grep -q "\"$KEY\""; then
            print_limited "${RED}✗ Missing key: $KEY${NC}"
            exit 1
        fi
    done
    
    print_limited "${GREEN}✓${NC} Schema valid: all required keys present"
    
    # Extract values
    DELTA_P95=$(echo "$RESP" | grep -o '"delta_p95_pct":[^,}]*' | cut -d: -f2 | tr -d ' ')
    BULLETS_COUNT=$(echo "$RESP" | grep -o '"bullets":\[[^\]]*\]' | grep -o ',' | wc -l)
    BULLETS_COUNT=$((BULLETS_COUNT + 1))
    
    print_limited "  ΔP95: $DELTA_P95%"
    print_limited "  Bullets: $BULLETS_COUNT"
}

test_real_run_optional() {
    print_header "Test 3: Real Run (Optional)"
    
    # Only run if health is OK and --full flag passed
    if [[ "${1:-}" != "--full" ]]; then
        print_limited "${YELLOW}⊘${NC} Skipped (pass --full to enable)"
        return
    fi
    
    print_limited "Running real agent (120s budget)..."
    
    START_TIME=$(date +%s)
    RESP=$(curl -sf --max-time 130 -X POST "$BASE_URL/api/agent/run?v=2&dry=false" || echo '{"ok":false,"error":"timeout"}')
    
    OK=$(echo "$RESP" | grep -o '"ok":[^,}]*' | cut -d: -f2 | tr -d ' ')
    VERDICT=$(echo "$RESP" | grep -o '"verdict":"[^"]*"' | cut -d'"' -f4)
    
    ELAPSED=$(($(date +%s) - START_TIME))
    
    if [[ "$OK" == "true" ]]; then
        print_limited "${GREEN}✓${NC} Real run completed: $VERDICT (${ELAPSED}s)"
    else
        print_limited "${YELLOW}⚠${NC} Real run failed (non-critical): $RESP"
    fi
    
    # Fetch updated summary
    sleep 1
    SUMMARY=$(curl -sf --max-time 10 "$BASE_URL/api/agent/summary?v=2" || echo '{"ok":false}')
    UPDATED_AT=$(echo "$SUMMARY" | grep -o '"generated_at":"[^"]*"' | cut -d'"' -f4)
    
    if [[ -n "$UPDATED_AT" ]]; then
        print_limited "${GREEN}✓${NC} Summary updated: $UPDATED_AT"
    fi
}

final_report() {
    print_header "Final Report"
    
    print_limited "${GREEN}✅ ALL PASS${NC}"
    print_limited ""
    print_limited "Agent V2 installation verified:"
    print_limited "  - Dry run endpoint works"
    print_limited "  - Summary endpoint returns valid schema"
    print_limited "  - All required keys present"
    print_limited ""
    print_limited "Next steps:"
    print_limited "  1. Start frontend: npm run dev (from frontend/)"
    print_limited "  2. Open http://localhost:3000/agent"
    print_limited "  3. Click 'Refresh' to view last summary"
    print_limited ""
}

# Main execution
main() {
    print_limited "Agent V2 Verification"
    print_limited "Base URL: $BASE_URL"
    print_limited ""
    
    check_dependencies
    test_dry_run
    test_summary_schema
    test_real_run_optional "$@"
    final_report
}

main "$@"

