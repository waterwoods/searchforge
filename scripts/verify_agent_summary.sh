#!/bin/bash
# ================================================================
# Agent Summary V2 Verification Script
# ================================================================
# Verifies /api/agent/summary?v=2 always returns HTTP 200 + JSON
# and never throws 500 errors (soft-fail mode).
#
# Usage:
#   ./scripts/verify_agent_summary.sh
#
# Exit codes:
#   0 = Success (endpoint healthy)
#   1 = Failure (500 error or malformed response)
# ================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config
BASE_URL="${BASE_URL:-http://localhost:8011}"
ENDPOINT="/api/agent/summary?v=2"
FULL_URL="$BASE_URL$ENDPOINT"

echo "================================================================"
echo "Agent Summary V2 Verification"
echo "================================================================"
echo ""
echo "Target: $FULL_URL"
echo ""

# Test 1: HTTP Status Code
echo "[1/4] Checking HTTP status code..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FULL_URL" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✓ PASS${NC} - HTTP $HTTP_CODE"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "   ${RED}✗ FAIL${NC} - Connection failed (server not running?)"
    exit 1
else
    echo -e "   ${RED}✗ FAIL${NC} - HTTP $HTTP_CODE (expected 200)"
    exit 1
fi

# Test 2: Response is valid JSON
echo ""
echo "[2/4] Checking JSON validity..."
RESPONSE=$(curl -s "$FULL_URL" || echo '{}')

if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓ PASS${NC} - Valid JSON returned"
else
    echo -e "   ${RED}✗ FAIL${NC} - Response is not valid JSON"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Test 3: Required fields exist
echo ""
echo "[3/4] Checking required fields..."
REQUIRED_FIELDS=("delta_p95_pct" "delta_qps_pct" "error_rate_pct" "bullets")
ALL_FIELDS_OK=true

for field in "${REQUIRED_FIELDS[@]}"; do
    if echo "$RESPONSE" | jq -e ".$field" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} Field '$field' exists"
    else
        echo -e "   ${RED}✗${NC} Field '$field' missing"
        ALL_FIELDS_OK=false
    fi
done

if [ "$ALL_FIELDS_OK" = false ]; then
    echo -e "\n   ${RED}✗ FAIL${NC} - Missing required fields"
    exit 1
fi

# Test 4: Check .ok field and bullets array
echo ""
echo "[4/4] Checking response structure..."
OK_FIELD=$(echo "$RESPONSE" | jq -r '.ok // "null"')
BULLETS=$(echo "$RESPONSE" | jq -r '.bullets // []' 2>/dev/null)
BULLETS_COUNT=$(echo "$BULLETS" | jq 'length' 2>/dev/null || echo "0")

echo "   Status (.ok): $OK_FIELD"
echo "   Bullets count: $BULLETS_COUNT"

if [ "$BULLETS_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✓ PASS${NC} - Bullets array populated"
else
    echo -e "   ${YELLOW}⚠ WARN${NC} - Bullets array empty (acceptable for soft-fail)"
fi

# Summary
echo ""
echo "================================================================"
echo "SUMMARY"
echo "================================================================"
echo ""
echo "Endpoint: $ENDPOINT"
echo "HTTP Status: $HTTP_CODE"
echo "Response .ok: $OK_FIELD"
echo "Bullets: $BULLETS_COUNT item(s)"
echo ""

# Check for soft-fail mode
ERROR_FIELD=$(echo "$RESPONSE" | jq -r '.error // "none"')
MODE_FIELD=$(echo "$RESPONSE" | jq -r '.mode // "unknown"')

if [ "$ERROR_FIELD" != "none" ]; then
    echo -e "${YELLOW}ℹ${NC} Soft-fail detected:"
    echo "   Error: $ERROR_FIELD"
    echo "   Mode: $MODE_FIELD"
    echo ""
fi

echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
echo ""
echo "✓ No HTTP 500 errors"
echo "✓ Always returns HTTP 200 + JSON"
echo "✓ Soft-fail mode working correctly"
echo ""
echo "================================================================"
exit 0

