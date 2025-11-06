#!/bin/bash
# run_lab_headless.sh - Headless Lab Experiment Runner
# ======================================================
# One-command experiment runner for flow control and routing tests.
#
# Usage:
#   ./scripts/run_lab_headless.sh flow        # Run flow control experiment
#   ./scripts/run_lab_headless.sh routing     # Run routing experiment
#   ./scripts/run_lab_headless.sh combo       # Run COMBO (flow + routing) experiment
#   ./scripts/run_lab_headless.sh both        # Run both experiments
#
#   With load generation:
#   ./scripts/run_lab_headless.sh flow --with-load --qps 10 --window 180
#   ./scripts/run_lab_headless.sh combo --with-load --qps 10 --window 120 --rounds 2 \
#       --flow-policy aimd --target-p95 1200 --conc-cap 32 --batch-cap 32 \
#       --routing-mode rules --topk-threshold 32 --topk "16,32,64"
#
# Requirements:
#   - app_main running on port 8011
#   - Qdrant and Redis healthy
#   - Backend in clean state
#
# Output:
#   - reports/lab_flow_report.txt (≤80 lines)
#   - reports/lab_routing_report.txt (≤80 lines)

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8011}"
EXPERIMENT_TYPE="${1:-flow}"
A_WINDOW_MS="${A_WINDOW_MS:-120000}"  # 2 minutes
B_WINDOW_MS="${B_WINDOW_MS:-120000}"  # 2 minutes
ROUNDS="${ROUNDS:-2}"  # Number of ABAB cycles

# Load generation flags
WITH_LOAD=false
AUTO_TUNE=false
QPS=10.0
CONCURRENCY=5
TOPK=10
WINDOW_SEC=180
SEED=42
RECALL_SAMPLE=0.0
ROUTING_MODE="rules"
TOPK_THRESHOLD=32
TOPK_THRESHOLDS=""
FLOW_POLICY="aimd"
TARGET_P95=1200
TARGET_P95_VALUES=""
CONC_CAP=32
CONC_CAPS=""
BATCH_CAP=32
BATCH_CAPS=""
COOLDOWN=30
TIME_BUDGET=0
PER_COMBO_CAP=0
EARLY_STOP=0
APPLY_BEST=false
RESUME=false
VECTOR_BACKEND="faiss"

# Parse arguments
shift  # Skip first arg (experiment type)
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-load)
            WITH_LOAD=true
            shift
            ;;
        --auto-tune)
            AUTO_TUNE=true
            WITH_LOAD=true  # Auto-tune requires load generation
            shift
            ;;
        --qps)
            QPS="$2"
            shift 2
            ;;
        --concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        --topk)
            TOPK="$2"
            shift 2
            ;;
        --window)
            WINDOW_SEC="$2"
            shift 2
            ;;
        --rounds)
            ROUNDS="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --recall-sample)
            RECALL_SAMPLE="$2"
            shift 2
            ;;
        --routing-mode)
            ROUTING_MODE="$2"
            shift 2
            ;;
        --topk-threshold)
            TOPK_THRESHOLD="$2"
            shift 2
            ;;
        --topk-thresholds)
            TOPK_THRESHOLDS="$2"
            shift 2
            ;;
        --flow-policy)
            FLOW_POLICY="$2"
            shift 2
            ;;
        --target-p95)
            TARGET_P95="$2"
            TARGET_P95_VALUES="$2"
            shift 2
            ;;
        --conc-cap)
            CONC_CAP="$2"
            CONC_CAPS="$2"
            shift 2
            ;;
        --batch-cap)
            BATCH_CAP="$2"
            BATCH_CAPS="$2"
            shift 2
            ;;
        --cooldown)
            COOLDOWN="$2"
            shift 2
            ;;
        --time-budget)
            TIME_BUDGET="$2"
            shift 2
            ;;
        --per-combo-cap)
            PER_COMBO_CAP="$2"
            shift 2
            ;;
        --early-stop)
            EARLY_STOP="$2"
            shift 2
            ;;
        --apply-best)
            APPLY_BEST=true
            shift
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --vector-backend)
            VECTOR_BACKEND="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

check_health() {
    log_info "Checking system health..."
    
    HEALTH=$(curl -s "$BASE_URL/api/lab/config" || echo '{"ok":false}')
    
    if echo "$HEALTH" | jq -e '.ok == true' > /dev/null 2>&1; then
        # Check dependencies
        REDIS_OK=$(echo "$HEALTH" | jq -r '.health.redis.ok')
        QDRANT_OK=$(echo "$HEALTH" | jq -r '.health.qdrant.ok')
        
        if [ "$REDIS_OK" = "true" ] && [ "$QDRANT_OK" = "true" ]; then
            log_success "All dependencies healthy"
            return 0
        else
            log_error "Dependencies unhealthy: Redis=$REDIS_OK, Qdrant=$QDRANT_OK"
            return 1
        fi
    else
        log_error "Failed to connect to $BASE_URL"
        return 1
    fi
}

enable_quiet_mode() {
    log_info "Enabling Quiet Mode..."
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/ops/quiet_mode/enable")
    
    if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
        log_success "Quiet Mode enabled"
        return 0
    else
        log_error "Failed to enable Quiet Mode"
        echo "$RESPONSE" | jq '.'
        return 1
    fi
}

prewarm_system() {
    log_info "Prewarming system (60s)..."
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/ops/lab/prewarm" \
        -H "Content-Type: application/json" \
        -d '{"duration_sec": 60}')
    
    if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
        log_success "Prewarm started"
        
        # Wait for prewarm to complete
        log_info "Waiting 60 seconds for prewarm..."
        sleep 60
        log_success "Prewarm completed"
        return 0
    else
        log_error "Failed to start prewarm"
        echo "$RESPONSE" | jq '.'
        return 1
    fi
}

start_experiment() {
    local exp_type="$1"
    
    log_info "Starting ${exp_type} experiment..."
    log_info "  - A window: ${A_WINDOW_MS}ms ($(($A_WINDOW_MS / 1000))s)"
    log_info "  - B window: ${B_WINDOW_MS}ms ($(($B_WINDOW_MS / 1000))s)"
    log_info "  - Rounds: ${ROUNDS}"
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/ops/lab/start" \
        -H "Content-Type: application/json" \
        -d "{\"experiment_type\": \"${exp_type}\", \"a_ms\": ${A_WINDOW_MS}, \"b_ms\": ${B_WINDOW_MS}, \"rounds\": ${ROUNDS}}")
    
    if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
        EXPERIMENT_ID=$(echo "$RESPONSE" | jq -r '.experiment_id')
        log_success "Experiment started: $EXPERIMENT_ID"
        return 0
    else
        ERROR_REASON=$(echo "$RESPONSE" | jq -r '.error // "unknown"')
        log_error "Failed to start experiment: $ERROR_REASON"
        echo "$RESPONSE" | jq '.'
        return 1
    fi
}

monitor_experiment() {
    log_info "Monitoring experiment progress..."
    
    # Calculate total duration
    local total_ms=$(( $A_WINDOW_MS * $ROUNDS + $B_WINDOW_MS * $ROUNDS ))
    local total_sec=$(( $total_ms / 1000 ))
    local check_interval=10
    local checks=$(( $total_sec / $check_interval ))
    
    log_info "Total duration: ${total_sec}s (~$(($total_sec / 60)) minutes)"
    log_info "Will check status every ${check_interval}s"
    echo
    
    for i in $(seq 1 $checks); do
        sleep $check_interval
        
        STATUS=$(curl -s "$BASE_URL/ops/lab/status" || echo '{"ok":false}')
        
        if echo "$STATUS" | jq -e '.ok == true' > /dev/null 2>&1; then
            RUNNING=$(echo "$STATUS" | jq -r '.running')
            PHASE=$(echo "$STATUS" | jq -r '.phase')
            ROUND=$(echo "$STATUS" | jq -r '.current_round')
            TOTAL_ROUNDS=$(echo "$STATUS" | jq -r '.total_rounds')
            PROGRESS=$(echo "$STATUS" | jq -r '.current_window_progress')
            NOISE=$(echo "$STATUS" | jq -r '.current_noise')
            
            if [ "$RUNNING" = "false" ]; then
                log_success "Experiment completed"
                break
            fi
            
            printf "\r${BLUE}[%3d/%3d]${NC} Round %d/%d | Phase: %s | Progress: %3d%% | Noise: %.1f" \
                $i $checks $ROUND $TOTAL_ROUNDS "$PHASE" "$PROGRESS" "$NOISE"
        else
            printf "\r${YELLOW}[%3d/%3d]${NC} Status check failed" $i $checks
        fi
    done
    
    echo
    echo
    log_success "Monitoring complete"
}

stop_experiment() {
    log_info "Stopping experiment..."
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/ops/lab/stop")
    
    if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
        REPORT_PATH=$(echo "$RESPONSE" | jq -r '.report_path')
        WINDOWS=$(echo "$RESPONSE" | jq -r '.windows_collected')
        
        log_success "Experiment stopped"
        log_info "  - Windows collected: $WINDOWS"
        log_info "  - Report: $REPORT_PATH"
        
        return 0
    else
        log_warning "Stop returned non-ok (experiment may have auto-completed)"
        echo "$RESPONSE" | jq '.'
        return 0  # Not a fatal error
    fi
}

fetch_report() {
    log_info "Fetching experiment report..."
    
    RESPONSE=$(curl -s "$BASE_URL/ops/lab/report")
    
    if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
        REPORT=$(echo "$RESPONSE" | jq -r '.report')
        
        # Save report
        mkdir -p reports
        echo "$REPORT" > "reports/lab_${EXPERIMENT_TYPE}_report.txt"
        
        log_success "Report saved to reports/lab_${EXPERIMENT_TYPE}_report.txt"
        
        # Display summary
        echo
        echo "=" * 70
        echo "$REPORT" | head -n 30
        echo "..." 
        echo "=" * 70
        echo
        
        # Check report size
        LINE_COUNT=$(echo "$REPORT" | wc -l)
        if [ "$LINE_COUNT" -le 80 ]; then
            log_success "Report is ≤80 lines ($LINE_COUNT lines)"
        else
            log_warning "Report exceeds 80 lines ($LINE_COUNT lines)"
        fi
        
        return 0
    else
        log_error "Failed to fetch report"
        echo "$RESPONSE" | jq '.'
        return 1
    fi
}

disable_quiet_mode() {
    log_info "Disabling Quiet Mode..."
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/ops/quiet_mode/disable")
    
    if echo "$RESPONSE" | jq -e '.ok == true' > /dev/null 2>&1; then
        log_success "Quiet Mode disabled"
        return 0
    else
        log_warning "Failed to disable Quiet Mode (not critical)"
        return 0
    fi
}

run_single_experiment() {
    local exp_type="$1"
    
    echo
    echo "======================================================================"
    echo "RUNNING $(echo "$exp_type" | tr '[:lower:]' '[:upper:]') EXPERIMENT (Headless Mode)"
    echo "======================================================================"
    echo
    
    # Check if load generation is enabled for flow experiments
    if [ "$WITH_LOAD" = true ] && [ "$exp_type" = "flow_shaping" ]; then
        log_info "Running FLOW with internal load generation"
        echo "  QPS: $QPS"
        echo "  Concurrency: $CONCURRENCY"
        echo "  Top-K: $TOPK"
        echo "  Window: ${WINDOW_SEC}s"
        echo "  Seed: $SEED"
        echo "  Recall Sample: $RECALL_SAMPLE"
        echo
        
        # Run Python load generator
        # Note: Use port 8000 for search endpoint, not 8011
        python3 scripts/run_lab_flow_with_load.py \
            --qps "$QPS" \
            --concurrency "$CONCURRENCY" \
            --topk "$TOPK" \
            --window "$WINDOW_SEC" \
            --rounds "$ROUNDS" \
            --seed "$SEED" \
            --recall-sample "$RECALL_SAMPLE" \
            --base-url "http://localhost:8000"
        
        return $?
    fi
    
    # Check if load generation is enabled for routing experiments
    if [ "$WITH_LOAD" = true ] && [ "$exp_type" = "routing" ]; then
        log_info "Running ROUTING with internal load generation"
        echo "  QPS: $QPS"
        echo "  Concurrency: $CONCURRENCY"
        echo "  Top-K Mix: $TOPK"
        echo "  Window: ${WINDOW_SEC}s"
        echo "  Seed: $SEED"
        echo "  Routing Mode: $ROUTING_MODE"
        echo "  Recall Sample: $RECALL_SAMPLE"
        echo "  Vector Backend: $VECTOR_BACKEND"
        echo
        
        # Set environment variable for vector backend
        export VECTOR_BACKEND="$VECTOR_BACKEND"
        
        # Run Python routing load generator
        python3 scripts/run_lab_route_with_load.py \
            --qps "$QPS" \
            --concurrency "$CONCURRENCY" \
            --topk "$TOPK" \
            --window "$WINDOW_SEC" \
            --rounds "$ROUNDS" \
            --seed "$SEED" \
            --recall-sample "$RECALL_SAMPLE" \
            --routing-mode "$ROUTING_MODE" \
            --base-url "http://localhost:8011"
        
        return $?
    fi
    
    # Check if auto-tune is enabled for combo experiments
    if [ "$AUTO_TUNE" = true ] && [ "$exp_type" = "combo" ]; then
        log_info "Running COMBO with AUTO-TUNE"
        echo "  QPS: $QPS"
        echo "  Concurrency: $CONCURRENCY"
        echo "  Top-K Mix: $TOPK"
        echo "  Window: ${WINDOW_SEC}s"
        echo "  Rounds: $ROUNDS"
        echo "  Seed: $SEED"
        echo "  Flow Policy: $FLOW_POLICY"
        echo "  Target P95 Values: ${TARGET_P95_VALUES}"
        echo "  Conc Caps: ${CONC_CAPS:-$CONC_CAP}"
        echo "  Batch Caps: ${BATCH_CAPS:-$BATCH_CAP}"
        echo "  Routing Mode: $ROUTING_MODE"
        echo "  TopK Thresholds: ${TOPK_THRESHOLDS}"
        echo "  Cooldown: ${COOLDOWN}s"
        echo
        
        # Determine parameter values
        CONC_CAPS_ARG="${CONC_CAPS:-$CONC_CAP}"
        BATCH_CAPS_ARG="${BATCH_CAPS:-$BATCH_CAP}"
        
        # Build command
        CMD="python3 scripts/run_lab_combo_autotune.py \
            --qps $QPS \
            --concurrency $CONCURRENCY \
            --topk $TOPK \
            --window $WINDOW_SEC \
            --rounds $ROUNDS \
            --seed $SEED \
            --flow-policy $FLOW_POLICY \
            --target-p95 \"$TARGET_P95_VALUES\" \
            --conc-cap \"$CONC_CAPS_ARG\" \
            --batch-cap \"$BATCH_CAPS_ARG\" \
            --routing-mode $ROUTING_MODE \
            --topk-threshold \"$TOPK_THRESHOLDS\" \
            --cooldown $COOLDOWN \
            --base-url http://localhost:8011"
        
        # Add optional flags
        if [ "$TIME_BUDGET" -gt 0 ]; then
            CMD="$CMD --time-budget $TIME_BUDGET"
        fi
        if [ "$PER_COMBO_CAP" -gt 0 ]; then
            CMD="$CMD --per-combo-cap $PER_COMBO_CAP"
        fi
        if [ "$EARLY_STOP" -gt 0 ]; then
            CMD="$CMD --early-stop $EARLY_STOP"
        fi
        if [ "$APPLY_BEST" = true ]; then
            CMD="$CMD --apply-best"
        fi
        if [ "$RESUME" = true ]; then
            CMD="$CMD --resume"
        fi
        
        # Run command
        eval $CMD
        
        return $?
    fi
    
    # Check if load generation is enabled for combo experiments
    if [ "$WITH_LOAD" = true ] && [ "$exp_type" = "combo" ]; then
        log_info "Running COMBO with internal load generation"
        echo "  QPS: $QPS"
        echo "  Concurrency: $CONCURRENCY"
        echo "  Top-K Mix: $TOPK"
        echo "  Window: ${WINDOW_SEC}s"
        echo "  Rounds: $ROUNDS"
        echo "  Seed: $SEED"
        echo "  Flow Policy: $FLOW_POLICY"
        echo "  Target P95: ${TARGET_P95}ms"
        echo "  Conc Cap: $CONC_CAP"
        echo "  Batch Cap: $BATCH_CAP"
        echo "  Routing Mode: $ROUTING_MODE"
        echo "  TopK Threshold: $TOPK_THRESHOLD"
        echo
        
        # Run Python combo load generator
        python3 scripts/run_lab_combo_with_load.py \
            --qps "$QPS" \
            --concurrency "$CONCURRENCY" \
            --topk "$TOPK" \
            --window "$WINDOW_SEC" \
            --rounds "$ROUNDS" \
            --seed "$SEED" \
            --flow-policy "$FLOW_POLICY" \
            --target-p95 "$TARGET_P95" \
            --conc-cap "$CONC_CAP" \
            --batch-cap "$BATCH_CAP" \
            --routing-mode "$ROUTING_MODE" \
            --topk-threshold "$TOPK_THRESHOLD" \
            --base-url "http://localhost:8011"
        
        return $?
    fi
    
    # Standard experiment flow (without load generation)
    # Step 1: Health check
    check_health || return 1
    
    # Step 2: Enable quiet mode
    enable_quiet_mode || return 1
    
    # Step 3: Prewarm
    prewarm_system || return 1
    
    # Step 4: Start experiment
    start_experiment "$exp_type" || return 1
    
    # Step 5: Monitor progress
    monitor_experiment
    
    # Step 6: Stop experiment (if still running)
    stop_experiment
    
    # Step 7: Fetch report
    fetch_report || return 1
    
    # Step 8: Disable quiet mode
    disable_quiet_mode
    
    echo
    log_success "${exp_type^^} experiment complete!"
    echo
    
    return 0
}

# Main execution
main() {
    echo "======================================================================"
    echo "LAB EXPERIMENT RUNNER (Headless Mode)"
    echo "======================================================================"
    echo "Target: $BASE_URL"
    echo "Experiment: $EXPERIMENT_TYPE"
    echo "======================================================================"
    echo
    
    # Check prerequisites
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    # Run experiments
    case "$EXPERIMENT_TYPE" in
        flow|flow_shaping)
            EXPERIMENT_TYPE="flow_shaping"
            run_single_experiment "flow_shaping" || exit 1
            ;;
        
        routing)
            EXPERIMENT_TYPE="routing"
            run_single_experiment "routing" || exit 1
            ;;
        
        combo)
            EXPERIMENT_TYPE="combo"
            run_single_experiment "combo" || exit 1
            ;;
        
        both)
            log_info "Running both experiments sequentially"
            echo
            
            EXPERIMENT_TYPE="flow_shaping"
            run_single_experiment "flow_shaping" || exit 1
            
            log_info "Waiting 30s before next experiment..."
            sleep 30
            
            EXPERIMENT_TYPE="routing"
            run_single_experiment "routing" || exit 1
            ;;
        
        *)
            log_error "Unknown experiment type: $EXPERIMENT_TYPE"
            echo "Usage: $0 {flow|routing|combo|both}"
            exit 1
            ;;
    esac
    
    # Success summary
    echo
    echo "======================================================================"
    echo "ALL EXPERIMENTS COMPLETED SUCCESSFULLY"
    echo "======================================================================"
    echo
    echo "Reports generated:"
    ls -lh reports/lab_*_report.txt 2>/dev/null || echo "  (none)"
    echo
    log_success "Headless run complete!"
}

# Run main
main

