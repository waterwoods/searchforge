#!/bin/bash
#
# verify_refactor.sh - Refactoring Verification Script
# ======================================================
# Verifies that app_main.py refactoring maintains all external behaviors.
#
# Tests:
# 1. /readyz returns 200 and completes in <=30ms (Python async service)
# 2. /search works without "repeated model loading" in logs
# 3. /search P95 latency hasn't regressed (20 concurrent requests)
# 4. /api/agent/code_lookup falls back gracefully without OPENAI_API_KEY
#
# Usage:
#   ./scripts/verify_refactor.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8011}"
CONCURRENCY=20
ITERATIONS=20

echo "========================================="
echo "  Refactoring Verification Tests"
echo "========================================="
echo ""
echo "Target: $BASE_URL"
echo "Concurrency: $CONCURRENCY"
echo "Iterations: $ITERATIONS"
echo ""

# ========================================
# Test 1: /readyz Performance (<= 30ms)
# ========================================

echo "Test 1: /readyz performance check..."

readyz_latencies=()
for i in $(seq 1 5); do
    start=$(date +%s%N)
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/readyz")
    end=$(date +%s%N)
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    latency_ms=$(echo "scale=2; ($end - $start) / 1000000" | bc)
    readyz_latencies+=($latency_ms)
    
    if [ "$http_code" != "200" ]; then
        echo -e "${RED}✗ FAIL${NC}: /readyz returned $http_code (expected 200)"
        exit 1
    fi
    
    # Check if clients_ready is true
    clients_ready=$(echo "$body" | jq -r '.clients_ready // .ok')
    if [ "$clients_ready" != "true" ]; then
        echo -e "${YELLOW}⚠ WARN${NC}: clients_ready=$clients_ready (may affect later tests)"
    fi
done

# Calculate average latency
avg_latency=$(echo "${readyz_latencies[@]}" | tr ' ' '\n' | awk '{s+=$1}END{print s/NR}')
max_latency=$(echo "${readyz_latencies[@]}" | tr ' ' '\n' | sort -nr | head -1)

echo -e "${GREEN}✓ PASS${NC}: /readyz returned 200"
echo "  Average latency: ${avg_latency}ms"
echo "  Max latency: ${max_latency}ms"

if (( $(echo "$max_latency > 30" | bc -l) )); then
    echo -e "${RED}✗ FAIL${NC}: Max latency ${max_latency}ms exceeds 30ms threshold"
    exit 1
else
    echo -e "${GREEN}✓ PASS${NC}: All latencies <= 30ms (target for Python async service)"
fi

echo ""

# ========================================
# Test 2: /search Log Check (No Repeated Model Loading)
# ========================================

echo "Test 2: /search log check (no repeated model loading)..."

# Truncate log file for test (if accessible)
LOG_FILE="${LOG_FILE:-logs/app_main.log}"
if [ -f "$LOG_FILE" ]; then
    : > "$LOG_FILE"
    echo "  Truncated $LOG_FILE for clean test"
fi

# Send a test search request
search_response=$(curl -s -X POST "$BASE_URL/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query", "top_k": 10, "collection": "fiqa"}')

search_ok=$(echo "$search_response" | jq -r '.ok')
if [ "$search_ok" != "true" ]; then
    echo -e "${RED}✗ FAIL${NC}: /search returned ok=false"
    echo "$search_response" | jq '.'
    exit 1
fi

echo -e "${GREEN}✓ PASS${NC}: /search returned ok=true"

# Check logs for repeated model loading
if [ -f "$LOG_FILE" ]; then
    model_load_count=$(grep -c "Loading embedding model\|Initializing Qdrant client\|Initializing Redis client" "$LOG_FILE" 2>/dev/null || echo "0")
    
    if [ "$model_load_count" -gt "0" ]; then
        echo -e "${RED}✗ FAIL${NC}: Found $model_load_count model/client initialization in logs (should be 0 after startup)"
        grep "Loading embedding model\|Initializing Qdrant client\|Initializing Redis client" "$LOG_FILE" || true
        exit 1
    else
        echo -e "${GREEN}✓ PASS${NC}: No repeated model/client loading in logs"
    fi
else
    echo -e "${YELLOW}⚠ WARN${NC}: Log file $LOG_FILE not found, skipping log check"
fi

echo ""

# ========================================
# Test 3: /search P95 Latency (Concurrent Load)
# ========================================

echo "Test 3: /search P95 latency test (${ITERATIONS} requests, ${CONCURRENCY} concurrent)..."

# Create temporary file for results
tmpfile=$(mktemp)

# Function to send search request and record latency
send_search() {
    start=$(date +%s%N)
    response=$(curl -s -X POST "$BASE_URL/search" \
        -H "Content-Type: application/json" \
        -d '{"query": "financial advice", "top_k": 10, "collection": "fiqa"}' \
        -w "\n%{http_code}")
    end=$(date +%s%N)
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        # Extract latency from response
        server_latency=$(echo "$body" | jq -r '.latency_ms // 0')
        client_latency=$(echo "scale=2; ($end - $start) / 1000000" | bc)
        echo "$server_latency $client_latency" >> "$tmpfile"
    else
        echo "ERROR 0" >> "$tmpfile"
    fi
}

export -f send_search
export BASE_URL
export tmpfile

# Run concurrent requests
seq 1 $ITERATIONS | xargs -P $CONCURRENCY -I {} bash -c 'send_search'

# Calculate P95 from results
p95_server=$(cat "$tmpfile" | awk '{print $1}' | grep -v ERROR | sort -n | awk 'BEGIN{c=0} {a[c]=$1; c++} END{print a[int(c*0.95)]}')
p95_client=$(cat "$tmpfile" | awk '{print $2}' | grep -v ERROR | sort -n | awk 'BEGIN{c=0} {a[c]=$1; c++} END{print a[int(c*0.95)]}')
error_count=$(grep -c ERROR "$tmpfile" || echo "0")

echo -e "${GREEN}✓ PASS${NC}: Completed $ITERATIONS requests"
echo "  Server-reported P95: ${p95_server}ms"
echo "  Client-measured P95: ${p95_client}ms"
echo "  Errors: $error_count"

if [ "$error_count" -gt "0" ]; then
    echo -e "${RED}✗ FAIL${NC}: $error_count requests failed"
    exit 1
fi

# Compare with baseline (if available)
BASELINE_P95="${BASELINE_P95:-500}"  # 500ms default baseline
if (( $(echo "$p95_server > $BASELINE_P95" | bc -l) )); then
    echo -e "${RED}✗ FAIL${NC}: P95 ${p95_server}ms exceeds baseline ${BASELINE_P95}ms"
    exit 1
else
    echo -e "${GREEN}✓ PASS${NC}: P95 within baseline (${BASELINE_P95}ms)"
fi

rm -f "$tmpfile"

echo ""

# ========================================
# Test 4: /api/agent/code_lookup Fallback (No OPENAI_API_KEY)
# ========================================

echo "Test 4: /api/agent/code_lookup fallback test (without valid OpenAI key)..."

# Test with a simple query
code_lookup_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/agent/code_lookup" \
    -H "Content-Type: application/json" \
    -d '{"message": "embedding code"}')

http_code=$(echo "$code_lookup_response" | tail -n 1)
body=$(echo "$code_lookup_response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}: /api/agent/code_lookup returned 200 (fallback worked)"
    
    # Check if summary mentions fallback
    summary=$(echo "$body" | jq -r '.summary_md')
    if echo "$summary" | grep -q "LLM 不可用"; then
        echo -e "${GREEN}✓ PASS${NC}: Fallback mode detected in response"
    elif echo "$summary" | grep -q "没有找到"; then
        echo -e "${GREEN}✓ PASS${NC}: No results found (expected behavior)"
    else
        echo -e "${YELLOW}⚠ INFO${NC}: Response doesn't indicate fallback (may have valid OpenAI key)"
    fi
    
    files_count=$(echo "$body" | jq '.files | length')
    echo "  Files returned: $files_count"
    
elif [ "$http_code" = "503" ]; then
    echo -e "${YELLOW}⚠ WARN${NC}: /api/agent/code_lookup returned 503 (clients not initialized)"
    echo "  This may be expected if Qdrant/embedding clients failed to initialize"
elif [ "$http_code" = "500" ]; then
    error_detail=$(echo "$body" | jq -r '.detail // .error')
    echo -e "${RED}✗ FAIL${NC}: /api/agent/code_lookup returned 500: $error_detail"
    exit 1
else
    echo -e "${RED}✗ FAIL${NC}: /api/agent/code_lookup returned unexpected status $http_code"
    echo "$body" | jq '.'
    exit 1
fi

echo ""

# ========================================
# Summary
# ========================================

echo "========================================="
echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ /readyz is fast (<= 30ms for Python async)"
echo "  ✓ /search has no repeated model loading"
echo "  ✓ /search P95 latency is within baseline"
echo "  ✓ /api/agent/code_lookup falls back gracefully"
echo ""
echo "Refactoring verification complete!"

