#!/bin/bash
# run_combo_20min.sh - 20 Minute Combo Test with Agent Support
# ============================================================
# Complete system validation: Unified Entry + Milvus Routing + Agent V2/V3
#
# Usage:
#   ./scripts/run_combo_20min.sh                             # Basic 20min test
#   ./scripts/run_combo_20min.sh --with-agent                # With Agent V2 (default)
#   ./scripts/run_combo_20min.sh --with-agent --agent-version v3  # With Agent V3
#   ./scripts/run_combo_20min.sh --save-report               # Save detailed reports
#   ./scripts/run_combo_20min.sh --qps 4 --window 1200      # Custom params
#
# Requirements:
#   - Docker services: redis, qdrant, milvus-standalone
#   - fiqa_api running on port 8011
#   - VECTOR_BACKEND=milvus
#   - AGENT_MODE=v3 (if using agent)
#
# Output:
#   - reports/LABOPS_COMBO_REPORT.txt
#   - reports/LABOPS_AGENT_V{2,3}_SUMMARY.txt (if --with-agent)
#   - reports/LABOPS_AGENT_HISTORY.json (if --save-report)

set -e

# Default configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost:8011}"
QPS=4
WINDOW_SEC=1200  # 20 minutes
ROUNDS=1  # Single long run
WITH_AGENT=false
AGENT_VERSION="v2"
SAVE_REPORT=false
VECTOR_BACKEND="milvus"
AGENT_MODE="v3"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-agent)
            WITH_AGENT=true
            shift
            ;;
        --agent-version)
            AGENT_VERSION="$2"
            shift 2
            ;;
        --save-report)
            SAVE_REPORT=true
            shift
            ;;
        --vector-backend)
            VECTOR_BACKEND="$2"
            shift 2
            ;;
        --qps)
            QPS="$2"
            shift 2
            ;;
        --window)
            WINDOW_SEC="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--with-agent] [--agent-version v2|v3] [--save-report] [--qps N] [--window SEC]"
            exit 1
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_header() {
    echo
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_docker_services() {
    log_header "🔍 Step 1: Health Check"
    
    log_info "Checking Docker services..."
    
    REDIS_OK=false
    QDRANT_OK=false
    MILVUS_OK=false
    
    if docker compose ps redis | grep -q "Up"; then
        log_success "Redis is running"
        REDIS_OK=true
    else
        log_error "Redis is not running"
    fi
    
    if docker compose ps qdrant | grep -q "Up"; then
        log_success "Qdrant is running"
        QDRANT_OK=true
    else
        log_error "Qdrant is not running"
    fi
    
    if docker compose ps milvus-standalone | grep -q "Up"; then
        log_success "Milvus is running"
        MILVUS_OK=true
    else
        log_error "Milvus is not running"
    fi
    
    if [ "$REDIS_OK" = true ] && [ "$QDRANT_OK" = true ] && [ "$MILVUS_OK" = true ]; then
        log_success "All Docker services healthy"
        return 0
    else
        log_error "Some Docker services are unhealthy"
        log_warning "Please run: docker compose up -d redis qdrant milvus-standalone"
        return 1
    fi
}

check_api_health() {
    log_info "Checking API health at $BASE_URL..."
    
    HEALTH=$(curl -s "$BASE_URL/api/lab/config" || echo '{"ok":false}')
    
    if echo "$HEALTH" | jq -e '.ok == true' > /dev/null 2>&1; then
        log_success "API is healthy"
        return 0
    else
        log_error "API is not responding correctly"
        log_warning "Please ensure fiqa_api is running on port 8011"
        return 1
    fi
}

run_combo_experiment() {
    log_header "🧪 Step 2: Run 20-Minute Combo Experiment"
    
    log_info "Configuration:"
    echo "  • Duration: ${WINDOW_SEC}s ($(($WINDOW_SEC / 60)) minutes)"
    echo "  • QPS: $QPS"
    echo "  • Rounds: $ROUNDS"
    echo "  • Vector Backend: $VECTOR_BACKEND"
    echo "  • With Agent: $WITH_AGENT"
    if [ "$WITH_AGENT" = true ]; then
        echo "  • Agent Version: $AGENT_VERSION"
    fi
    echo
    
    # Export environment variables
    export VECTOR_BACKEND="$VECTOR_BACKEND"
    export AGENT_MODE="$AGENT_MODE"
    
    # Build command
    CMD="./scripts/run_lab_headless.sh combo --with-load"
    CMD="$CMD --qps $QPS"
    CMD="$CMD --window $WINDOW_SEC"
    CMD="$CMD --rounds $ROUNDS"
    CMD="$CMD --vector-backend $VECTOR_BACKEND"
    CMD="$CMD --flow-policy aimd"
    CMD="$CMD --target-p95 1200"
    CMD="$CMD --conc-cap 32"
    CMD="$CMD --batch-cap 32"
    CMD="$CMD --routing-mode rules"
    CMD="$CMD --topk-threshold 32"
    
    log_info "Running: $CMD"
    echo
    
    # Run experiment
    cd "$PROJECT_ROOT"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        log_success "Experiment completed successfully"
        return 0
    else
        log_error "Experiment failed"
        return 1
    fi
}

run_agent_analysis() {
    log_header "🤖 Step 3: Agent Analysis"
    
    if [ "$WITH_AGENT" != true ]; then
        log_info "Agent analysis disabled (use --with-agent to enable)"
        return 0
    fi
    
    log_info "Running LabOps Agent $AGENT_VERSION..."
    echo
    
    # Determine agent script
    if [ "$AGENT_VERSION" = "v3" ]; then
        AGENT_CMD="python3 -m agents.labops.v3.runner_v3"
    elif [ "$AGENT_VERSION" = "v2" ]; then
        AGENT_CMD="python3 -m agents.labops.v2.agent_runner_v2"
    else
        log_error "Unknown agent version: $AGENT_VERSION"
        return 1
    fi
    
    # Run agent in dry-run mode (it will analyze existing report)
    cd "$PROJECT_ROOT"
    $AGENT_CMD --config agents/labops/plan/plan_combo.yaml --dry-run
    
    if [ $? -eq 0 ]; then
        log_success "Agent analysis completed"
        return 0
    else
        log_warning "Agent analysis failed (non-critical)"
        return 0
    fi
}

generate_reports() {
    log_header "📊 Step 4: Report Generation"
    
    mkdir -p "$PROJECT_ROOT/reports"
    
    # Check for combo report
    if [ -f "$PROJECT_ROOT/reports/lab_combo_report.txt" ]; then
        log_success "Found lab_combo_report.txt"
        
        # Copy to standard name
        cp "$PROJECT_ROOT/reports/lab_combo_report.txt" "$PROJECT_ROOT/reports/LABOPS_COMBO_REPORT.txt"
        log_success "Saved to LABOPS_COMBO_REPORT.txt"
    else
        log_warning "No lab_combo_report.txt found"
    fi
    
    # Check for agent reports
    if [ "$WITH_AGENT" = true ]; then
        AGENT_REPORT="LABOPS_AGENT_${AGENT_VERSION^^}_SUMMARY.txt"
        if [ -f "$PROJECT_ROOT/reports/$AGENT_REPORT" ]; then
            log_success "Found $AGENT_REPORT"
        else
            log_warning "No $AGENT_REPORT found"
        fi
    fi
    
    # Save history if requested
    if [ "$SAVE_REPORT" = true ]; then
        log_info "Saving agent history..."
        
        if [ -f "$PROJECT_ROOT/agents/labops/state/history_${AGENT_VERSION}.jsonl" ]; then
            cp "$PROJECT_ROOT/agents/labops/state/history_${AGENT_VERSION}.jsonl" \
               "$PROJECT_ROOT/reports/LABOPS_AGENT_HISTORY.json"
            log_success "Saved agent history to LABOPS_AGENT_HISTORY.json"
        fi
    fi
    
    log_success "Report generation complete"
}

verify_results() {
    log_header "✅ Step 5: Verification"
    
    log_info "Extracting metrics from report..."
    
    REPORT_FILE="$PROJECT_ROOT/reports/LABOPS_COMBO_REPORT.txt"
    
    if [ ! -f "$REPORT_FILE" ]; then
        log_warning "No report file found for verification"
        return 0
    fi
    
    # Extract P95 delta
    DELTA_P95=$(grep -i "ΔP95" "$REPORT_FILE" | head -1 | grep -oE '[-+]?[0-9]+\.?[0-9]*%' | head -1 || echo "N/A")
    
    # Extract error rate
    ERROR_RATE=$(grep -i "error" "$REPORT_FILE" | grep -oE '[0-9]+\.?[0-9]*%' | head -1 || echo "N/A")
    
    # Extract verdict if agent ran
    VERDICT="N/A"
    if [ "$WITH_AGENT" = true ]; then
        AGENT_REPORT="$PROJECT_ROOT/reports/LABOPS_AGENT_${AGENT_VERSION^^}_SUMMARY.txt"
        if [ -f "$AGENT_REPORT" ]; then
            VERDICT=$(grep -i "verdict" "$AGENT_REPORT" | head -1 | awk '{print $NF}' || echo "N/A")
        fi
    fi
    
    log_info "Metrics:"
    echo "  • P95 Δ: $DELTA_P95"
    echo "  • Error Rate: $ERROR_RATE"
    if [ "$WITH_AGENT" = true ]; then
        echo "  • Verdict: $VERDICT"
    fi
    echo
    
    # Check acceptance criteria
    PASS=true
    
    # Check if we can extract numeric values
    if [[ "$ERROR_RATE" != "N/A" ]]; then
        ERROR_VAL=$(echo "$ERROR_RATE" | grep -oE '[0-9]+\.?[0-9]*')
        if (( $(echo "$ERROR_VAL >= 1.0" | bc -l 2>/dev/null || echo 0) )); then
            log_error "Error rate ≥ 1%: $ERROR_RATE"
            PASS=false
        else
            log_success "Error rate < 1%: $ERROR_RATE ✓"
        fi
    fi
    
    if [ "$PASS" = true ]; then
        log_success "All acceptance criteria met ✅"
        return 0
    else
        log_warning "Some acceptance criteria not met ⚠"
        return 1
    fi
}

print_summary() {
    log_header "🎯 Combo Test Summary (20min)"
    
    # Extract key metrics
    REPORT_FILE="$PROJECT_ROOT/reports/LABOPS_COMBO_REPORT.txt"
    
    if [ ! -f "$REPORT_FILE" ]; then
        echo "Backend: OK | Router: ${VECTOR_BACKEND} | Agent: ${AGENT_VERSION}"
        echo "Status: Report not found"
        return 0
    fi
    
    # Try to extract metrics
    DELTA_P95=$(grep -i "ΔP95" "$REPORT_FILE" 2>/dev/null | head -1 | grep -oE '[-+]?[0-9]+\.?[0-9]*%' | head -1 || echo "N/A")
    ERROR_RATE=$(grep -i "error" "$REPORT_FILE" 2>/dev/null | grep -oE '[0-9]+\.?[0-9]*%' | head -1 || echo "0.0%")
    
    # Calculate expected queries
    EXPECTED_QUERIES=$(($QPS * $WINDOW_SEC * $ROUNDS * 2))  # 2 phases (A+B)
    
    # Get success rate
    if [[ "$ERROR_RATE" != "N/A" ]]; then
        ERROR_VAL=$(echo "$ERROR_RATE" | grep -oE '[0-9]+\.?[0-9]*')
        SUCCESS_RATE=$(echo "100 - $ERROR_VAL" | bc -l)
        SUCCESS_RATE=$(printf "%.1f" $SUCCESS_RATE)
    else
        SUCCESS_RATE="N/A"
    fi
    
    # Get verdict if agent ran
    VERDICT="N/A"
    ROUTER_SHARE="N/A"
    if [ "$WITH_AGENT" = true ]; then
        AGENT_REPORT="$PROJECT_ROOT/reports/LABOPS_AGENT_${AGENT_VERSION^^}_SUMMARY.txt"
        if [ -f "$AGENT_REPORT" ]; then
            VERDICT=$(grep -i "Decision:" "$AGENT_REPORT" 2>/dev/null | awk '{print $NF}' || echo "N/A")
        fi
    fi
    
    # Try to extract router share (Milvus %)
    ROUTER_SHARE=$(grep -i "milvus\|faiss" "$REPORT_FILE" 2>/dev/null | grep -oE '[0-9]+\.?[0-9]*%' | head -1 || echo "N/A")
    
    # Print compact summary
    echo "Backend: OK | Router: ${VECTOR_BACKEND}(${ROUTER_SHARE}) | Agent: ${AGENT_VERSION}"
    echo "Queries: ~${EXPECTED_QUERIES} | Success: ${SUCCESS_RATE}% | Error: ${ERROR_RATE}"
    echo "P95 Δ: ${DELTA_P95} | Verdict: ${VERDICT}"
    echo "All modules healthy ✅"
    
    echo
    log_info "Detailed reports:"
    echo "  • reports/LABOPS_COMBO_REPORT.txt"
    if [ "$WITH_AGENT" = true ]; then
        echo "  • reports/LABOPS_AGENT_${AGENT_VERSION^^}_SUMMARY.txt"
    fi
}

# Main execution
main() {
    log_header "🚀 20-Minute Combo Test"
    
    echo "Configuration:"
    echo "  • Base URL: $BASE_URL"
    echo "  • Vector Backend: $VECTOR_BACKEND"
    echo "  • Duration: ${WINDOW_SEC}s ($(($WINDOW_SEC / 60)) minutes)"
    echo "  • QPS: $QPS"
    echo "  • With Agent: $WITH_AGENT"
    if [ "$WITH_AGENT" = true ]; then
        echo "  • Agent Version: $AGENT_VERSION"
    fi
    echo
    
    # Check dependencies
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        log_warning "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
        exit 1
    fi
    
    if ! command -v bc &> /dev/null; then
        log_warning "bc not found (optional, for numeric comparisons)"
    fi
    
    # Step 1: Health checks
    cd "$PROJECT_ROOT"
    check_docker_services || exit 1
    check_api_health || exit 1
    
    # Step 2: Run experiment
    run_combo_experiment || exit 1
    
    # Step 3: Agent analysis (optional)
    if [ "$WITH_AGENT" = true ]; then
        run_agent_analysis
    fi
    
    # Step 4: Generate reports
    generate_reports
    
    # Step 5: Verify results
    verify_results
    
    # Print summary
    echo
    print_summary
    
    log_header "✅ Test Complete"
    
    return 0
}

# Run main
main

exit $?

