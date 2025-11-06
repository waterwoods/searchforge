#!/bin/bash
# Black Swan Hard Mode Test Script
# Tests the enhanced Black Swan functionality with real Qdrant hits

set -euo pipefail

API_BASE="http://localhost:8001"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Black Swan Hard Mode Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if backend is running
log_info "1️⃣  Checking backend connectivity..."
if ! curl -s -f "$API_BASE/ops/summary" > /dev/null; then
    log_error "Backend not reachable at $API_BASE"
    exit 1
fi
log_success "Backend is running"

# Check Black Swan config
log_info "2️⃣  Checking Black Swan Hard Mode configuration..."
CONFIG=$(curl -s "$API_BASE/ops/black_swan/config")
USE_REAL=$(echo "$CONFIG" | jq -r '.use_real // false')
NOCACHE=$(echo "$CONFIG" | jq -r '.nocache // false')

if [[ "$USE_REAL" == "true" && "$NOCACHE" == "true" ]]; then
    log_success "Hard Mode enabled: use_real=$USE_REAL, nocache=$NOCACHE"
else
    log_error "Hard Mode not properly configured: use_real=$USE_REAL, nocache=$NOCACHE"
    exit 1
fi

# Check Qdrant connectivity
log_info "3️⃣  Checking Qdrant connectivity..."
QDRANT_STATUS=$(curl -s "$API_BASE/ops/qdrant/ping")
QDRANT_OK=$(echo "$QDRANT_STATUS" | jq -r '.ok // false')

if [[ "$QDRANT_OK" == "true" ]]; then
    COLLECTIONS=$(echo "$QDRANT_STATUS" | jq -r '.collections | length')
    log_success "Qdrant connected with $COLLECTIONS collections"
else
    log_error "Qdrant not reachable"
    exit 1
fi

# Trigger Mode A test
log_info "4️⃣  Triggering Hard Mode A test..."
RESPONSE=$(curl -s -X POST "$API_BASE/ops/black_swan" \
    -H "Content-Type: application/json" \
    -d '{"mode":"A"}')

RUN_ID=$(echo "$RESPONSE" | jq -r '.run_id // empty')
if [[ -z "$RUN_ID" ]]; then
    log_error "Failed to start Black Swan test"
    echo "Response: $RESPONSE"
    exit 1
fi

log_success "Black Swan Mode A started with run_id: $RUN_ID"

# Monitor progress
log_info "5️⃣  Monitoring test progress..."
PHASE="starting"
PROGRESS=0
QDRANT_HITS=0
MAX_WAIT=180  # 3 minutes max wait
WAIT_COUNT=0

while [[ $WAIT_COUNT -lt $MAX_WAIT ]]; do
    STATUS=$(curl -s "$API_BASE/ops/black_swan/status")
    CURRENT_PHASE=$(echo "$STATUS" | jq -r '.phase // "unknown"')
    CURRENT_PROGRESS=$(echo "$STATUS" | jq -r '.progress // 0')
    RUNNING=$(echo "$STATUS" | jq -r '.running // false')
    
    # Get Qdrant hits
    QDRANT_STATS=$(curl -s "$API_BASE/ops/qdrant/stats")
    CURRENT_HITS=$(echo "$QDRANT_STATS" | jq -r '.hits // 0')
    
    if [[ "$CURRENT_PHASE" != "$PHASE" ]] || [[ "$CURRENT_PROGRESS" != "$PROGRESS" ]] || [[ "$CURRENT_HITS" != "$QDRANT_HITS" ]]; then
        log_info "Phase: $CURRENT_PHASE | Progress: $CURRENT_PROGRESS% | Qdrant Hits: $CURRENT_HITS"
        PHASE="$CURRENT_PHASE"
        PROGRESS="$CURRENT_PROGRESS"
        QDRANT_HITS="$CURRENT_HITS"
    fi
    
    if [[ "$RUNNING" == "false" ]]; then
        break
    fi
    
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
done

if [[ $WAIT_COUNT -ge $MAX_WAIT ]]; then
    log_error "Test timed out after $MAX_WAIT seconds"
    exit 1
fi

# Final status check
FINAL_STATUS=$(curl -s "$API_BASE/ops/black_swan/status")
FINAL_PHASE=$(echo "$FINAL_STATUS" | jq -r '.phase // "unknown"')
FINAL_HITS=$(curl -s "$API_BASE/ops/qdrant/stats" | jq -r '.hits // 0')

log_info "6️⃣  Test completed with phase: $FINAL_PHASE"

# Validation checks
log_info "7️⃣  Running acceptance tests..."

# Check 1: Qdrant hits >= 200
if [[ $FINAL_HITS -ge 200 ]]; then
    log_success "✅ Qdrant hits validation: $FINAL_HITS >= 200"
else
    log_error "❌ Qdrant hits validation failed: $FINAL_HITS < 200"
fi

# Check 2: Test completed successfully
if [[ "$FINAL_PHASE" == "complete" ]]; then
    log_success "✅ Test completion validation: phase = complete"
else
    log_error "❌ Test completion validation failed: phase = $FINAL_PHASE"
fi

# Check 3: Get final report
log_info "8️⃣  Retrieving final report..."
REPORT_RESPONSE=$(curl -s "$API_BASE/ops/black_swan")
REPORT_EXISTS=$(echo "$REPORT_RESPONSE" | jq -r '.report != null')

if [[ "$REPORT_EXISTS" == "true" ]]; then
    REPORT_MODE=$(echo "$REPORT_RESPONSE" | jq -r '.report.mode // "unknown"')
    REPORT_HITS=$(echo "$REPORT_RESPONSE" | jq -r '.report.qdrant_hits // 0')
    log_success "✅ Final report available: mode=$REPORT_MODE, hits=$REPORT_HITS"
else
    log_error "❌ Final report not available"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Black Swan Hard Mode Test Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Final Results:"
echo "   • Final Phase: $FINAL_PHASE"
echo "   • Total Qdrant Hits: $FINAL_HITS"
echo "   • Run ID: $RUN_ID"
echo ""
echo "🔍 Next Steps:"
echo "   • Check dashboard at http://localhost:3000"
echo "   • Verify P95 latency spike during trip phase"
echo "   • Confirm Auto Tuner auto-resume after 15s"
echo ""
