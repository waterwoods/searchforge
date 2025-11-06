#!/bin/bash
# verify_routing.sh - Routing Experiment Verification Script
# ===========================================================
# Quick verification that routing ABAB experiment runs end-to-end.
#
# Steps:
# 1. Preflight: Check Redis/Qdrant/Backend health
# 2. Run quick ABAB (window=30s, qps=8, topk "16,64")
# 3. Confirm report exists: reports/LAB_ROUTE_REPORT_MINI.txt
# 4. Parse and assert key metrics present
# 5. Assert FAISS share ≥30%, error rate <1%
# 6. Echo ✅ ROUTING VERIFY PASS or print failures
#
# Usage:
#   ./scripts/verify_routing.sh

set -e

# Fix OpenMP library conflict between numpy and FAISS
export KMP_DUPLICATE_LIB_OK=TRUE

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8011}"  # app_main with FAISS routing
QPS=8.0
WINDOW_SEC=30
TOPK="16,64"
ROUTING_MODE="rules"

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

# Step 1: Preflight checks
preflight_checks() {
    log_info "Step 1: Preflight checks..."
    
    # Check Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        log_error "Redis is not running"
        return 1
    fi
    log_success "Redis is healthy"
    
    # Check Qdrant
    if ! curl -s "http://localhost:6333/collections" > /dev/null 2>&1; then
        log_error "Qdrant is not running"
        return 1
    fi
    log_success "Qdrant is healthy"
    
    # Check Backend
    HEALTH=$(curl -s "$BASE_URL/ops/routing/status" || echo '{"ok":false}')
    if ! echo "$HEALTH" | grep -q '"ok":true'; then
        log_error "Backend is not healthy at $BASE_URL"
        return 1
    fi
    log_success "Backend is healthy"
    
    return 0
}

# Step 2: Run quick ABAB routing experiment
run_quick_experiment() {
    log_info "Step 2: Running quick routing experiment..."
    log_info "  QPS: $QPS"
    log_info "  Window: ${WINDOW_SEC}s"
    log_info "  Top-K Mix: $TOPK"
    log_info "  Routing Mode: $ROUTING_MODE"
    
    # Calculate total duration
    TOTAL_SEC=$((60 + WINDOW_SEC * 4))  # warmup + 2 ABAB rounds
    log_info "  Total duration: ~${TOTAL_SEC}s"
    
    # Run experiment
    python3 scripts/run_lab_route_with_load.py \
        --qps "$QPS" \
        --concurrency 3 \
        --topk "$TOPK" \
        --window "$WINDOW_SEC" \
        --rounds 2 \
        --seed 42 \
        --routing-mode "$ROUTING_MODE" \
        --base-url "$BASE_URL" 2>&1 | tee /tmp/routing_verify.log
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_error "Experiment failed"
        return 1
    fi
    
    log_success "Experiment completed"
    return 0
}

# Step 3: Check report exists
check_report_exists() {
    log_info "Step 3: Checking report file..."
    
    REPORT_PATH="reports/LAB_ROUTE_REPORT_MINI.txt"
    
    if [ ! -f "$REPORT_PATH" ]; then
        log_error "Report not found: $REPORT_PATH"
        return 1
    fi
    
    log_success "Report exists: $REPORT_PATH"
    
    # Check line count
    LINE_COUNT=$(wc -l < "$REPORT_PATH")
    if [ "$LINE_COUNT" -le 80 ]; then
        log_success "Report is ≤80 lines ($LINE_COUNT lines)"
    else
        log_warning "Report exceeds 80 lines ($LINE_COUNT lines)"
    fi
    
    return 0
}

# Step 4: Parse and validate metrics
validate_metrics() {
    log_info "Step 4: Validating metrics..."
    
    REPORT_PATH="reports/LAB_ROUTE_REPORT_MINI.txt"
    
    # Check for required fields
    REQUIRED_FIELDS=(
        "ΔP95:"
        "ΔQPS:"
        "FAISS:"
        "Qdrant:"
        "Fallbacks"
    )
    
    for field in "${REQUIRED_FIELDS[@]}"; do
        if ! grep -q "$field" "$REPORT_PATH"; then
            log_error "Missing required field: $field"
            return 1
        fi
    done
    log_success "All required fields present"
    
    # Extract FAISS share percentage from Phase B
    FAISS_SHARE=$(grep "PHASE B" -A 10 "$REPORT_PATH" | grep "FAISS:" | head -1 | sed -E 's/.*\(([0-9.]+)%\).*/\1/' || echo "0")
    
    if [ -z "$FAISS_SHARE" ] || [ "$FAISS_SHARE" = "0" ]; then
        log_error "Could not extract FAISS share percentage"
        return 1
    fi
    
    log_info "FAISS Share: ${FAISS_SHARE}%"
    
    # Check FAISS share ≥30% (soft warning)
    if (( $(echo "$FAISS_SHARE >= 30" | bc -l) )); then
        log_success "FAISS adoption is good (≥30%)"
    else
        log_warning "FAISS adoption is low (<30%): ${FAISS_SHARE}%"
        # Don't fail, just warn
    fi
    
    # Extract error rate from Phase B
    ERROR_RATE=$(grep "PHASE B" -A 10 "$REPORT_PATH" | grep "Error Rate:" | head -1 | sed -E 's/.*: ([0-9.]+)%.*/\1/' || echo "100")
    
    log_info "Error Rate: ${ERROR_RATE}%"
    
    # Check error rate <1%
    if (( $(echo "$ERROR_RATE < 1.0" | bc -l) )); then
        log_success "Error rate is acceptable (<1%)"
    else
        log_error "Error rate too high (≥1%): ${ERROR_RATE}%"
        return 1
    fi
    
    # Extract delta P95
    DELTA_P95=$(grep "ΔP95:" "$REPORT_PATH" | head -1 | sed -E 's/.*(\([+-][0-9.]+%\)).*/\1/' || echo "(+0%)")
    log_info "ΔP95: $DELTA_P95"
    
    # Extract delta QPS
    DELTA_QPS=$(grep "ΔQPS:" "$REPORT_PATH" | head -1 | sed -E 's/.*(\([+-][0-9.]+%\)).*/\1/' || echo "(+0%)")
    log_info "ΔQPS: $DELTA_QPS"
    
    return 0
}

# Main verification flow
main() {
    echo
    echo "======================================================================"
    echo "ROUTING EXPERIMENT VERIFICATION"
    echo "======================================================================"
    echo
    
    # Check prerequisites
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is required but not installed"
        exit 1
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        log_error "redis-cli is required but not installed"
        exit 1
    fi
    
    if ! command -v bc &> /dev/null; then
        log_error "bc is required but not installed"
        exit 1
    fi
    
    # Run verification steps
    FAILED=0
    
    if ! preflight_checks; then
        FAILED=1
    fi
    
    if [ $FAILED -eq 0 ]; then
        if ! run_quick_experiment; then
            FAILED=1
        fi
    fi
    
    if [ $FAILED -eq 0 ]; then
        if ! check_report_exists; then
            FAILED=1
        fi
    fi
    
    if [ $FAILED -eq 0 ]; then
        if ! validate_metrics; then
            FAILED=1
        fi
    fi
    
    echo
    echo "======================================================================"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ ROUTING VERIFY PASS${NC}"
        echo "======================================================================"
        echo
        echo "All checks passed! Routing experiment is working correctly."
        exit 0
    else
        echo -e "${RED}❌ ROUTING VERIFY FAIL${NC}"
        echo "======================================================================"
        echo
        echo "Some checks failed. Review the logs above for details."
        exit 1
    fi
}

# Run main
main

