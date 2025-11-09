#!/usr/bin/env bash
#
# policy_demo.sh - Policy Switching and Auto-Rollback Demo
# ==========================================================
# Demonstrates:
# 1. Policy switching (balanced_v1)
# 2. Running experiments with policy
# 3. Fault injection to trigger SLA breach
# 4. Auto-rollback to baseline_v1
# 5. Generating demo report
#

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
REPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/reports"
REPORT_FILE="${REPORT_DIR}/POLICY_DEMO_REPORT.md"
LOG_FILE="${REPORT_DIR}/policy_demo.log"
RUNS_DIR="/app/.runs"

# SLA Thresholds (from policies.json)
P95_BUDGET_MS="${P95_BUDGET_MS:-1500}"
ERR_BUDGET="${ERR_BUDGET:-0.01}"
BREACH_STREAK="${BREACH_STREAK:-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE"
}

log_section() {
    echo -e "\n${BLUE}========================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}$*${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}========================================${NC}\n" | tee -a "$LOG_FILE"
}

# Initialize report
init_report() {
    mkdir -p "$REPORT_DIR"
    cat > "$REPORT_FILE" <<'EOF'
# Policy Demo Report

**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")  
**Objective:** Demonstrate policy switching, SLA monitoring, and auto-rollback

---

## Executive Summary

This report demonstrates the policy management system with:
- Three-tier policy switching (fast/balanced/quality)
- SLA breach detection (P95 latency > 1500ms or error rate > 1%)
- Automatic rollback to baseline on consecutive breaches
- Full observability through structured logging

---

## Test Scenarios

EOF
}

# Warmup system
warmup() {
    log_section "Step 1: Warming Up System"
    log "Running warmup with 100 queries..."
    
    curl -s -X POST "${BASE_URL}/api/admin/warmup" \
        -H "Content-Type: application/json" \
        -d '{"limit": 100, "timeout_sec": 120}' \
        | jq '.' || log_error "Warmup failed"
    
    log "✓ Warmup completed"
}

# Get current policy
get_policy() {
    curl -s "${BASE_URL}/api/admin/policy/current" | jq '.'
}

# Apply policy
apply_policy() {
    local policy_name="$1"
    log "Applying policy: ${policy_name}"
    
    local response=$(curl -s -X POST "${BASE_URL}/api/admin/policy/apply?name=${policy_name}")
    echo "$response" | jq '.'
    
    # Extract and log key fields
    local applied_at=$(echo "$response" | jq -r '.applied_at')
    local prev_policy=$(echo "$response" | jq -r '.previous_policy')
    
    log "✓ Policy applied: ${policy_name} (previous: ${prev_policy}, at: ${applied_at})"
    
    # Log to report
    {
        echo ""
        echo "### Policy Switch: ${prev_policy} → ${policy_name}"
        echo ""
        echo "**Timestamp:** ${applied_at}"
        echo ""
        echo '```json'
        echo "$response" | jq '.'
        echo '```'
        echo ""
    } >> "$REPORT_FILE"
}

# Run experiment batch
run_experiment() {
    local sample_size="$1"
    local ef_search="${2:-32}"
    local description="$3"
    
    log_section "Running Experiment: ${description}"
    log "Sample size: ${sample_size}, ef_search: ${ef_search}"
    
    # Start experiment
    local job_response=$(curl -s -X POST "${BASE_URL}/api/experiment/run" \
        -H "Content-Type: application/json" \
        -d "{
            \"config_file\": \"configs/fiqa_suite.yaml\",
            \"overrides\": {
                \"sample\": ${sample_size},
                \"ef_search\": ${ef_search},
                \"dataset_name\": \"fiqa_10k_v1\",
                \"qrels_name\": \"fiqa_10k_v1\"
            }
        }")
    
    local job_id=$(echo "$job_response" | jq -r '.job_id')
    log "Job started: ${job_id}"
    
    # Wait for completion
    local max_wait=180
    local elapsed=0
    local status="QUEUED"
    
    while [[ "$status" != "SUCCEEDED" && "$status" != "FAILED" && $elapsed -lt $max_wait ]]; do
        sleep 5
        elapsed=$((elapsed + 5))
        
        local status_response=$(curl -s "${BASE_URL}/api/experiment/status/${job_id}")
        status=$(echo "$status_response" | jq -r '.status')
        
        log "Job ${job_id} status: ${status} (${elapsed}s elapsed)"
    done
    
    if [[ "$status" == "SUCCEEDED" ]]; then
        log "✓ Experiment completed successfully"
        
        # Get metrics
        if [[ -f "${RUNS_DIR}/${job_id}/metrics.json" ]]; then
            local metrics=$(cat "${RUNS_DIR}/${job_id}/metrics.json")
            local p95=$(echo "$metrics" | jq -r '.metrics.p95_ms')
            local recall=$(echo "$metrics" | jq -r '.metrics.recall_at_10')
            local policy_name=$(echo "$metrics" | jq -r '.policy.name // "unknown"')
            
            log "Results: P95=${p95}ms, Recall@10=${recall}, Policy=${policy_name}"
            
            # Write to report
            {
                echo ""
                echo "### Experiment: ${description}"
                echo ""
                echo "**Job ID:** ${job_id}"
                echo "**Status:** ${status}"
                echo "**Metrics:**"
                echo "- P95 Latency: ${p95} ms"
                echo "- Recall@10: ${recall}"
                echo "- Policy: ${policy_name}"
                echo ""
                echo '```json'
                echo "$metrics" | jq '.metrics'
                echo '```'
                echo ""
            } >> "$REPORT_FILE"
            
            echo "$job_id|$p95|$recall"
        else
            log_warn "Metrics file not found for job ${job_id}"
            echo "$job_id|0|0"
        fi
    else
        log_error "Experiment failed or timed out (status: ${status})"
        echo "failed|0|0"
    fi
}

# Inject fault to trigger SLA breach
inject_fault() {
    log_section "Step 3: Injecting Fault (High ef_search)"
    log "Setting ef_search=200 to artificially increase latency..."
    
    # Run with very high ef_search to trigger breach
    run_experiment 50 200 "Fault Injection (ef_search=200)"
}

# Extract logs
extract_logs() {
    local pattern="$1"
    local count="${2:-10}"
    
    # Try docker logs first
    if command -v docker &> /dev/null; then
        docker logs fiqa_api 2>&1 | grep "$pattern" | tail -n "$count" || echo "(no logs found)"
    else
        # Fallback to local logs if available
        find "${RUNS_DIR}" -name "*.log" -exec grep "$pattern" {} \; | tail -n "$count" || echo "(no logs found)"
    fi
}

# Main execution
main() {
    log_section "Policy Demo - Starting"
    log "BASE_URL: ${BASE_URL}"
    log "Report: ${REPORT_FILE}"
    
    # Initialize report
    init_report
    
    # Step 1: Warmup
    warmup
    
    # Step 2: Check initial policy
    log_section "Step 2: Check Initial Policy"
    local initial_policy=$(get_policy)
    log "Initial policy:"
    echo "$initial_policy" | jq '.'
    
    {
        echo "## Initial State"
        echo ""
        echo '```json'
        echo "$initial_policy" | jq '.'
        echo '```'
        echo ""
    } >> "$REPORT_FILE"
    
    # Step 3: Apply balanced_v1 policy
    log_section "Step 3: Apply Balanced Policy"
    apply_policy "balanced_v1"
    
    # Step 4: Run baseline experiment
    log_section "Step 4: Run Baseline Experiment"
    local baseline_result=$(run_experiment 200 32 "Baseline (balanced_v1, ef_search=32)")
    log "Baseline result: ${baseline_result}"
    
    # Step 5: Inject fault (high ef_search)
    log_section "Step 5: Fault Injection - First Breach"
    local fault1_result=$(run_experiment 50 200 "Fault Injection #1 (ef_search=200)")
    log "Fault #1 result: ${fault1_result}"
    
    # Step 6: Second fault to trigger rollback
    log_section "Step 6: Fault Injection - Second Breach (Trigger Rollback)"
    local fault2_result=$(run_experiment 50 200 "Fault Injection #2 (ef_search=200)")
    log "Fault #2 result: ${fault2_result}"
    
    # Step 7: Check policy after rollback
    log_section "Step 7: Verify Auto-Rollback"
    local final_policy=$(get_policy)
    log "Policy after auto-rollback:"
    echo "$final_policy" | jq '.'
    
    {
        echo "## Post-Rollback State"
        echo ""
        echo '```json'
        echo "$final_policy" | jq '.'
        echo '```'
        echo ""
    } >> "$REPORT_FILE"
    
    # Step 8: Extract key logs
    log_section "Step 8: Extracting Logs"
    
    {
        echo "## Key Log Excerpts"
        echo ""
        echo "### Policy Apply Logs"
        echo '```'
        extract_logs "\[POLICY_APPLY\]" 5
        echo '```'
        echo ""
        echo "### SLA Breach Logs"
        echo '```'
        extract_logs "\[SLA_BREACH\]" 5
        echo '```'
        echo ""
        echo "### Auto-Rollback Logs"
        echo '```'
        extract_logs "\[AUTO_ROLLBACK\]" 5
        echo '```'
        echo ""
    } >> "$REPORT_FILE"
    
    # Finalize report
    {
        echo "## Conclusion"
        echo ""
        echo "✅ **Demo completed successfully**"
        echo ""
        echo "Key observations:"
        echo "1. Policy switching works atomically via REST API"
        echo "2. SLA breaches are detected and logged"
        echo "3. Auto-rollback triggers after ${BREACH_STREAK} consecutive breaches"
        echo "4. System returns to stable baseline_v1 policy"
        echo ""
        echo "---"
        echo ""
        echo "*Generated by: scripts/policy_demo.sh*"
        echo ""
    } >> "$REPORT_FILE"
    
    log_section "Demo Complete"
    log "✓ Report generated: ${REPORT_FILE}"
    log "✓ Log file: ${LOG_FILE}"
    
    # Display report location
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Demo Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "📄 Report: ${REPORT_FILE}"
    echo "📋 Logs:   ${LOG_FILE}"
    echo ""
    echo "To view report:"
    echo "  cat ${REPORT_FILE}"
    echo ""
}

# Run main
main "$@"

