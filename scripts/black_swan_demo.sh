#!/usr/bin/env bash
#
# black_swan_demo.sh
# Run a full "Black Swan" demo sequence, capturing before/trip/after snapshots.
# Exit 0 on success, 1 on failure.
#

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Filter out comments and empty lines, then remove inline comments
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep -v '^$' | sed 's/#.*$//' | xargs)
fi

# Black Swan Real Retrieval Mode - Default to REAL
export BLACK_SWAN_USE_REAL="${BLACK_SWAN_USE_REAL:-true}"
export BLACK_SWAN_NOCACHE="${BLACK_SWAN_NOCACHE:-true}"
export FIQA_SEARCH_URL="${FIQA_SEARCH_URL:-http://localhost:8080/search}"
export QDRANT_COLLECTION="${QDRANT_COLLECTION:-beir_fiqa_full_ta}"

API_BASE="${API_BASE:-${APP_DEMO_URL:-http://localhost:8001}}"
REPORTS_DIR="reports"
BEFORE_FILE="${REPORTS_DIR}/black_swan_before.json"
TRIP_FILE="${REPORTS_DIR}/black_swan_trip.json"
AFTER_FILE="${REPORTS_DIR}/black_swan_after.json"

# Configurable parameters
BLACK_SWAN_WARMUP_QPS="${BLACK_SWAN_WARMUP_QPS:-20}"  # Increased from 10 to 20
BLACK_SWAN_LOAD_QPS="${BLACK_SWAN_LOAD_QPS:-70}"
BLACK_SWAN_LOAD_DURATION="${BLACK_SWAN_LOAD_DURATION:-${PLAY_B_DURATION_SEC:-60}}"
# Note: BLACK_SWAN_NOCACHE and BLACK_SWAN_USE_REAL set above (default true)

# ========================================
# Auto-calculate phase durations (Mode B: 10%/10%/60%/20%)
# ========================================
TOTAL_DURATION="${BLACK_SWAN_LOAD_DURATION}"
PHASE_WARMUP_PCT=10
PHASE_BASELINE_PCT=10
PHASE_TRIP_PCT=60
PHASE_RECOVERY_PCT=20

# Calculate actual phase durations (in seconds)
PHASE_WARMUP_SEC=$((TOTAL_DURATION * PHASE_WARMUP_PCT / 100))
PHASE_BASELINE_SEC=$((TOTAL_DURATION * PHASE_BASELINE_PCT / 100))
PHASE_TRIP_SEC=$((TOTAL_DURATION * PHASE_TRIP_PCT / 100))
PHASE_RECOVERY_SEC=$((TOTAL_DURATION * PHASE_RECOVERY_PCT / 100))

# Override hardcoded values with calculated ones
BLACK_SWAN_WARMUP_DURATION="${PHASE_WARMUP_SEC}"
BLACK_SWAN_BUFFER_SEC=5  # Keep 5s buffer for metrics stabilization
TRIP_WAIT_SEC="${PHASE_TRIP_SEC}"
BLACK_SWAN_RECOVERY_WAIT="${PHASE_RECOVERY_SEC}"

# Baseline gate thresholds (adaptive across machines)
BASELINE_P95_MIN="${BASELINE_P95_MIN:-10}"
BASELINE_P95_MAX="${BASELINE_P95_MAX:-200}"
BASELINE_MIN_SAMPLES="${BASELINE_MIN_SAMPLES:-100}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Log calculated phase durations
log_info "Phase durations (${TOTAL_DURATION}s total): warmup=${PHASE_WARMUP_SEC}s baseline=${PHASE_BASELINE_SEC}s trip=${PHASE_TRIP_SEC}s recovery=${PHASE_RECOVERY_SEC}s"

# Function to add nocache parameter if enabled
add_nocache_param() {
    local url="$1"
    if [[ "${BLACK_SWAN_NOCACHE}" == "true" ]]; then
        # Add timestamp and random number to bypass cache
        local timestamp=$(date +%s)
        local random_num=$((RANDOM % 10000))
        if [[ "$url" == *"?"* ]]; then
            echo "${url}&nocache=${timestamp}_${random_num}"
        else
            echo "${url}?nocache=${timestamp}_${random_num}"
        fi
    else
        echo "$url"
    fi
}

# Global variable to hold run_id (passed via environment from backend)
RUN_ID="${BLACK_SWAN_RUN_ID:-}"

# Validate RUN_ID is set
if [[ -z "$RUN_ID" ]]; then
    echo "[ERROR] BLACK_SWAN_RUN_ID environment variable not set"
    echo "This script must be called by the backend with RUN_ID set"
    exit 1
fi

echo "[INFO] Black Swan run_id: $RUN_ID"

# Tap event logging function
send_tap_event() {
    local event=$1
    local phase=${2:-""}
    local message=${3:-""}
    local http=${4:-0}
    
    # Only send if TAP_ENABLED (check via health endpoint)
    if [[ "${TAP_ENABLED:-false}" == "true" ]]; then
        curl -sf -X POST "${API_BASE}/ops/tap/event" \
            -H "Content-Type: application/json" \
            -d "{\"client\":\"script\",\"event\":\"${event}\",\"run_id\":\"${RUN_ID}\",\"phase\":\"${phase}\",\"message\":\"${message}\",\"http\":${http}}" \
            > /dev/null 2>&1 || true
    fi
}

# Progress reporting function (with run_id gating and tap logging)
update_progress() {
    local phase=$1
    local progress=$2
    local eta_sec=${3:-0}
    local message=${4:-""}
    
    # Skip if run_id not set (shouldn't happen, but defensive)
    if [[ -z "$RUN_ID" ]]; then
        log_error "RUN_ID not set, skipping progress update"
        return 1
    fi
    
    # Send tap event for progress updates
    send_tap_event "progress" "$phase" "$message"
    
    curl -sf -X POST "${API_BASE}/ops/black_swan/progress" \
        -H "Content-Type: application/json" \
        -H "X-Tap-Client: script" \
        -H "X-Tap-Run-ID: ${RUN_ID}" \
        -H "X-Tap-Phase: ${phase}" \
        -d "{\"run_id\":\"${RUN_ID}\",\"phase\":\"${phase}\",\"progress\":${progress},\"eta_sec\":${eta_sec},\"message\":\"${message}\"}" \
        > /dev/null || true
    
    log_info "[${phase}] ${progress}% - ${message}"
}

# Error reporting function (with structured error and tap logging)
update_error() {
    local code=$1
    local step=$2
    local http=${3:-0}
    local message=${4:-"Unknown error"}
    
    # Truncate message to 80 chars
    message="${message:0:80}"
    
    # Skip if run_id not set
    if [[ -z "$RUN_ID" ]]; then
        log_error "RUN_ID not set, cannot report error"
        return 1
    fi
    
    log_error "Error: code=${code}, step=${step}, http=${http}, message=${message}"
    
    # Send tap event for error
    send_tap_event "error" "$step" "$message" "$http"
    
    curl -sf -X POST "${API_BASE}/ops/black_swan/progress" \
        -H "Content-Type: application/json" \
        -H "X-Tap-Client: script" \
        -H "X-Tap-Run-ID: ${RUN_ID}" \
        -H "X-Tap-Phase: error" \
        -d "{\"run_id\":\"${RUN_ID}\",\"phase\":\"error\",\"progress\":0,\"message\":\"${message}\",\"error\":{\"code\":\"${code}\",\"step\":\"${step}\",\"http\":${http},\"message\":\"${message}\"}}" \
        > /dev/null || true
}

# Retry curl with exponential backoff (1s, 2s, 4s) and tap breadcrumbs
retry_curl() {
    local max_tries=3
    local delay=1
    local try=1
    local http_status=0
    local response=""
    
    # All arguments are passed to curl
    local curl_args=("$@")
    
    while [[ $try -le $max_tries ]]; do
        # Capture both status and response
        response=$(curl -sf -w "\nHTTP_STATUS:%{http_code}" \
            -H "X-Tap-Client: script" \
            -H "X-Tap-Run-ID: ${RUN_ID}" \
            "${curl_args[@]}" 2>&1 || echo "")
        http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2 || echo "000")
        
        # Remove status line from response
        response=$(echo "$response" | grep -v "HTTP_STATUS:" || echo "")
        
        # Log to file for debugging
        cat > "${REPORTS_DIR}/black_swan_last_http.json" <<EOF
{
  "url": "${curl_args[*]}",
  "try": ${try},
  "http_status": ${http_status},
  "response": $(echo "$response" | jq -Rs . 2>/dev/null || echo "\"\""),
  "timestamp": $(date +%s)
}
EOF
        
        # Check if successful (2xx or 3xx)
        if [[ "${http_status}" =~ ^[23][0-9][0-9]$ ]]; then
            echo "$response"
            return 0
        fi
        
        # Send tap breadcrumb on curl failure
        send_tap_event "curl_error" "${CURRENT_STEP:-unknown}" "HTTP ${http_status} on attempt ${try}" "$http_status"
        
        log_error "Attempt $try/$max_tries failed (HTTP ${http_status}), retrying in ${delay}s..."
        sleep "$delay"
        delay=$((delay * 2))
        try=$((try + 1))
    done
    
    # All retries failed
    log_error "All $max_tries attempts failed (last HTTP: ${http_status})"
    echo "$response"
    return 1
}

cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Black Swan demo failed"
        # Note: Specific errors should call update_error directly
        # This is just a catch-all for unexpected failures
        update_error "unexpected_failure" "unknown" 0 "Test failed unexpectedly"
        exit 1
    fi
}

trap cleanup EXIT

# Preconditions: Check API and create reports directory
log_info "Checking preconditions..."

# Send start event
send_tap_event "start" "starting" "Black Swan test starting with run_id=${RUN_ID}"

update_progress "starting" 5 90 "Checking API connectivity..."

# Check API with retries
CURRENT_STEP="preflight"
if ! retry_curl "${API_BASE}/ops/summary" > /dev/null; then
    log_error "API not reachable at ${API_BASE}/ops/summary after 3 retries"
    # Extract HTTP status from last_http.json if available
    HTTP_STATUS=$(jq -r '.http_status // 0' "${REPORTS_DIR}/black_swan_last_http.json" 2>/dev/null || echo "0")
    update_error "api_unreachable" "preflight" "$HTTP_STATUS" "API not reachable after retries"
    exit 1
fi

log_success "API is reachable at ${API_BASE}"

if [[ ! -d "${REPORTS_DIR}" ]]; then
    mkdir -p "${REPORTS_DIR}"
    log_info "Created ${REPORTS_DIR} directory"
fi

# STEP 0: Pre-warm with light traffic to establish valid baseline
CURRENT_STEP="warmup"
update_progress "warmup" 10 85 "Starting warmup phase (${BLACK_SWAN_WARMUP_QPS} QPS × ${BLACK_SWAN_WARMUP_DURATION}s)..."
log_info "STEP 0: Pre-warming system with light traffic..."

# Start warmup load with retries
WARMUP_URL=$(add_nocache_param "${API_BASE}/load/start?qps=${BLACK_SWAN_WARMUP_QPS}&pattern=constant&duty=100&duration=${BLACK_SWAN_WARMUP_DURATION}")
if ! retry_curl -X POST "$WARMUP_URL" > /dev/null; then
    log_error "Failed to start warmup load after retries"
    HTTP_STATUS=$(jq -r '.http_status // 0' "${REPORTS_DIR}/black_swan_last_http.json" 2>/dev/null || echo "0")
    update_error "load_start_failed" "warmup" "$HTTP_STATUS" "Failed to start warmup load"
    exit 1
fi

# Verify load actually started by checking /load/status
sleep 2
LOAD_RUNNING=$(curl -sf "${API_BASE}/load/status" | jq -r '.running // false' 2>/dev/null || echo "false")
if [[ "$LOAD_RUNNING" != "true" ]]; then
    log_error "Warmup load did not start (load/status shows running=false)"
    update_error "load_verify_failed" "warmup" 0 "Load started but not confirmed running"
    exit 1
fi

log_success "Warmup load started (${BLACK_SWAN_WARMUP_QPS} QPS × ${BLACK_SWAN_WARMUP_DURATION}s)"
update_progress "warmup" 15 80 "Warmup in progress..."

# Wait for warmup to complete + buffer with progress updates
log_info "Waiting $((BLACK_SWAN_WARMUP_DURATION + BLACK_SWAN_BUFFER_SEC))s for warmup to complete..."
WARMUP_WAIT_TOTAL=$((BLACK_SWAN_WARMUP_DURATION + BLACK_SWAN_BUFFER_SEC))
WARMUP_ELAPSED=0
while [[ $WARMUP_ELAPSED -lt $WARMUP_WAIT_TOTAL ]]; do
    sleep 3
    WARMUP_ELAPSED=$((WARMUP_ELAPSED + 3))
    # Update progress from 15% to 20% during warmup
    WARMUP_PROGRESS=$((15 + (5 * WARMUP_ELAPSED / WARMUP_WAIT_TOTAL)))
    ETA=$((75 - (5 * WARMUP_ELAPSED / WARMUP_WAIT_TOTAL)))
    update_progress "warmup" $WARMUP_PROGRESS $ETA "Warmup in progress (${WARMUP_ELAPSED}/${WARMUP_WAIT_TOTAL}s)..."
done

update_progress "warmup" 20 75 "Warmup complete, metrics stabilizing..."
log_success "Warmup complete, waiting for metrics to stabilize..."

# Additional wait to ensure metrics are aggregated (window60s needs 3+ samples)
log_info "Waiting additional 5s for metrics aggregation..."
sleep 3
update_progress "warmup" 22 73 "Metrics aggregating..."
sleep 2

# STEP 1: Capture baseline snapshot (now with valid samples)
CURRENT_STEP="baseline"
update_progress "baseline" 25 70 "Capturing baseline snapshot..."
log_info "STEP 1: Capturing baseline snapshot..."

# Use retry_curl for baseline capture
if ! retry_curl "${API_BASE}/ops/summary" | jq '.' > "${BEFORE_FILE}"; then
    log_error "Failed to capture baseline snapshot after retries"
    HTTP_STATUS=$(jq -r '.http_status // 0' "${REPORTS_DIR}/black_swan_last_http.json" 2>/dev/null || echo "0")
    update_error "snapshot_failed" "baseline" "$HTTP_STATUS" "Failed to capture baseline snapshot"
    exit 1
fi

log_success "Baseline snapshot saved to ${BEFORE_FILE}"

# Check series60s non-empty buckets (guard rail)
NON_EMPTY_BUCKETS=$(jq -r '.series60s.non_empty // 0' "${BEFORE_FILE}")
log_info "Series60s non-empty buckets: ${NON_EMPTY_BUCKETS}/13"

# Lowered threshold: need at least 3 buckets for time series rendering
if [[ "${NON_EMPTY_BUCKETS}" -lt 3 ]]; then
    log_error "❌ Insufficient samples: only ${NON_EMPTY_BUCKETS}/13 non-empty buckets (need ≥3)"
    update_error "insufficient_samples" "baseline" 0 "Only ${NON_EMPTY_BUCKETS}/13 non-empty buckets"
    exit 1
fi

log_success "✓ Sufficient bucket coverage: ${NON_EMPTY_BUCKETS}/13 buckets"

# Adaptive baseline gate validation (warn instead of fail for outliers)
BEFORE_SAMPLES=$(jq -r '.window60s.samples // 0' "${BEFORE_FILE}")
BEFORE_P95=$(jq -r '.window60s.p95_ms // null' "${BEFORE_FILE}")

log_info "Baseline gate check: samples=${BEFORE_SAMPLES}, p95=${BEFORE_P95}ms"
log_info "Thresholds: samples≥${BASELINE_MIN_SAMPLES}, p95∈[${BASELINE_P95_MIN}, ${BASELINE_P95_MAX}]ms"

# Initialize gate status
BASELINE_ACCEPTED=true
BASELINE_WARNING=false
BASELINE_REASON="ok"

# Check samples
if [[ "${BEFORE_SAMPLES}" -lt "${BASELINE_MIN_SAMPLES}" ]]; then
    BASELINE_WARNING=true
    BASELINE_REASON="low_samples"
    log_error "⚠️  Baseline warning: samples=${BEFORE_SAMPLES} < ${BASELINE_MIN_SAMPLES} (low sample count)"
fi

# Check p95 range (adaptive gates)
if [[ "${BEFORE_P95}" == "null" ]]; then
    BASELINE_ACCEPTED=false
    BASELINE_WARNING=true
    BASELINE_REASON="null_p95"
    log_error "❌ Baseline rejected: p95 is null (no latency data)"
    update_error "null_p95" "baseline" 0 "Baseline p95 is null (no latency data)"
    exit 1
elif awk -v p95="${BEFORE_P95}" -v min="${BASELINE_P95_MIN}" -v max="${BASELINE_P95_MAX}" \
     'BEGIN {exit !(p95 >= min && p95 <= max)}'; then
    # Within acceptable range
    if [[ "${BASELINE_WARNING}" == "false" ]]; then
        log_success "✓ Baseline accepted: ${BEFORE_SAMPLES} samples, p95=${BEFORE_P95}ms"
    else
        log_success "✓ Baseline accepted (with warning: ${BASELINE_REASON}): p95=${BEFORE_P95}ms"
    fi
elif awk -v p95="${BEFORE_P95}" -v min="${BASELINE_P95_MIN}" 'BEGIN {exit !(p95 < min)}'; then
    # Too fast (< min)
    BASELINE_WARNING=true
    BASELINE_REASON="too_fast"
    log_error "⚠️  Baseline warning: p95=${BEFORE_P95}ms < ${BASELINE_P95_MIN}ms (super fast machine)"
    log_info "Data recorded but may not be representative of typical systems"
else
    # Too slow (> max)
    BASELINE_WARNING=true
    BASELINE_REASON="too_slow"
    log_error "⚠️  Baseline warning: p95=${BEFORE_P95}ms > ${BASELINE_P95_MAX}ms (slow machine or load)"
    log_info "Data recorded but system may be under stress"
fi

# Create baseline_gate.json for inclusion in report
# Convert bash booleans to JSON booleans
BASELINE_ACCEPTED_JSON=$([ "$BASELINE_ACCEPTED" = "true" ] && echo "true" || echo "false")
BASELINE_WARNING_JSON=$([ "$BASELINE_WARNING" = "true" ] && echo "true" || echo "false")

cat > "${REPORTS_DIR}/baseline_gate.json" <<EOF
{
  "p95_ms": ${BEFORE_P95},
  "samples": ${BEFORE_SAMPLES},
  "accepted": ${BASELINE_ACCEPTED_JSON},
  "warning": ${BASELINE_WARNING_JSON},
  "reason": "${BASELINE_REASON}",
  "thresholds": {
    "p95_min": ${BASELINE_P95_MIN},
    "p95_max": ${BASELINE_P95_MAX},
    "min_samples": ${BASELINE_MIN_SAMPLES}
  }
}
EOF

log_info "Baseline gate status saved to baseline_gate.json"
update_progress "baseline" 30 65 "Baseline gate: ${BASELINE_REASON}"

# STEP 2: Start high load to trigger guardrail
CURRENT_STEP="trip"
update_progress "trip" 35 60 "Starting high load test (${BLACK_SWAN_LOAD_QPS} QPS × ${BLACK_SWAN_LOAD_DURATION}s)..."
log_info "STEP 2: Starting high load (qps=${BLACK_SWAN_LOAD_QPS}, pattern=step, duty=100, duration=${BLACK_SWAN_LOAD_DURATION})..."

TRIP_URL=$(add_nocache_param "${API_BASE}/load/start?qps=${BLACK_SWAN_LOAD_QPS}&pattern=step&duty=100&duration=${BLACK_SWAN_LOAD_DURATION}")
if ! retry_curl -X POST "$TRIP_URL" > /dev/null; then
    log_error "Failed to start high load test after retries"
    HTTP_STATUS=$(jq -r '.http_status // 0' "${REPORTS_DIR}/black_swan_last_http.json" 2>/dev/null || echo "0")
    update_error "load_start_failed" "trip" "$HTTP_STATUS" "Failed to start high load test"
    exit 1
fi

# Verify load actually started
sleep 2
LOAD_RUNNING=$(curl -sf "${API_BASE}/load/status" | jq -r '.running // false' 2>/dev/null || echo "false")
if [[ "$LOAD_RUNNING" != "true" ]]; then
    log_error "High load test did not start (load/status shows running=false)"
    update_error "load_verify_failed" "trip" 0 "High load started but not confirmed running"
    exit 1
fi

log_success "Load test started"
update_progress "trip" 40 55 "High load running..."

# STEP 3: Wait and capture "trip" snapshot with progress updates
update_progress "trip" 45 50 "Waiting ${TRIP_WAIT_SEC}s for system to show stress response..."
log_info "STEP 3: Waiting ${TRIP_WAIT_SEC} seconds for stress response..."
TRIP_ELAPSED=0
TRIP_INTERVAL=5  # Update every 5s
while [[ $TRIP_ELAPSED -lt $TRIP_WAIT_SEC ]]; do
    sleep $TRIP_INTERVAL
    TRIP_ELAPSED=$((TRIP_ELAPSED + TRIP_INTERVAL))
    # Progress from 45% to 55% during trip
    TRIP_PROGRESS=$((45 + (10 * TRIP_ELAPSED / TRIP_WAIT_SEC)))
    ETA=$((50 - (10 * TRIP_ELAPSED / TRIP_WAIT_SEC)))
    update_progress "trip" $TRIP_PROGRESS $ETA "Stress response developing ($TRIP_ELAPSED/${TRIP_WAIT_SEC}s)..."
done

update_progress "trip" 50 45 "Capturing trip snapshot..."
log_info "Capturing 'trip' snapshot..."

if ! retry_curl "${API_BASE}/ops/summary" | jq '.' > "${TRIP_FILE}"; then
    log_error "Failed to capture trip snapshot after retries"
    HTTP_STATUS=$(jq -r '.http_status // 0' "${REPORTS_DIR}/black_swan_last_http.json" 2>/dev/null || echo "0")
    update_error "snapshot_failed" "trip" "$HTTP_STATUS" "Failed to capture trip snapshot"
    exit 1
fi

log_success "Trip snapshot saved to ${TRIP_FILE}"
update_progress "trip" 55 40 "Trip snapshot captured"

# STEP 4: Wait for recovery and capture "after" snapshot with progress updates
CURRENT_STEP="recovery"
update_progress "recovery" 60 35 "Waiting ${BLACK_SWAN_RECOVERY_WAIT}s for system recovery..."
log_info "STEP 4: Waiting ${BLACK_SWAN_RECOVERY_WAIT} seconds for recovery..."
RECOVERY_ELAPSED=0
while [[ $RECOVERY_ELAPSED -lt $BLACK_SWAN_RECOVERY_WAIT ]]; do
    sleep 5
    RECOVERY_ELAPSED=$((RECOVERY_ELAPSED + 5))
    # Progress from 60% to 85% during recovery
    RECOVERY_PROGRESS=$((60 + (25 * RECOVERY_ELAPSED / BLACK_SWAN_RECOVERY_WAIT)))
    ETA=$((35 - (25 * RECOVERY_ELAPSED / BLACK_SWAN_RECOVERY_WAIT)))
    update_progress "recovery" $RECOVERY_PROGRESS $ETA "System recovering ($RECOVERY_ELAPSED/${BLACK_SWAN_RECOVERY_WAIT}s)..."
done

update_progress "recovery" 85 10 "Capturing after snapshot..."
log_info "Capturing 'after' snapshot..."

if ! retry_curl "${API_BASE}/ops/summary" | jq '.' > "${AFTER_FILE}"; then
    log_error "Failed to capture after snapshot after retries"
    HTTP_STATUS=$(jq -r '.http_status // 0' "${REPORTS_DIR}/black_swan_last_http.json" 2>/dev/null || echo "0")
    update_error "snapshot_failed" "recovery" "$HTTP_STATUS" "Failed to capture recovery snapshot"
    exit 1
fi

log_success "After snapshot saved to ${AFTER_FILE}"
update_progress "recovery" 90 5 "Recovery snapshot captured"

# Combine report with telemetry
update_progress "complete" 95 2 "Combining snapshots into final report..."
log_info "Combining snapshots into final report..."

TIMESTAMP=$(date +%s)
FINAL_REPORT="${REPORTS_DIR}/black_swan_${TIMESTAMP}.json"

# Fetch playbook_params from backend status (includes mode, heavy_params, duration, etc.)
PLAYBOOK_PARAMS_JSON=$(curl -sf "${API_BASE}/ops/black_swan/status" | jq -c '.playbook_params // {}' || echo '{}')

# Build report with progress_timeline, warmup parameters, baseline_gate, and playbook_params
if ! jq -s \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg warmup_qps "${BLACK_SWAN_WARMUP_QPS}" \
    --arg warmup_duration "${BLACK_SWAN_WARMUP_DURATION}" \
    --arg buffer_sec "${BLACK_SWAN_BUFFER_SEC}" \
    --arg load_qps "${BLACK_SWAN_LOAD_QPS}" \
    --arg load_duration "${BLACK_SWAN_LOAD_DURATION}" \
    --arg recovery_wait "${BLACK_SWAN_RECOVERY_WAIT}" \
    --argjson playbook_params "${PLAYBOOK_PARAMS_JSON}" \
    '{
        timestamp: $ts,
        progress_timeline: ["starting", "warmup", "baseline", "trip", "recovery", "complete"],
        warmup_config: {
            qps: ($warmup_qps|tonumber),
            duration_sec: ($warmup_duration|tonumber),
            buffer_sec: ($buffer_sec|tonumber)
        },
        test_config: {
            load_qps: ($load_qps|tonumber),
            load_duration_sec: ($load_duration|tonumber),
            recovery_wait_sec: ($recovery_wait|tonumber)
        },
        playbook_params: $playbook_params,
        baseline_gate: .[3],
        before: .[0],
        trip: .[1],
        after: .[2]
    }' \
    "${BEFORE_FILE}" \
    "${TRIP_FILE}" \
    "${AFTER_FILE}" \
    "${REPORTS_DIR}/baseline_gate.json" \
    > "${FINAL_REPORT}"; then
    log_error "Failed to combine snapshots"
    update_error "report_write_failed" "finalize" 0 "Failed to write final report JSON"
    exit 1
fi

log_success "Combined report saved to ${FINAL_REPORT}"

# Extract just the filename for reporting
REPORT_FILENAME=$(basename "${FINAL_REPORT}")

# Send complete event
send_tap_event "complete" "complete" "Black Swan test complete: ${REPORT_FILENAME}"

update_progress "complete" 100 0 "Black Swan test complete: ${REPORT_FILENAME}"

echo ""
echo "✅ Black Swan demo complete: ${FINAL_REPORT}"
echo "🦢 Report saved to: ${FINAL_REPORT}"
echo "📊 View at: ${API_BASE}/ops/black_swan"
echo ""

exit 0
