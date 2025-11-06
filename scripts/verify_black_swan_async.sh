#!/usr/bin/env bash
#
# verify_black_swan_async.sh
# Verification script for Black Swan async implementation
#
# This script:
# 1. Starts app_main on port 8011
# 2. Runs a short Black Swan test (mode B)
# 3. Monitors status until complete
# 4. Validates report schema
# 5. Checks precedence chain
# 6. Reports Redis status (degraded if unavailable)
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="${API_URL:-http://localhost:8011}"
MAX_WAIT_SEC=180
POLL_INTERVAL=2

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_error() { echo -e "${RED}[✗]${NC} $*"; }

echo "=========================================="
echo "Black Swan Async Verification"
echo "=========================================="
echo ""

# Check if app_main is running
log_info "Checking if app_main is running on ${API_URL}..."
if ! curl -sf "${API_URL}/healthz" > /dev/null; then
    log_error "app_main not reachable at ${API_URL}"
    log_info "Please start app_main first: cd services/fiqa_api && python app_main.py"
    exit 1
fi

log_success "app_main is running"

# Check verify endpoint for Black Swan async status
log_info "Checking /ops/verify for Black Swan async status..."
VERIFY_RESPONSE=$(curl -sf "${API_URL}/ops/verify")
BS_ENABLED=$(echo "$VERIFY_RESPONSE" | jq -r '.black_swan_async.enabled // false')
BS_AVAILABLE=$(echo "$VERIFY_RESPONSE" | jq -r '.black_swan_async.available // false')

if [[ "$BS_ENABLED" != "true" ]] || [[ "$BS_AVAILABLE" != "true" ]]; then
    log_error "Black Swan async not enabled or available"
    echo "$VERIFY_RESPONSE" | jq '.black_swan_async'
    exit 1
fi

log_success "Black Swan async is enabled and available"

# Check Redis status
REDIS_CONNECTED=$(curl -sf "${API_URL}/admin/health" 2>/dev/null | jq -r '.redis_connected // false' || echo "false")
if [[ "$REDIS_CONNECTED" == "true" ]]; then
    log_success "Redis connected"
else
    log_info "Redis not connected (degraded mode: memory-only)"
fi

# Start Black Swan test (short duration for testing)
log_info "Starting Black Swan test (mode B, short duration)..."
START_RESPONSE=$(curl -sf -X POST "${API_URL}/ops/black_swan" \
    -H "Content-Type: application/json" \
    -d '{
        "mode": "B",
        "params": {
            "warmup_duration": 5,
            "baseline_duration": 5,
            "trip_duration": 10,
            "recovery_duration": 5,
            "warmup_qps": 10,
            "trip_qps": 30,
            "recovery_qps": 10,
            "concurrency": 8
        }
    }' 2>&1)

# Check if start was successful
if echo "$START_RESPONSE" | grep -q '"ok":true' || echo "$START_RESPONSE" | grep -q '"status":"starting"'; then
    log_success "Black Swan test started"
else
    log_error "Failed to start Black Swan test"
    echo "$START_RESPONSE"
    exit 1
fi

# Extract run_id if available
RUN_ID=$(echo "$START_RESPONSE" | jq -r '.run_id // "unknown"' 2>/dev/null || echo "unknown")
log_info "Run ID: $RUN_ID"

# Poll status until complete
log_info "Polling status (max ${MAX_WAIT_SEC}s)..."
START_TIME=$(date +%s)
LAST_PHASE=""
LAST_PROGRESS=0

while true; do
    ELAPSED=$(($(date +%s) - START_TIME))
    
    if [[ $ELAPSED -gt $MAX_WAIT_SEC ]]; then
        log_error "Timeout after ${MAX_WAIT_SEC}s"
        exit 1
    fi
    
    # Get status
    STATUS=$(curl -sf "${API_URL}/ops/black_swan/status" 2>/dev/null || echo "{}")
    
    if [[ -z "$STATUS" ]] || [[ "$STATUS" == "{}" ]]; then
        log_error "Failed to get status"
        sleep $POLL_INTERVAL
        continue
    fi
    
    PHASE=$(echo "$STATUS" | jq -r '.phase // "unknown"')
    PROGRESS=$(echo "$STATUS" | jq -r '.progress // 0')
    ETA=$(echo "$STATUS" | jq -r '.eta_sec // 0')
    MESSAGE=$(echo "$STATUS" | jq -r '.message // ""')
    P95=$(echo "$STATUS" | jq -r '.metrics.p95_ms // "null"')
    QPS=$(echo "$STATUS" | jq -r '.metrics.qps // 0')
    
    # Log if phase changed
    if [[ "$PHASE" != "$LAST_PHASE" ]] || [[ $((PROGRESS - LAST_PROGRESS)) -gt 10 ]]; then
        log_info "Phase: $PHASE, Progress: ${PROGRESS}%, ETA: ${ETA}s, P95: ${P95}ms, QPS: ${QPS}"
        LAST_PHASE="$PHASE"
        LAST_PROGRESS=$PROGRESS
    fi
    
    # Check if complete or failed
    if [[ "$PHASE" == "complete" ]]; then
        log_success "Test completed!"
        break
    elif [[ "$PHASE" == "error" ]]; then
        ERROR_MSG=$(echo "$STATUS" | jq -r '.error // "Unknown error"')
        log_error "Test failed: $ERROR_MSG"
        exit 1
    elif [[ "$PHASE" == "canceled" ]]; then
        log_error "Test was canceled"
        exit 1
    fi
    
    sleep $POLL_INTERVAL
done

# Get final report
log_info "Fetching final report..."
REPORT_RESPONSE=$(curl -sf "${API_URL}/ops/black_swan/report" 2>/dev/null || echo "{}")

if echo "$REPORT_RESPONSE" | grep -q '"ok":true'; then
    log_success "Report retrieved successfully"
    
    # Extract report
    REPORT=$(echo "$REPORT_RESPONSE" | jq '.report')
    
    # Validate schema
    log_info "Validating report schema..."
    
    # Check required fields
    REQUIRED_FIELDS=("run_id" "mode" "warmup" "trip" "summary")
    for FIELD in "${REQUIRED_FIELDS[@]}"; do
        if echo "$REPORT" | jq -e ".${FIELD}" > /dev/null 2>&1; then
            log_success "Field present: $FIELD"
        else
            log_error "Missing field: $FIELD"
            exit 1
        fi
    done
    
    # Check metrics in phases
    PHASES=("warmup" "baseline" "trip" "recovery")
    for PHASE in "${PHASES[@]}"; do
        P95=$(echo "$REPORT" | jq -r ".${PHASE}.metrics.p95_ms // null")
        if [[ "$P95" != "null" ]]; then
            log_success "Phase $PHASE has P95 metric: ${P95}ms"
        else
            log_info "Phase $PHASE P95 is null (might be expected)"
        fi
    done
    
    # Check precedence chain
    log_info "Checking precedence chain..."
    PRECEDENCE=$(echo "$REPORT" | jq -r '.precedence_chain // []')
    CHAIN_LENGTH=$(echo "$PRECEDENCE" | jq 'length')
    
    if [[ "$CHAIN_LENGTH" -gt 0 ]]; then
        log_success "Precedence chain present (${CHAIN_LENGTH} items)"
        echo "$PRECEDENCE" | jq -r '.[] | "  - " + .' | head -3
    else
        log_info "Precedence chain empty (no force override active)"
    fi
    
    # Check summary
    TOTAL_REQUESTS=$(echo "$REPORT" | jq -r '.summary.total_requests // 0')
    TOTAL_ERRORS=$(echo "$REPORT" | jq -r '.summary.total_errors // 0')
    
    log_success "Summary: ${TOTAL_REQUESTS} requests, ${TOTAL_ERRORS} errors"
    
else
    log_error "Failed to retrieve report"
    echo "$REPORT_RESPONSE"
    exit 1
fi

# Final checks
echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
log_success "✓ app_main running and accessible"
log_success "✓ Black Swan async enabled and available"

if [[ "$REDIS_CONNECTED" == "true" ]]; then
    log_success "✓ Redis connected"
else
    log_info "⚠ Redis not connected (degraded: memory-only)"
fi

log_success "✓ Test started successfully"
log_success "✓ Status endpoint working"
log_success "✓ Test completed without errors"
log_success "✓ Report retrieved and validated"
log_success "✓ All required fields present"

echo ""
echo -e "${GREEN}=========================================="
echo -e "✓ ALL CHECKS PASSED (black_swan_async)"
echo -e "==========================================${NC}"
echo ""

exit 0

