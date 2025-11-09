#!/bin/bash
# Run MMR Grid Search: Top-K × λ
# Tests combinations of Top-K ∈ {10,20,30} and λ ∈ {0.1,0.3,0.5}

set -e

BASE_URL="${BASE:-http://localhost:8000}"
DATASET="${DATASET:-fiqa_10k_v1}"
QRELS="${QRELS:-fiqa_qrels_10k_v1}"
SAMPLE="${SAMPLE:-200}"
FAST_MODE="${FAST_MODE:-false}"

echo "=========================================="
echo "MMR Grid Search: Top-K × λ"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Dataset: $DATASET"
echo "Qrels: $QRELS"
echo "Sample: $SAMPLE"
echo "Fast Mode: $FAST_MODE"
echo ""

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/home/andy/searchforge/reports/mmr_grid_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Output Directory: $OUTPUT_DIR"
echo ""

# Grid parameters
TOP_KS=(10 20 30)
LAMBDAS=(0.1 0.3 0.5)

JOB_IDS=()

echo "Submitting ${#TOP_KS[@]} × ${#LAMBDAS[@]} = $((${#TOP_KS[@]} * ${#LAMBDAS[@]})) jobs..."
echo ""

# Submit all jobs
for top_k in "${TOP_KS[@]}"; do
    for lambda in "${LAMBDAS[@]}"; do
        label="topk${top_k}_lambda${lambda}"
        echo "[SUBMIT] Top-K=${top_k}, λ=${lambda} (${label})"
        
        # Submit job via API
        response=$(curl -s -X POST "${BASE_URL}/api/experiment/run" \
            -H "Content-Type: application/json" \
            -d "{
                \"dataset_name\": \"${DATASET}\",
                \"qrels_name\": \"${QRELS}\",
                \"sample\": ${SAMPLE},
                \"repeats\": 1,
                \"fast_mode\": ${FAST_MODE},
                \"overrides\": {
                    \"top_k\": ${top_k},
                    \"mmr\": true,
                    \"mmr_lambda\": ${lambda},
                    \"sample\": ${SAMPLE}
                }
            }")
        
        job_id=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('job_id', ''))")
        
        if [ -z "$job_id" ]; then
            echo "  ✗ Failed to submit job"
            echo "  Response: $response"
        else
            echo "  ✓ Job ID: $job_id"
            JOB_IDS+=("$job_id:$label")
        fi
        
        sleep 0.5
    done
done

echo ""
echo "=========================================="
echo "Submitted ${#JOB_IDS[@]} jobs. Waiting for completion..."
echo "=========================================="
echo ""

# Wait for all jobs to complete
MAX_WAIT_SEC=3600  # 1 hour max
POLL_INTERVAL=10
elapsed=0

while [ $elapsed -lt $MAX_WAIT_SEC ]; do
    completed=0
    running=0
    failed=0
    
    for job_entry in "${JOB_IDS[@]}"; do
        job_id="${job_entry%%:*}"
        label="${job_entry##*:}"
        
        status=$(curl -s "${BASE_URL}/api/experiment/status/${job_id}" | \
            python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('job', {}).get('status', 'UNKNOWN'))")
        
        case "$status" in
            SUCCEEDED)
                ((completed++))
                ;;
            FAILED)
                ((failed++))
                echo "  ✗ Job $job_id ($label) FAILED"
                ;;
            RUNNING|QUEUED)
                ((running++))
                ;;
        esac
    done
    
    echo "[$(date +'%H:%M:%S')] Progress: ${completed} completed, ${running} running, ${failed} failed (${#JOB_IDS[@]} total)"
    
    if [ $completed -eq ${#JOB_IDS[@]} ]; then
        echo ""
        echo "✅ All jobs completed successfully!"
        break
    fi
    
    if [ $((completed + failed)) -eq ${#JOB_IDS[@]} ]; then
        echo ""
        echo "⚠ All jobs finished with ${failed} failures"
        break
    fi
    
    sleep $POLL_INTERVAL
    elapsed=$((elapsed + POLL_INTERVAL))
done

if [ $elapsed -ge $MAX_WAIT_SEC ]; then
    echo ""
    echo "⚠ Timeout after ${MAX_WAIT_SEC}s"
fi

echo ""
echo "=========================================="
echo "Collecting Results..."
echo "=========================================="
echo ""

# Collect results from all jobs
RESULTS_FILE="${OUTPUT_DIR}/grid_results.jsonl"
> "$RESULTS_FILE"

for job_entry in "${JOB_IDS[@]}"; do
    job_id="${job_entry%%:*}"
    label="${job_entry##*:}"
    
    echo "[COLLECT] $label (job_id: $job_id)"
    
    # Get job detail with metrics
    job_detail=$(curl -s "${BASE_URL}/api/experiment/job/${job_id}")
    
    # Extract metrics
    status=$(echo "$job_detail" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'UNKNOWN'))")
    
    if [ "$status" = "SUCCEEDED" ]; then
        metrics=$(echo "$job_detail" | python3 -c "
import sys, json
data = json.load(sys.stdin)
metrics = data.get('metrics', {}).get('metrics', {})
config = data.get('config', {})
print(json.dumps({
    'job_id': data.get('job_id', ''),
    'label': '${label}',
    'top_k': config.get('top_k', 0),
    'mmr_lambda': config.get('mmr_lambda', 0),
    'recall_at_10': metrics.get('recall_at_10', 0),
    'p95_ms': metrics.get('p95_ms', 0),
    'qps': metrics.get('qps', 0),
    'status': 'SUCCEEDED'
}))
")
        echo "$metrics" >> "$RESULTS_FILE"
        echo "  ✓ Recall@10=$(echo "$metrics" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin)['recall_at_10']:.4f}\")")"
    else
        echo "  ✗ Status: $status"
        echo "{\"job_id\": \"${job_id}\", \"label\": \"${label}\", \"status\": \"${status}\"}" >> "$RESULTS_FILE"
    fi
done

echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""

# Generate winners report
echo "=========================================="
echo "Generating Winners Report..."
echo "=========================================="

python3 << 'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path
import os

# Read results
results_file = Path(os.environ.get('RESULTS_FILE', 'grid_results.jsonl'))
output_dir = Path(os.environ.get('OUTPUT_DIR', '.'))

if not results_file.exists():
    print(f"✗ Results file not found: {results_file}")
    sys.exit(1)

results = []
with open(results_file, 'r') as f:
    for line in f:
        if line.strip():
            results.append(json.loads(line))

# Filter successful results
successful = [r for r in results if r.get('status') == 'SUCCEEDED']

if not successful:
    print("✗ No successful jobs found")
    sys.exit(1)

print(f"✓ Loaded {len(successful)} successful results")
print()

# Sort by recall (descending)
by_recall = sorted(successful, key=lambda x: x.get('recall_at_10', 0), reverse=True)

# Sort by p95 (ascending - lower is better)
by_latency = sorted(successful, key=lambda x: x.get('p95_ms', float('inf')))

# Sort by QPS (descending)
by_qps = sorted(successful, key=lambda x: x.get('qps', 0), reverse=True)

# Calculate Pareto frontier (Recall@10 vs p95_ms)
# Higher recall is better, lower p95 is better
def is_dominated(candidate, others):
    """Check if candidate is dominated by any other point."""
    for other in others:
        if other is candidate:
            continue
        # other dominates candidate if:
        # - other has >= recall AND <= p95
        # - at least one is strictly better
        if (other['recall_at_10'] >= candidate['recall_at_10'] and 
            other['p95_ms'] <= candidate['p95_ms'] and
            (other['recall_at_10'] > candidate['recall_at_10'] or 
             other['p95_ms'] < candidate['p95_ms'])):
            return True
    return False

pareto_points = [r for r in successful if not is_dominated(r, successful)]
pareto_sorted = sorted(pareto_points, key=lambda x: x['recall_at_10'], reverse=True)

# Select winners (3 tiers)
# 省时档 (time-saving): Best latency
# 均衡档 (balanced): Best Pareto point (middle ground)
# 高质档 (high-quality): Best recall

winner_timesaving = by_latency[0] if by_latency else None
winner_quality = by_recall[0] if by_recall else None

# Balanced: pick middle Pareto point
if len(pareto_sorted) >= 3:
    winner_balanced = pareto_sorted[len(pareto_sorted) // 2]
elif len(pareto_sorted) == 2:
    winner_balanced = pareto_sorted[0]  # Favor recall
elif pareto_sorted:
    winner_balanced = pareto_sorted[0]
else:
    winner_balanced = None

# Build winners report
winners = {
    "schema_version": 1,
    "dataset": os.environ.get('DATASET', 'unknown'),
    "timestamp": os.environ.get('TIMESTAMP', ''),
    "total_configs": len(results),
    "successful_configs": len(successful),
    "winners": {
        "timesaving": {
            "label": winner_timesaving['label'],
            "top_k": winner_timesaving['top_k'],
            "mmr_lambda": winner_timesaving['mmr_lambda'],
            "recall_at_10": round(winner_timesaving['recall_at_10'], 4),
            "p95_ms": round(winner_timesaving['p95_ms'], 1),
            "qps": round(winner_timesaving['qps'], 2),
            "job_id": winner_timesaving['job_id']
        } if winner_timesaving else None,
        "balanced": {
            "label": winner_balanced['label'],
            "top_k": winner_balanced['top_k'],
            "mmr_lambda": winner_balanced['mmr_lambda'],
            "recall_at_10": round(winner_balanced['recall_at_10'], 4),
            "p95_ms": round(winner_balanced['p95_ms'], 1),
            "qps": round(winner_balanced['qps'], 2),
            "job_id": winner_balanced['job_id']
        } if winner_balanced else None,
        "quality": {
            "label": winner_quality['label'],
            "top_k": winner_quality['top_k'],
            "mmr_lambda": winner_quality['mmr_lambda'],
            "recall_at_10": round(winner_quality['recall_at_10'], 4),
            "p95_ms": round(winner_quality['p95_ms'], 1),
            "qps": round(winner_quality['qps'], 2),
            "job_id": winner_quality['job_id']
        } if winner_quality else None
    },
    "pareto_frontier": [
        {
            "label": p['label'],
            "top_k": p['top_k'],
            "mmr_lambda": p['mmr_lambda'],
            "recall_at_10": round(p['recall_at_10'], 4),
            "p95_ms": round(p['p95_ms'], 1),
            "qps": round(p['qps'], 2)
        }
        for p in pareto_sorted
    ],
    "all_results": [
        {
            "label": r['label'],
            "top_k": r['top_k'],
            "mmr_lambda": r['mmr_lambda'],
            "recall_at_10": round(r['recall_at_10'], 4),
            "p95_ms": round(r['p95_ms'], 1),
            "qps": round(r['qps'], 2)
        }
        for r in successful
    ]
}

# Save winners report
winners_file = output_dir / 'winners_topk_mmr.json'
with open(winners_file, 'w') as f:
    json.dump(winners, f, indent=2, ensure_ascii=False)

print(f"✓ Winners report saved to: {winners_file}")
print()

# Print summary
print("=" * 60)
print("WINNERS SUMMARY")
print("=" * 60)
print()

if winner_timesaving:
    print("🏆 省时档 (Time-Saving):")
    print(f"   Config: Top-K={winner_timesaving['top_k']}, λ={winner_timesaving['mmr_lambda']}")
    print(f"   Recall@10: {winner_timesaving['recall_at_10']:.4f}")
    print(f"   P95: {winner_timesaving['p95_ms']:.1f}ms")
    print()

if winner_balanced:
    print("⚖️  均衡档 (Balanced):")
    print(f"   Config: Top-K={winner_balanced['top_k']}, λ={winner_balanced['mmr_lambda']}")
    print(f"   Recall@10: {winner_balanced['recall_at_10']:.4f}")
    print(f"   P95: {winner_balanced['p95_ms']:.1f}ms")
    print()

if winner_quality:
    print("🎯 高质档 (High-Quality):")
    print(f"   Config: Top-K={winner_quality['top_k']}, λ={winner_quality['mmr_lambda']}")
    print(f"   Recall@10: {winner_quality['recall_at_10']:.4f}")
    print(f"   P95: {winner_quality['p95_ms']:.1f}ms")
    print()

print("=" * 60)
print(f"Pareto Frontier: {len(pareto_sorted)} configurations")
print("=" * 60)

for i, p in enumerate(pareto_sorted, 1):
    print(f"{i}. Top-K={p['top_k']}, λ={p['mmr_lambda']:.1f} → Recall@10={p['recall_at_10']:.4f}, P95={p['p95_ms']:.1f}ms")

print()
print("=" * 60)

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ MMR Grid Search Complete!"
echo "=========================================="
echo "Results: ${OUTPUT_DIR}/winners_topk_mmr.json"
echo ""

