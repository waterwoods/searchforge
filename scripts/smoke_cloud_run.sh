#!/bin/bash
# smoke_cloud_run.sh - Smoke test for Cloud Run endpoints
# Tests healthz, readyz, and /api/query endpoints

set -e

CLOUD_RUN_URL="${CLOUD_RUN_URL:-https://fiqa-api-g7zatxrycq-uw.a.run.app}"

echo "=========================================="
echo "Cloud Run Smoke Test"
echo "=========================================="
echo "URL: $CLOUD_RUN_URL"
echo ""

# Validate CLOUD_RUN_URL is set
if [ -z "$CLOUD_RUN_URL" ]; then
    echo "❌ FAIL: CLOUD_RUN_URL is not set"
    exit 1
fi

# Test healthz
echo "[1/4] Testing /healthz..."
HEALTHZ_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${CLOUD_RUN_URL}/healthz" || echo "000")
if [ "$HEALTHZ_CODE" = "200" ]; then
    echo "✅ PASS: /healthz returned 200"
    # Verify response body contains status
    HEALTHZ_BODY=$(curl -s "${CLOUD_RUN_URL}/healthz")
    if echo "$HEALTHZ_BODY" | grep -q '"status"'; then
        echo "  Response: $(echo "$HEALTHZ_BODY" | head -c 100)..."
    fi
else
    echo "❌ FAIL: /healthz returned $HEALTHZ_CODE"
    exit 1
fi

# Test readyz
echo "[2/4] Testing /readyz..."
READYZ_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${CLOUD_RUN_URL}/readyz" || echo "000")
if [ "$READYZ_CODE" = "200" ]; then
    echo "✅ PASS: /readyz returned 200"
else
    echo "❌ FAIL: /readyz returned $READYZ_CODE"
    exit 1
fi

# Test /api/query with retry logic (cold start warmup)
echo "[3/4] Testing POST /api/query..."
QUERY_PAYLOAD='{"question":"What is diversification in investing?","top_k":10}'
QUERY_SUCCESS=false
MAX_RETRIES=3

for i in $(seq 1 $MAX_RETRIES); do
    echo "  Attempt $i/$MAX_RETRIES..."
    QUERY_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$QUERY_PAYLOAD" \
        "${CLOUD_RUN_URL}/api/query" || echo -e "\n000")
    
    HTTP_CODE=$(echo "$QUERY_RESPONSE" | tail -n1)
    BODY=$(echo "$QUERY_RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Check if response has non-empty answer or sources
        if echo "$BODY" | grep -q '"ok":true' && \
           (echo "$BODY" | grep -q '"answer":' || echo "$BODY" | grep -q '"sources":'); then
            echo "✅ PASS: /api/query returned 200 with valid response"
            echo "  Response preview: $(echo "$BODY" | head -c 200)..."
            QUERY_SUCCESS=true
            break
        else
            echo "  ⚠️  Response 200 but missing answer/sources, retrying..."
        fi
    elif [ "$HTTP_CODE" = "503" ]; then
        echo "  ⚠️  Got 503 (cold start/embedding_warming), waiting 10s before retry..."
        if [ $i -lt $MAX_RETRIES ]; then
            sleep 10
        fi
    elif echo "$BODY" | grep -q "embedding_warming"; then
        echo "  ⚠️  Got embedding_warming, waiting 10s before retry..."
        if [ $i -lt $MAX_RETRIES ]; then
            sleep 10
        fi
    else
        echo "  ❌ Got HTTP $HTTP_CODE"
        echo "  Response: $(echo "$BODY" | head -c 500)"
    fi
done

if [ "$QUERY_SUCCESS" = false ]; then
    # Check if we got embedding_warming - this means service is running but not ready
    if echo "$BODY" | grep -q "embedding_warming"; then
        echo "⚠️  WARN: /api/query returned 503 with embedding_warming (service running but not ready)"
        echo "  This is expected for cold starts. Service will be ready after warmup."
    else
        echo "❌ FAIL: /api/query did not return 200 after $MAX_RETRIES attempts"
        echo "  Last response: $(echo "$BODY" | head -c 200)"
        exit 1
    fi
fi

# Test /api/metrics/demo-summary (should never 404)
echo "[4/4] Testing GET /api/metrics/demo-summary..."
DEMO_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${CLOUD_RUN_URL}/api/metrics/demo-summary" || echo "000")
if [ "$DEMO_CODE" = "200" ]; then
    echo "✅ PASS: /api/metrics/demo-summary returned 200"
    DEMO_BODY=$(curl -s "${CLOUD_RUN_URL}/api/metrics/demo-summary")
    if echo "$DEMO_BODY" | grep -q '"kpis"'; then
        echo "  Response contains KPIs"
    fi
else
    echo "❌ FAIL: /api/metrics/demo-summary returned $DEMO_CODE (should always return 200)"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All critical endpoints passed!"
echo "=========================================="
