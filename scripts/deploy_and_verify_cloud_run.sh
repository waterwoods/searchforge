#!/usr/bin/env bash
# Complete Cloud Run deployment and verification script
# Handles all steps: env check, preflight, deploy, health checks, query test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Cloud Run Deployment and Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 0: Snapshot current status
echo "Step 0: Snapshot current /readyz status..."
CURRENT_READYZ=$(curl -sS https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz 2>/dev/null || echo '{"ok":false,"error":"unreachable"}')
echo "$CURRENT_READYZ" | python3 -m json.tool 2>/dev/null || echo "$CURRENT_READYZ"
echo ""

# Step 1: Check required env vars
echo "Step 1: Checking required environment variables..."
if ! bash "$SCRIPT_DIR/check_env_vars.sh"; then
    echo ""
    echo "Please set the required environment variables:"
    echo "  export QDRANT_URL=..."
    echo "  export QDRANT_API_KEY=..."
    echo "  export QDRANT_COLLECTION=..."
    echo "  export GCP_PROJECT=..."
    echo "  export GCP_REGION=..."
    echo ""
    echo "Or source from a .env file:"
    echo "  source .env.cloudrun"
    exit 1
fi

# Set DEMO_MODE
export DEMO_MODE=true
echo "✅ DEMO_MODE=true (for retrieval-only mode)"
echo ""

# Step 2: Preflight check
echo "Step 2: Preflight - Verifying Qdrant Cloud connectivity..."
if ! python3 "$SCRIPT_DIR/verify_qdrant_cloud.py"; then
    echo ""
    echo -e "${RED}❌ Qdrant Cloud preflight check failed${NC}"
    echo "   Please verify:"
    echo "   1. QDRANT_URL is correct"
    echo "   2. QDRANT_API_KEY is valid"
    echo "   3. QDRANT_COLLECTION exists"
    echo "   4. Network connectivity to Qdrant Cloud"
    exit 1
fi
echo ""

# Step 3: Deploy
echo "Step 3: Deploying to Cloud Run..."
if ! bash "$SCRIPT_DIR/deploy_rag_demo.sh"; then
    echo ""
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Capture service URL from deploy script output or gcloud
SERVICE_NAME="${SERVICE_NAME:-fiqa-api}"
GCP_PROJECT="${GCP_PROJECT:-${PROJECT_ID:-optimal-disk-472305-e2}}"
GCP_REGION="${GCP_REGION:-${REGION:-us-west1}}"

CLOUD_RUN_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$GCP_REGION" \
    --project "$GCP_PROJECT" \
    --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$CLOUD_RUN_URL" ]; then
    echo -e "${RED}❌ Failed to get service URL${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment complete${NC}"
echo "   Service URL: $CLOUD_RUN_URL"
echo ""

# Step 4: Health checks with retries
echo "Step 4: Waiting for service readiness (max 3 minutes)..."
MAX_TRIES=18
SLEEP_SEC=10
LIVE_OK=false
READYZ_OK=false

for i in $(seq 1 $MAX_TRIES); do
    echo -n "  Attempt $i/$MAX_TRIES: "
    
    # Liveness: /healthz is intercepted at Google’s Cloud Run edge (404 HTML). Prefer /health/live.
    if curl -sf --max-time 10 "${CLOUD_RUN_URL}/health/live" > /dev/null 2>&1; then
        LIVE_OK=true
        echo -n "live=OK "
    elif curl -sf --max-time 10 "${CLOUD_RUN_URL}/api/healthz" > /dev/null 2>&1; then
        LIVE_OK=true
        echo -n "api_healthz=OK "
    elif curl -sf --max-time 10 "${CLOUD_RUN_URL}/healthz" > /dev/null 2>&1; then
        LIVE_OK=true
        echo -n "healthz=OK "
    else
        echo -n "live=FAIL "
    fi
    
    # Check /readyz
    READYZ_RESPONSE=$(curl -sS --max-time 10 "${CLOUD_RUN_URL}/readyz" 2>/dev/null || echo '{"ok":false}')
    READYZ_OK_VAL=$(echo "$READYZ_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "false")
    
    if [ "$READYZ_OK_VAL" = "True" ] || [ "$READYZ_OK_VAL" = "true" ]; then
        READYZ_OK=true
        echo "readyz=OK"
        echo ""
        echo "✅ Service is ready!"
        echo "$READYZ_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$READYZ_RESPONSE"
        break
    else
        echo "readyz=NOT_READY"
        if [ $i -lt $MAX_TRIES ]; then
            sleep $SLEEP_SEC
        fi
    fi
done

if [ "$READYZ_OK" != "true" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  /readyz still not ready after $MAX_TRIES attempts${NC}"
    echo "   Fetching recent logs..."
    echo ""
    gcloud run services logs read "$SERVICE_NAME" \
        --region "$GCP_REGION" \
        --project "$GCP_PROJECT" \
        --limit 100 2>/dev/null | tail -50 || echo "Failed to fetch logs"
    echo ""
    echo "   Common issues:"
    echo "   - Qdrant connection/auth failure (check QDRANT_URL and QDRANT_API_KEY)"
    echo "   - Network connectivity issues"
    echo "   - Missing environment variables"
    echo ""
fi

# Step 5: Query endpoint verification
echo "Step 5: Testing query endpoint..."
QUERY_TESTS=(
    "what is diversification"
    "risk premium"
    "bond duration"
)

QUERY_OK=false
for query_text in "${QUERY_TESTS[@]}"; do
    echo ""
    echo "  Testing query: \"$query_text\""
    QUERY_RESPONSE=$(curl -sS -X POST "${CLOUD_RUN_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$query_text\",\"top_k\":5}" \
        --max-time 30 2>/dev/null || echo '{"ok":false}')
    
    # Check if response has results
    HAS_RESULTS=$(echo "$QUERY_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('ok') and (data.get('sources') or data.get('items')):
        results = data.get('sources') or data.get('items') or []
        if len(results) > 0:
            # Check if result has doc_id or id and text/snippet
            first = results[0]
            has_id = 'doc_id' in first or 'id' in first
            has_text = 'text' in first or 'snippet' in first or 'content' in first
            print('true' if (has_id and has_text) else 'false')
        else:
            print('false')
    else:
        print('false')
except:
    print('false')
" 2>/dev/null || echo "false")
    
    if [ "$HAS_RESULTS" = "true" ]; then
        QUERY_OK=true
        echo -e "  ${GREEN}✅ Query successful - results returned${NC}"
        # Show first result summary (safe, no secrets)
        echo "$QUERY_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('sources') or data.get('items') or []
    if results:
        first = results[0]
        doc_id = first.get('doc_id') or first.get('id', 'N/A')
        title = first.get('title', 'N/A')[:60]
        print(f'    First result: doc_id={doc_id}, title={title}...')
except:
    pass
" 2>/dev/null || true
        break
    else
        echo -e "  ${YELLOW}⚠️  No results returned${NC}"
    fi
done

# Step 6: Final checklist
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Final Checklist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$LIVE_OK" = "true" ]; then
    echo -e "${GREEN}✅ Liveness returns 200 (/health/live or /api/healthz)${NC}"
else
    echo -e "${RED}❌ Liveness failed (/health/live and fallbacks)${NC}"
fi

if [ "$READYZ_OK" = "true" ]; then
    echo -e "${GREEN}✅ /readyz returns ok:true${NC}"
else
    echo -e "${RED}❌ /readyz not ready${NC}"
fi

if [ "$QUERY_OK" = "true" ]; then
    echo -e "${GREEN}✅ /api/query returns hits${NC}"
else
    echo -e "${RED}❌ /api/query failed or returned no results${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Service URL: $CLOUD_RUN_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Exit with appropriate code
if [ "$LIVE_OK" = "true" ] && [ "$READYZ_OK" = "true" ] && [ "$QUERY_OK" = "true" ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed${NC}"
    exit 1
fi
