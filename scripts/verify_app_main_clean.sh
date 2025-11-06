#!/usr/bin/env bash
# verify_app_main_clean.sh - Comprehensive verification for app_main deproxy & graceful degradation
# 
# Usage:
#   ./scripts/verify_app_main_clean.sh [BASE_URL]
#
# Example:
#   ./scripts/verify_app_main_clean.sh http://localhost:8011

set -euo pipefail

BASE_URL="${1:-http://localhost:8011}"
REPORT_FILE="reports/APP_MAIN_CLEAN_VERIFY.md"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

echo "========================================="
echo "App Main Clean Verification"
echo "========================================="
echo "Target: $BASE_URL"
echo "Report: $REPORT_FILE"
echo ""

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASS_COUNT++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARN_COUNT++))
}

# Check if app_main is reachable
echo "[1/10] Checking app_main reachability..."
if curl -sf "$BASE_URL/healthz" > /dev/null; then
    pass "app_main is reachable at $BASE_URL"
else
    fail "app_main is NOT reachable at $BASE_URL"
    echo "Aborting test suite."
    exit 1
fi
echo ""

# Test 1: /ops/verify shows proxy_to_v2 == false
echo "[2/10] Testing /ops/verify for proxy_to_v2 flag..."
VERIFY_RESP=$(curl -sf "$BASE_URL/ops/verify" || echo '{"ok":false}')
PROXY_V2=$(echo "$VERIFY_RESP" | jq -r '.proxy_to_v2 // "missing"')

if [[ "$PROXY_V2" == "false" ]]; then
    pass "/ops/verify shows proxy_to_v2: false"
else
    fail "/ops/verify proxy_to_v2 is $PROXY_V2 (expected: false)"
fi
echo ""

# Test 2: /ops/verify shows data_sources (Qdrant/Redis)
echo "[3/10] Testing /ops/verify for data_sources structure..."
QDRANT_OK=$(echo "$VERIFY_RESP" | jq -r '.data_sources.qdrant.ok // "missing"')
REDIS_OK=$(echo "$VERIFY_RESP" | jq -r '.data_sources.redis.ok // "missing"')

if [[ "$QDRANT_OK" != "missing" && "$REDIS_OK" != "missing" ]]; then
    pass "/ops/verify includes data_sources (qdrant.ok=$QDRANT_OK, redis.ok=$REDIS_OK)"
else
    fail "/ops/verify missing data_sources structure"
fi
echo ""

# Test 3: /ops/qdrant/stats returns ok:true or ok:false (never 5xx)
echo "[4/10] Testing /ops/qdrant/stats for graceful degradation..."
STATS_HTTP=$(curl -sf -o /tmp/qdrant_stats.json -w "%{http_code}" "$BASE_URL/ops/qdrant/stats" || echo "000")
STATS_OK=$(jq -r '.ok // "missing"' /tmp/qdrant_stats.json 2>/dev/null || echo "missing")

if [[ "$STATS_HTTP" == "200" ]]; then
    if [[ "$STATS_OK" == "true" || "$STATS_OK" == "false" ]]; then
        pass "/ops/qdrant/stats returns 200 with ok:$STATS_OK"
    else
        warn "/ops/qdrant/stats returns 200 but ok field is missing or invalid"
    fi
else
    fail "/ops/qdrant/stats returned HTTP $STATS_HTTP (expected: 200)"
fi
echo ""

# Test 4: /ops/qdrant/stats structure (has all required fields)
echo "[5/10] Testing /ops/qdrant/stats structure..."
STATS_HITS=$(jq -r '.hits_60s // "missing"' /tmp/qdrant_stats.json 2>/dev/null || echo "missing")
STATS_P95=$(jq -r '.p95_query_ms_60s // "null"' /tmp/qdrant_stats.json 2>/dev/null || echo "missing")

if [[ "$STATS_HITS" != "missing" && "$STATS_P95" != "missing" ]]; then
    pass "/ops/qdrant/stats has complete structure (hits_60s=$STATS_HITS, p95_query_ms_60s=$STATS_P95)"
else
    fail "/ops/qdrant/stats missing required fields"
fi
echo ""

# Test 5: /ops/qa/feed returns ok:true or ok:false (never 5xx)
echo "[6/10] Testing /ops/qa/feed for graceful degradation..."
FEED_HTTP=$(curl -sf -o /tmp/qa_feed.json -w "%{http_code}" "$BASE_URL/ops/qa/feed?limit=5" || echo "000")
FEED_OK=$(jq -r '.ok // "missing"' /tmp/qa_feed.json 2>/dev/null || echo "missing")

if [[ "$FEED_HTTP" == "200" ]]; then
    if [[ "$FEED_OK" == "true" || "$FEED_OK" == "false" ]]; then
        pass "/ops/qa/feed returns 200 with ok:$FEED_OK"
    else
        warn "/ops/qa/feed returns 200 but ok field is missing or invalid"
    fi
else
    fail "/ops/qa/feed returned HTTP $FEED_HTTP (expected: 200)"
fi
echo ""

# Test 6: /ops/qa/feed has items array (empty is ok)
echo "[7/10] Testing /ops/qa/feed structure..."
FEED_ITEMS=$(jq -r '.items | type' /tmp/qa_feed.json 2>/dev/null || echo "missing")

if [[ "$FEED_ITEMS" == "array" ]]; then
    FEED_COUNT=$(jq -r '.items | length' /tmp/qa_feed.json)
    pass "/ops/qa/feed has items array (count: $FEED_COUNT)"
else
    fail "/ops/qa/feed missing items array"
fi
echo ""

# Test 7: /ops/summary returns 200 even if degraded
echo "[8/10] Testing /ops/summary for graceful degradation..."
SUMMARY_HTTP=$(curl -sf -o /tmp/summary.json -w "%{http_code}" "$BASE_URL/ops/summary" || echo "000")
SUMMARY_OK=$(jq -r '.ok // "missing"' /tmp/summary.json 2>/dev/null || echo "missing")

if [[ "$SUMMARY_HTTP" == "200" ]]; then
    pass "/ops/summary returns 200 (ok:$SUMMARY_OK)"
else
    fail "/ops/summary returned HTTP $SUMMARY_HTTP (expected: 200)"
fi
echo ""

# Test 8: /readyz shows data_sources
echo "[9/10] Testing /readyz for data_sources..."
READYZ_RESP=$(curl -sf "$BASE_URL/readyz" || echo '{"ok":false}')
READYZ_QDRANT=$(echo "$READYZ_RESP" | jq -r '.data_sources.qdrant.ok // "missing"')
READYZ_REDIS=$(echo "$READYZ_RESP" | jq -r '.data_sources.redis.ok // "missing"')

if [[ "$READYZ_QDRANT" != "missing" && "$READYZ_REDIS" != "missing" ]]; then
    pass "/readyz includes data_sources (qdrant.ok=$READYZ_QDRANT, redis.ok=$READYZ_REDIS)"
else
    fail "/readyz missing data_sources structure"
fi
echo ""

# Test 9: No endpoints return 500/503 errors
echo "[10/10] Testing all endpoints for no 5xx errors..."
ENDPOINTS=(
    "/ops/verify"
    "/ops/summary"
    "/ops/qdrant/ping"
    "/ops/qdrant/config"
    "/ops/qdrant/stats"
    "/ops/qa/feed"
    "/ops/query_bank/status"
    "/ops/black_swan/status"
    "/ops/black_swan/config"
    "/readyz"
)

HAS_5XX=false
for endpoint in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" || echo "000")
    if [[ "$HTTP_CODE" =~ ^5 ]]; then
        fail "$endpoint returned HTTP $HTTP_CODE"
        HAS_5XX=true
    fi
done

if [[ "$HAS_5XX" == "false" ]]; then
    pass "No endpoints returned 5xx errors"
fi
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}PASS: $PASS_COUNT${NC}"
echo -e "${RED}FAIL: $FAIL_COUNT${NC}"
echo -e "${YELLOW}WARN: $WARN_COUNT${NC}"
echo ""

# Generate report file
echo "Generating report: $REPORT_FILE"
mkdir -p reports

cat > "$REPORT_FILE" <<EOF
# App Main Clean Verification Report
**Generated**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")  
**Target**: \`$BASE_URL\`  
**Status**: $(if [[ $FAIL_COUNT -eq 0 ]]; then echo "✅ **PASSED**"; else echo "❌ **FAILED**"; fi)

---

## Test Results

- ✅ **PASS**: $PASS_COUNT
- ❌ **FAIL**: $FAIL_COUNT
- ⚠️  **WARN**: $WARN_COUNT

---

## 1. /ops/verify Response

\`\`\`json
$(echo "$VERIFY_RESP" | jq '.')
\`\`\`

### Key Findings:
- **proxy_to_v2**: \`$PROXY_V2\` (Expected: \`false\`)
- **Qdrant Status**: \`$QDRANT_OK\`
- **Redis Status**: \`$REDIS_OK\`

---

## 2. /ops/qdrant/stats Response

**HTTP Status**: $STATS_HTTP

\`\`\`json
$(cat /tmp/qdrant_stats.json | jq '.' 2>/dev/null || echo '{}')
\`\`\`

### Structure Validation:
- **ok**: \`$STATS_OK\`
- **hits_60s**: \`$STATS_HITS\`
- **p95_query_ms_60s**: \`$STATS_P95\`

---

## 3. /ops/qa/feed Response

**HTTP Status**: $FEED_HTTP

\`\`\`json
$(cat /tmp/qa_feed.json | jq '.' 2>/dev/null || echo '{}')
\`\`\`

### Structure Validation:
- **ok**: \`$FEED_OK\`
- **items type**: \`$FEED_ITEMS\`
- **items count**: \`$(jq -r '.items | length' /tmp/qa_feed.json 2>/dev/null || echo 0)\`

---

## 4. /ops/summary Response

**HTTP Status**: $SUMMARY_HTTP

\`\`\`json
$(cat /tmp/summary.json | jq '.' 2>/dev/null || echo '{}')
\`\`\`

---

## 5. /readyz Response

\`\`\`json
$(echo "$READYZ_RESP" | jq '.')
\`\`\`

### Data Sources:
- **Qdrant**: \`$READYZ_QDRANT\`
- **Redis**: \`$READYZ_REDIS\`

---

## 6. HTTP Status Code Validation

All tested endpoints:

| Endpoint | HTTP Status | Status |
|----------|-------------|--------|
EOF

for endpoint in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "| \`$endpoint\` | $HTTP_CODE | ✅ OK |" >> "$REPORT_FILE"
    elif [[ "$HTTP_CODE" =~ ^5 ]]; then
        echo "| \`$endpoint\` | $HTTP_CODE | ❌ 5xx ERROR |" >> "$REPORT_FILE"
    else
        echo "| \`$endpoint\` | $HTTP_CODE | ⚠️  Non-200 |" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" <<EOF

---

## Acceptance Criteria

- [$(if [[ "$PROXY_V2" == "false" ]]; then echo "x"; else echo " "; fi))] **No proxy to app_v2**: \`/ops/verify\` shows \`proxy_to_v2: false\`
- [$(if [[ "$QDRANT_OK" != "missing" ]]; then echo "x"; else echo " "; fi))] **Qdrant status visible**: \`/ops/verify\` and \`/readyz\` include Qdrant status
- [$(if [[ "$REDIS_OK" != "missing" ]]; then echo "x"; else echo " "; fi))] **Redis status visible**: \`/ops/verify\` and \`/readyz\` include Redis status
- [$(if [[ "$STATS_HTTP" == "200" ]]; then echo "x"; else echo " "; fi))] **Graceful degradation**: \`/ops/qdrant/stats\` returns 200 (even if degraded)
- [$(if [[ "$FEED_HTTP" == "200" ]]; then echo "x"; else echo " "; fi))] **Graceful degradation**: \`/ops/qa/feed\` returns 200 (even if degraded)
- [$(if [[ "$HAS_5XX" == "false" ]]; then echo "x"; else echo " "; fi))] **No 5xx errors**: All endpoints return 200 (with \`ok:true\` or \`ok:false\`)

---

## Conclusion

$(if [[ $FAIL_COUNT -eq 0 ]]; then
    echo "✅ **All tests passed.** app_main is now fully deproxied and uses direct Qdrant/Redis connections with graceful degradation."
else
    echo "❌ **$FAIL_COUNT test(s) failed.** Please review the findings above and fix the issues."
fi)

$(if [[ $WARN_COUNT -gt 0 ]]; then
    echo ""
    echo "⚠️  **$WARN_COUNT warning(s) detected.** Review for potential issues."
fi)

---

**Next Steps**:
1. Review this report
2. Fix any failing tests
3. Re-run verification: \`./scripts/verify_app_main_clean.sh $BASE_URL\`
4. Once all tests pass, proceed with frontend integration testing

EOF

echo "Report written to: $REPORT_FILE"
echo ""

# Exit with failure if any tests failed
if [[ $FAIL_COUNT -gt 0 ]]; then
    echo -e "${RED}Verification FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}Verification PASSED${NC}"
    exit 0
fi

