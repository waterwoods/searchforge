#!/bin/bash
# qa_feature_guard.sh - Validation script for QA Feed and Qdrant Stats feature
# Usage: ./scripts/qa_feature_guard.sh [API_BASE]

set -e

API_BASE=${1:-"http://localhost:8001"}
PASS=0
FAIL=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[GUARD]${NC} $1"
}

pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    fail "jq is not installed. Please install: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

log "QA Feature Guard - Validating Qdrant Stats + QA Feed"
log "Target API: $API_BASE"
echo ""

# ========================================
# Test 1: Qdrant Stats Endpoint
# ========================================
log "Test 1: GET /ops/qdrant/stats"
STATS_RESP=$(curl -s "$API_BASE/ops/qdrant/stats")
STATS_OK=$(echo "$STATS_RESP" | jq -r '.ok // false')

if [ "$STATS_OK" = "true" ]; then
    pass "Qdrant stats endpoint responded OK"
    
    # Check schema
    HITS=$(echo "$STATS_RESP" | jq -r '.hits_60s // "null"')
    REMOTE_PCT=$(echo "$STATS_RESP" | jq -r '.remote_pct // "null"')
    CACHE_PCT=$(echo "$STATS_RESP" | jq -r '.cache_pct // "null"')
    AVG_RERANK=$(echo "$STATS_RESP" | jq -r '.avg_rerank_k // "null"')
    LAST_HIT=$(echo "$STATS_RESP" | jq -r '.last_hit_ts // "null"')
    
    if [ "$HITS" != "null" ] && [ "$REMOTE_PCT" != "null" ] && [ "$CACHE_PCT" != "null" ] && [ "$AVG_RERANK" != "null" ]; then
        pass "Qdrant stats schema valid: hits=$HITS, remote=$REMOTE_PCT%, cache=$CACHE_PCT%, avg_rerank=$AVG_RERANK"
    else
        fail "Qdrant stats schema incomplete: $STATS_RESP"
    fi
elif [ "$STATS_OK" = "false" ]; then
    ERROR=$(echo "$STATS_RESP" | jq -r '.error // "unknown"')
    if [ "$ERROR" = "QA_STATS_ENABLED=false" ]; then
        warn "Qdrant stats disabled (QA_STATS_ENABLED=false). Enable to pass this test."
    else
        fail "Qdrant stats endpoint error: $ERROR"
    fi
else
    fail "Qdrant stats endpoint unreachable or invalid response"
fi

echo ""

# ========================================
# Test 2: QA Feed Endpoint
# ========================================
log "Test 2: GET /ops/qa/feed"
FEED_RESP=$(curl -s "$API_BASE/ops/qa/feed?limit=10")
FEED_OK=$(echo "$FEED_RESP" | jq -r '.ok // false')

if [ "$FEED_OK" = "true" ]; then
    pass "QA feed endpoint responded OK"
    
    # Check schema
    ITEMS_COUNT=$(echo "$FEED_RESP" | jq -r '.items | length')
    CIRCUIT_OPEN=$(echo "$FEED_RESP" | jq -r '.circuit_open // false')
    SAMPLE_RATE=$(echo "$FEED_RESP" | jq -r '.sample_rate // "null"')
    EFFECTIVE_RATE=$(echo "$FEED_RESP" | jq -r '.sample_rate_effective // "null"')
    
    if [ "$SAMPLE_RATE" != "null" ] && [ "$EFFECTIVE_RATE" != "null" ]; then
        pass "QA feed schema valid: items=$ITEMS_COUNT, circuit=$CIRCUIT_OPEN, rate=$SAMPLE_RATE, effective=$EFFECTIVE_RATE"
    else
        fail "QA feed schema incomplete: $FEED_RESP"
    fi
    
    # Check items structure (if any)
    if [ "$ITEMS_COUNT" -gt 0 ]; then
        FIRST_ITEM=$(echo "$FEED_RESP" | jq -r '.items[0]')
        HAS_TS=$(echo "$FIRST_ITEM" | jq -r '.ts // "null"')
        HAS_MODE=$(echo "$FIRST_ITEM" | jq -r '.mode // "null"')
        HAS_LATENCY=$(echo "$FIRST_ITEM" | jq -r '.latency_ms // "null"')
        HAS_HIT_FROM=$(echo "$FIRST_ITEM" | jq -r '.hit_from // "null"')
        HAS_QUERY=$(echo "$FIRST_ITEM" | jq -r '.query // "null"')
        HAS_ANSWER=$(echo "$FIRST_ITEM" | jq -r '.answer // "null"')
        
        if [ "$HAS_TS" != "null" ] && [ "$HAS_MODE" != "null" ] && [ "$HAS_LATENCY" != "null" ] && [ "$HAS_HIT_FROM" != "null" ]; then
            pass "QA feed item schema valid: ts=$HAS_TS, mode=$HAS_MODE, latency=$HAS_LATENCY, hit_from=$HAS_HIT_FROM"
            
            # Check text masking (query/answer should be truncated)
            QUERY_LEN=${#HAS_QUERY}
            ANSWER_LEN=${#HAS_ANSWER}
            if [ "$QUERY_LEN" -le 120 ] && [ "$ANSWER_LEN" -le 200 ]; then
                pass "QA feed text truncation working: query_len=$QUERY_LEN, answer_len=$ANSWER_LEN"
            else
                warn "QA feed text may not be truncated properly: query_len=$QUERY_LEN (max 120), answer_len=$ANSWER_LEN (max 200)"
            fi
        else
            fail "QA feed item schema incomplete"
        fi
    else
        warn "QA feed has no items yet (may need traffic to populate)"
    fi
    
    # Check circuit breaker state
    if [ "$CIRCUIT_OPEN" = "true" ]; then
        warn "QA feed circuit breaker is OPEN - sampling paused due to budget violations"
    fi
    
elif [ "$FEED_OK" = "false" ]; then
    ERROR=$(echo "$FEED_RESP" | jq -r '.error // "unknown"')
    if [ "$ERROR" = "QA_FEED_ENABLED=false" ]; then
        warn "QA feed disabled (QA_FEED_ENABLED=false). Enable to test this feature."
    else
        fail "QA feed endpoint error: $ERROR"
    fi
else
    fail "QA feed endpoint unreachable or invalid response"
fi

echo ""

# ========================================
# Test 3: QA Feed NDJSON Download
# ========================================
log "Test 3: GET /ops/qa/feed.ndjson"
NDJSON_RESP=$(curl -s -I "$API_BASE/ops/qa/feed.ndjson")
NDJSON_STATUS=$(echo "$NDJSON_RESP" | grep -i "HTTP" | awk '{print $2}')

if [ "$NDJSON_STATUS" = "200" ]; then
    pass "QA feed NDJSON endpoint reachable (HTTP 200)"
    
    # Check content-type
    CONTENT_TYPE=$(echo "$NDJSON_RESP" | grep -i "content-type" | awk '{print $2}' | tr -d '\r')
    if [[ "$CONTENT_TYPE" == *"ndjson"* ]] || [[ "$CONTENT_TYPE" == *"json"* ]]; then
        pass "QA feed NDJSON content-type valid: $CONTENT_TYPE"
    else
        warn "QA feed NDJSON content-type unexpected: $CONTENT_TYPE"
    fi
    
    # Check content-disposition
    CONTENT_DISP=$(echo "$NDJSON_RESP" | grep -i "content-disposition")
    if [[ "$CONTENT_DISP" == *"attachment"* ]] && [[ "$CONTENT_DISP" == *"qa_feed"* ]]; then
        pass "QA feed NDJSON content-disposition valid (attachment)"
    else
        warn "QA feed NDJSON content-disposition may be missing or invalid"
    fi
    
elif [ "$NDJSON_STATUS" = "503" ]; then
    warn "QA feed NDJSON endpoint unavailable (HTTP 503) - likely QA_FEED_ENABLED=false"
else
    fail "QA feed NDJSON endpoint error (HTTP $NDJSON_STATUS)"
fi

echo ""

# ========================================
# Test 4: Enqueue Budget Check (Sanity)
# ========================================
log "Test 4: Enqueue budget sanity check"
log "Simulating 10 QA feed polls to check overhead..."

START_TIME=$(date +%s%3N)
for i in {1..10}; do
    curl -s "$API_BASE/ops/qa/feed?limit=20" > /dev/null
done
END_TIME=$(date +%s%3N)

TOTAL_MS=$((END_TIME - START_TIME))
AVG_MS=$((TOTAL_MS / 10))

if [ "$AVG_MS" -lt 50 ]; then
    pass "Average poll latency: ${AVG_MS}ms (< 50ms baseline)"
elif [ "$AVG_MS" -lt 100 ]; then
    warn "Average poll latency: ${AVG_MS}ms (50-100ms, acceptable but high)"
else
    fail "Average poll latency: ${AVG_MS}ms (> 100ms, may indicate performance issue)"
fi

echo ""

# ========================================
# Summary
# ========================================
TOTAL=$((PASS + FAIL))
echo "========================================"
if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed ($PASS/$TOTAL)${NC}"
    echo "QA Feed and Qdrant Stats feature is working correctly."
    exit 0
else
    echo -e "${RED}✗ Some tests failed ($FAIL failed, $PASS passed out of $TOTAL)${NC}"
    echo "Review failures above and check configuration (.env) or backend logs."
    exit 1
fi

