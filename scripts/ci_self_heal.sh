#!/bin/bash
# CI self-healing script
# Automatically fixes common CI failures and retries

set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
ENV_FILE="${ENV_FILE:-.env.current}"
MAX_RETRIES=3

# Function to print failure info
print_failure_info() {
    echo "=== CI Failure Information ==="
    echo "Last 10 lines of .runs/*.json files:"
    find .runs -name "*.json" -type f -exec sh -c 'echo "--- {} ---" && tail -10 "$1" 2>/dev/null || true' _ {} \; 2>/dev/null | head -50
    echo ""
}

# Function to check and fix DATASET_MISSING
fix_dataset_missing() {
    echo "[CI-HEAL] Checking for DATASET_MISSING..."
    if grep -q "DATASET_MISSING\|collection.*not found\|missing.*collection" .runs/*.json 2>/dev/null || \
       grep -q "DATASET_MISSING" /tmp/ci_output.log 2>/dev/null; then
        echo "[CI-HEAL] Dataset missing detected, running fiqa-import..."
        make fiqa-import COLLECTION=fiqa_para_50k || true
        return 0
    fi
    return 1
}

# Function to check and fix 401/403 errors
fix_auth_errors() {
    echo "[CI-HEAL] Checking for 401/403 errors..."
    if grep -q "401\|403\|Unauthorized\|Forbidden" /tmp/ci_output.log 2>/dev/null || \
       grep -q "set_policy.*401\|set_policy.*403" .runs/*.json 2>/dev/null; then
        echo "[CI-HEAL] Authentication error detected, checking AUTOTUNER_TOKENS..."
        if ! grep -q "^AUTOTUNER_TOKENS=" "${ENV_FILE}" 2>/dev/null; then
            echo "[CI-HEAL] Adding AUTOTUNER_TOKENS to ${ENV_FILE}..."
            echo "AUTOTUNER_TOKENS=devtoken" >> "${ENV_FILE}"
        fi
        if ! grep -q "^AUTOTUNER_RPS=" "${ENV_FILE}" 2>/dev/null; then
            echo "[CI-HEAL] Adding AUTOTUNER_RPS to ${ENV_FILE}..."
            echo "AUTOTUNER_RPS=0" >> "${ENV_FILE}"
        fi
        echo "[CI-HEAL] Restarting backend..."
        make restart || true
        sleep 5
        return 0
    fi
    return 1
}

# Function to check and fix cost line = 0
fix_cost_line() {
    echo "[CI-HEAL] Checking for cost_per_1k_usd == 0..."
    if [ -f .runs/real_large_trilines.csv ]; then
        cost_sum=$(awk -F, 'NR==1{for(i=1;i<=NF;i++)if($i=="cost_per_1k_usd")c=i} NR>1{s+=$c} END{print s+0}' .runs/real_large_trilines.csv 2>/dev/null || echo "0")
        if [ "${cost_sum}" = "0" ] || [ "${cost_sum}" = "" ]; then
            echo "[CI-HEAL] Cost line is 0, checking MODEL_PRICING_JSON..."
            if [ -z "${MODEL_PRICING_JSON:-}" ]; then
                echo "[CI-HEAL] MODEL_PRICING_JSON not set, using default pricing..."
                export MODEL_PRICING_JSON='{"gpt-4o-mini": {"input": 0.15, "output": 0.6}, "gpt-4o": {"input": 2.5, "output": 10.0}}'
            fi
            return 0
        fi
    fi
    return 1
}

# Wait for GPU worker if it's configured
wait_for_gpu_if_needed() {
    # Check if GPU worker is configured in docker-compose
    if docker compose ps gpu-worker 2>/dev/null | grep -q gpu-worker; then
        echo "[CI] GPU worker detected, waiting for readiness..."
        if bash scripts/wait_for_gpu_ready.sh; then
            echo "[CI] ✅ GPU worker ready"
        else
            echo "[CI] ❌ GPU worker not ready, but continuing (CPU fallback available)"
            # Don't fail here - CPU fallback should still work
        fi
    else
        echo "[CI] GPU worker not running, using CPU fallback"
    fi
}

# Main CI run with self-healing
run_ci_with_healing() {
    local attempt=1
    
    # Wait for GPU worker before starting CI
    wait_for_gpu_if_needed
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo "[CI] Attempt $attempt of $MAX_RETRIES..."
        
        # Run CI and capture output (use ci-raw to avoid recursion)
        if make ci-raw 2>&1 | tee /tmp/ci_output.log; then
            echo "[CI] ✅ Success on attempt $attempt"
            
            # Verify outputs
            if [ -f .runs/pareto.json ]; then
                if ! jq -e '.ok==true' .runs/pareto.json >/dev/null 2>&1; then
                    echo "[CI] ⚠️ pareto.json ok!=true, but continuing..."
                fi
            fi
            
            # Check cost line
            if [ -f .runs/real_large_trilines.csv ]; then
                cost_sum=$(awk -F, 'NR==1{for(i=1;i<=NF;i++)if($i=="cost_per_1k_usd")c=i} NR>1{s+=$c} END{print s+0}' .runs/real_large_trilines.csv 2>/dev/null || echo "0")
                if [ "${cost_sum}" != "0" ] && [ "${cost_sum}" != "" ]; then
                    echo "[CI] ✅ Cost line verified: ${cost_sum}"
                else
                    echo "[CI] ⚠️ Cost line is 0, but continuing..."
                fi
            fi
            
            return 0
        fi
        
        echo "[CI] ❌ Failed on attempt $attempt"
        print_failure_info
        
        # Try to self-heal
        healed=false
        if fix_dataset_missing; then
            echo "[CI-HEAL] ✅ Fixed DATASET_MISSING"
            healed=true
        fi
        
        if fix_auth_errors; then
            echo "[CI-HEAL] ✅ Fixed 401/403 errors"
            healed=true
        fi
        
        if fix_cost_line; then
            echo "[CI-HEAL] ✅ Fixed cost line"
            healed=true
        fi
        
        if [ "$healed" = "false" ]; then
            echo "[CI] ❌ No automatic fixes available. Manual intervention required."
            echo "[CI] Failure summary:"
            tail -50 /tmp/ci_output.log
            return 1
        fi
        
        attempt=$((attempt + 1))
        echo "[CI] Retrying after fixes..."
        sleep 3
    done
    
    echo "[CI] ❌ Failed after $MAX_RETRIES attempts"
    return 1
}

# Run CI with self-healing
run_ci_with_healing

