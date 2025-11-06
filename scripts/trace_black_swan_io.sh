#!/usr/bin/env bash
#
# trace_black_swan_io.sh
# Diagnostic script to verify Black Swan test reaches Qdrant
#
# Usage:
#   ./scripts/trace_black_swan_io.sh [mode]
#
# Arguments:
#   mode    Black Swan test mode: A, B, or C (default: A)
#

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

API_BASE="${API_BASE:-${APP_DEMO_URL:-http://localhost:8001}}"
MODE="${1:-A}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_error() { echo -e "${RED}[✗]${NC} $*"; }
log_diag() { echo -e "${BLUE}[DIAG]${NC} $*"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Black Swan → Qdrant Trace Diagnostic"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check Qdrant connectivity
log_info "Step 1: Testing Qdrant connectivity..."
QDRANT_RESPONSE=$(curl -sf "${API_BASE}/ops/qdrant/ping" 2>/dev/null || echo "{\"ok\": false}")
QDRANT_OK=$(echo "$QDRANT_RESPONSE" | jq -r '.ok // false')

if [[ "$QDRANT_OK" == "true" ]]; then
    QDRANT_HOST=$(echo "$QDRANT_RESPONSE" | jq -r '.host')
    QDRANT_PORT=$(echo "$QDRANT_RESPONSE" | jq -r '.port')
    QDRANT_LATENCY=$(echo "$QDRANT_RESPONSE" | jq -r '.latency_ms')
    QDRANT_COLLECTIONS=$(echo "$QDRANT_RESPONSE" | jq -r '.collections[]' | tr '\n' ', ' | sed 's/,$//')
    
    log_success "Qdrant reachable at ${QDRANT_HOST}:${QDRANT_PORT} (${QDRANT_LATENCY}ms)"
    log_diag "Collections: ${QDRANT_COLLECTIONS}"
else
    log_error "Qdrant unreachable!"
    echo "$QDRANT_RESPONSE" | jq '.'
    echo ""
    log_error "Cannot trace Black Swan → Qdrant flow if Qdrant is down."
    exit 1
fi

echo ""

# Step 2: Check if logs directory exists
log_info "Step 2: Checking logs directory..."
LOGS_DIR="${PROJECT_ROOT}/logs"
if [[ ! -d "$LOGS_DIR" ]]; then
    log_error "Logs directory not found: ${LOGS_DIR}"
    exit 1
fi
log_success "Logs directory exists: ${LOGS_DIR}"

echo ""

# Step 3: Trigger Black Swan test
log_info "Step 3: Triggering Black Swan test (mode=${MODE})..."

# Clear previous log tail
LOG_FILE="${LOGS_DIR}/backend_8001.log"
if [[ -f "$LOG_FILE" ]]; then
    # Mark current position
    LOG_START_LINE=$(wc -l < "$LOG_FILE")
else
    LOG_START_LINE=0
    log_error "Backend log not found: ${LOG_FILE}"
fi

# Trigger test
TRIGGER_RESPONSE=$(curl -sf -X POST "${API_BASE}/ops/black_swan" \
    -H "Content-Type: application/json" \
    -d "{\"mode\":\"${MODE}\"}" 2>/dev/null || echo "{\"ok\": false}")

TRIGGER_OK=$(echo "$TRIGGER_RESPONSE" | jq -r '.ok // false')

if [[ "$TRIGGER_OK" == "true" ]]; then
    RUN_ID=$(echo "$TRIGGER_RESPONSE" | jq -r '.run_id')
    log_success "Black Swan test started: run_id=${RUN_ID}"
else
    log_error "Failed to trigger Black Swan test"
    echo "$TRIGGER_RESPONSE" | jq '.'
    exit 1
fi

echo ""

# Step 4: Wait and monitor logs
log_info "Step 4: Monitoring logs for 15 seconds..."
sleep 15

# Extract new logs since test started
if [[ -f "$LOG_FILE" ]]; then
    NEW_LOGS=$(tail -n +$((LOG_START_LINE + 1)) "$LOG_FILE")
    
    # Count [BlackSwan] entries
    BLACKSWAN_COUNT=$(echo "$NEW_LOGS" | grep -c "\[BlackSwan\]" || echo "0")
    
    # Count [Qdrant] entries
    QDRANT_COUNT=$(echo "$NEW_LOGS" | grep -c "\[Qdrant\]" || echo "0")
    
    # Count MOCK mode warnings
    MOCK_COUNT=$(echo "$NEW_LOGS" | grep -c "MOCK mode, NOT hitting Qdrant" || echo "0")
    
    log_diag "Found ${BLACKSWAN_COUNT} [BlackSwan] log entries"
    log_diag "Found ${QDRANT_COUNT} [Qdrant] log entries"
    log_diag "Found ${MOCK_COUNT} MOCK mode warnings"
    
    echo ""
    log_info "Recent [BlackSwan] logs:"
    echo "$NEW_LOGS" | grep "\[BlackSwan\]" | tail -10 || log_error "No [BlackSwan] logs found"
    
    echo ""
    log_info "Recent [Qdrant] logs:"
    echo "$NEW_LOGS" | grep "\[Qdrant\]" | tail -10 || log_error "No [Qdrant] logs found"
    
    echo ""
else
    log_error "Cannot read log file: ${LOG_FILE}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Diagnostic Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 5: Verdict
if [[ $QDRANT_COUNT -gt 0 ]]; then
    log_success "✅ Black Swan test IS reaching Qdrant (${QDRANT_COUNT} queries logged)"
    log_info "Data layer is being exercised during chaos tests."
elif [[ $MOCK_COUNT -gt 0 ]]; then
    log_error "⚠️  Black Swan test is NOT reaching Qdrant"
    log_error "Found ${MOCK_COUNT} MOCK mode warnings - search endpoint is simulated"
    log_error "The /search endpoint in app_v2.py does not call real Qdrant"
    log_error ""
    log_error "Recommendation: Integrate real vector search into app_v2.py /search endpoint"
else
    log_error "❓ Inconclusive - no clear evidence either way"
    log_error "Check if Black Swan test actually generated search requests"
fi

echo ""
log_info "Full backend log: ${LOG_FILE}"
log_info "To check Black Swan status: curl ${API_BASE}/ops/black_swan/status"
echo ""

exit 0

