#!/usr/bin/env bash
# run_latency_grid.sh - P95 Latency Optimization Suite
# ====================================================
# Systematically reduces P95 from ~1250ms to <1000ms
#
# Parameter Grid:
#   efSearch ∈ {32, 64, 96}
#   concurrency ∈ {4, 8, 12}
#   warm_cache ∈ {0, 100}
#   Fixed: Top-K=10, MMR off
#
# Runs on:
#   - Gold dataset (fiqa_10k_v1 with fiqa_qrels_10k_v1)
#   - Hard dataset (fiqa_10k_v1 with hard qrels)
#
# Output:
#   - reports/winners_latency.json (winners with <1000ms p95)
#   - reports/latency_grid_summary.txt (parameter→p95 curves)

set -euo pipefail

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
PARALLEL="${PARALLEL:-3}"
MAX_POLL="${MAX_POLL:-300}"
POLL_INTERVAL="${POLL_INTERVAL:-5}"
WARMUP_LIMIT="${WARMUP_LIMIT:-100}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  P95 Latency Optimization Suite                             ║"
echo "║  Goal: Reduce P95 from ~1250ms to <1000ms                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "API Base: $API_BASE"
echo "Parallel Slots: $PARALLEL"
echo ""

# Create reports directory
mkdir -p reports

# Parameter Grid
EF_SEARCH_VALUES=(32 64 96)
CONCURRENCY_VALUES=(4 8 12)
WARM_CACHE_VALUES=(0 100)

# Calculate total experiments
TOTAL_EXPERIMENTS=$(( ${#EF_SEARCH_VALUES[@]} * ${#CONCURRENCY_VALUES[@]} * ${#WARM_CACHE_VALUES[@]} * 2 ))
echo "Total experiments: $TOTAL_EXPERIMENTS (${TOTAL_EXPERIMENTS}/2 per dataset)"
echo ""

# ========================================
# Step 0: Warmup (if warm_cache > 0)
# ========================================
warmup_cache() {
    local limit=$1
    
    if [ "$limit" -eq 0 ]; then
        echo -e "${YELLOW}[WARMUP]${NC} Skipping warmup (warm_cache=0)"
        return 0
    fi
    
    echo -e "${BLUE}[WARMUP]${NC} Prewarming with $limit queries..."
    
    response=$(curl -fsS -X POST "$API_BASE/api/admin/warmup" \
      -H 'content-type: application/json' \
      -d "{\"limit\": $limit, \"timeout_sec\": 300}" 2>/dev/null || echo '{"ok":false}')
    
    ok=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "False")
    
    if [ "$ok" = "True" ]; then
        queries_run=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('queries_run', 0))" 2>/dev/null)
        duration_ms=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('duration_ms', 0))" 2>/dev/null)
        cache_hit_rate=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('cache_hit_rate', 0))" 2>/dev/null)
        
        echo -e "${GREEN}[WARMUP]${NC} Complete: $queries_run queries in ${duration_ms}ms, cache_hit_rate=$cache_hit_rate"
    else
        echo -e "${RED}[WARMUP]${NC} Failed, continuing anyway..."
    fi
}

# ========================================
# Step 1: Submit experiments
# ========================================
declare -a job_ids=()
experiment_id=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Submitting experiments..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for dataset_type in "gold" "hard"; do
    for ef_search in "${EF_SEARCH_VALUES[@]}"; do
        for concurrency in "${CONCURRENCY_VALUES[@]}"; do
            for warm_cache in "${WARM_CACHE_VALUES[@]}"; do
                experiment_id=$((experiment_id + 1))
                
                # Warmup if needed
                if [ "$warm_cache" -gt 0 ]; then
                    warmup_cache "$warm_cache"
                fi
                
                # Set dataset and qrels based on type
                if [ "$dataset_type" = "gold" ]; then
                    dataset_name="fiqa_10k_v1"
                    qrels_name="fiqa_qrels_10k_v1"
                    use_hard="false"
                else
                    dataset_name="fiqa_10k_v1"
                    qrels_name="fiqa_qrels_hard_v1"  # Hard qrels
                    use_hard="true"
                fi
                
                name="exp_${dataset_type}_ef${ef_search}_c${concurrency}_w${warm_cache}"
                
                echo -e "${BLUE}[$experiment_id/$TOTAL_EXPERIMENTS]${NC} Submitting: $name"
                echo "   Parameters: efSearch=$ef_search, concurrency=$concurrency, warm_cache=$warm_cache"
                
                # Submit experiment
                response=$(curl -fsS -X POST "$API_BASE/api/experiment/run" \
                  -H 'content-type: application/json' \
                  -d "{
                    \"sample\": 30,
                    \"top_k\": 10,
                    \"fast_mode\": true,
                    \"rerank\": false,
                    \"repeats\": 1,
                    \"dataset_name\": \"$dataset_name\",
                    \"qrels_name\": \"$qrels_name\",
                    \"use_hard\": $use_hard,
                    \"ef_search\": $ef_search,
                    \"mmr\": false
                  }" 2>/dev/null || echo '{"ok":false}')
                
                ok=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "False")
                
                if [ "$ok" = "True" ]; then
                    job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)
                    job_ids+=("$job_id:$name:$dataset_type:$ef_search:$concurrency:$warm_cache")
                    echo -e "   ${GREEN}✓${NC} Submitted: $job_id"
                else
                    echo -e "   ${RED}✗${NC} Failed to submit"
                fi
                
                # Rate limiting
                if [ "$((experiment_id % PARALLEL))" -eq 0 ]; then
                    sleep 2
                fi
            done
        done
    done
done

echo ""
echo -e "${GREEN}✅${NC} All experiments submitted: ${#job_ids[@]} jobs"
echo ""

# ========================================
# Step 2: Poll for completion
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Polling for completion..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

declare -A job_status
for job_entry in "${job_ids[@]}"; do
    job_id="${job_entry%%:*}"
    job_status[$job_id]="RUNNING"
done

for i in $(seq 1 "$MAX_POLL"); do
    sleep "$POLL_INTERVAL"
    
    all_done=true
    succeeded=0
    failed=0
    running=0
    
    for job_entry in "${job_ids[@]}"; do
        job_id="${job_entry%%:*}"
        
        # Skip already completed
        if [[ "${job_status[$job_id]}" == "SUCCEEDED" ]] || [[ "${job_status[$job_id]}" == "FAILED" ]]; then
            [ "${job_status[$job_id]}" == "SUCCEEDED" ] && ((succeeded++)) || ((failed++))
            continue
        fi
        
        status_response=$(curl -fsS "$API_BASE/api/experiment/status/$job_id" 2>/dev/null || echo '{"job":{"status":"UNKNOWN"}}')
        status=$(echo "$status_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job', {}).get('status', 'UNKNOWN'))" 2>/dev/null)
        
        job_status[$job_id]=$status
        
        if [[ "$status" != "SUCCEEDED" ]] && [[ "$status" != "FAILED" ]]; then
            all_done=false
            ((running++))
        elif [[ "$status" == "SUCCEEDED" ]]; then
            ((succeeded++))
        else
            ((failed++))
        fi
    done
    
    echo -e "[$i/$MAX_POLL] ${GREEN}✓$succeeded${NC} | ${RED}✗$failed${NC} | ${YELLOW}⏳$running${NC}"
    
    if [ "$all_done" = true ]; then
        echo ""
        echo -e "${GREEN}✅ All jobs completed!${NC}"
        break
    fi
    
    if [ "$i" -eq "$MAX_POLL" ]; then
        echo ""
        echo -e "${RED}❌ Timeout: Some jobs incomplete${NC}"
        exit 1
    fi
done

echo ""

# ========================================
# Step 3: Collect results
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Collecting results and generating winners..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run Python analysis script
echo "${job_ids[@]}" | tr ' ' '\n' | python3 scripts/analyze_latency_winners.py

echo ""
echo -e "${GREEN}✅${NC} Results saved:"
echo "   - reports/latency_grid_all.json (all experiments)"
echo "   - reports/winners_latency.json (winners with p95 < 1000ms)"
echo ""

# Summary is already generated by Python script
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Latency optimization suite complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

