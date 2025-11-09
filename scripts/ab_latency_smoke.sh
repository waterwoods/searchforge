#!/usr/bin/env bash
# ab_latency_smoke.sh - A/B Latency Policy Validation
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  A/B Latency Policy Validation                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Load policies
baseline_ef=$(python3 -c "import json; print(json.load(open('configs/policies/policy_baseline.json'))['ef_search'])")
baseline_conc=$(python3 -c "import json; print(json.load(open('configs/policies/policy_baseline.json'))['concurrency'])")
baseline_topk=$(python3 -c "import json; print(json.load(open('configs/policies/policy_baseline.json'))['top_k'])")
baseline_mmr=$(python3 -c "import json; print(str(json.load(open('configs/policies/policy_baseline.json'))['mmr']).lower())")
baseline_lambda=$(python3 -c "import json; print(json.load(open('configs/policies/policy_baseline.json'))['mmr_lambda'])")

latency_ef=$(python3 -c "import json; print(json.load(open('configs/policies/policy_latency_v1.json'))['ef_search'])")
latency_conc=$(python3 -c "import json; print(json.load(open('configs/policies/policy_latency_v1.json'))['concurrency'])")
latency_topk=$(python3 -c "import json; print(json.load(open('configs/policies/policy_latency_v1.json'))['top_k'])")
latency_mmr=$(python3 -c "import json; print(str(json.load(open('configs/policies/policy_latency_v1.json'))['mmr']).lower())")
latency_lambda=$(python3 -c "import json; print(json.load(open('configs/policies/policy_latency_v1.json'))['mmr_lambda'])")
latency_warm=$(python3 -c "import json; print(json.load(open('configs/policies/policy_latency_v1.json'))['warm_cache'])")

echo "Baseline: ef=$baseline_ef, conc=$baseline_conc, topk=$baseline_topk"
echo "Latency:  ef=$latency_ef, conc=$latency_conc, topk=$latency_topk"
echo ""

# Warmup for latency_v1 (if warm_cache > 0)
if [ "$latency_warm" -gt 0 ]; then
    echo "🔥 Prewarming ($latency_warm queries)..."
    curl -fsS -X POST "$API_BASE/api/admin/warmup" \
      -H 'content-type: application/json' \
      -d "{\"limit\": $latency_warm}" > /dev/null 2>&1 || echo "   (warmup failed)"
fi

# Submit 4 experiments
echo "━━━ Submitting experiments ━━━"

submit() {
    local dataset=$1
    local qrels=$2
    local use_hard=$3
    local policy=$4
    local ef=$5
    local conc=$6
    local topk=$7
    local mmr=$8
    local lambda=$9
    
    response=$(curl -fsS -X POST "$API_BASE/api/experiment/run" \
      -H 'content-type: application/json' \
      -d "{
        \"sample\": 200,
        \"top_k\": $topk,
        \"fast_mode\": true,
        \"repeats\": 1,
        \"dataset_name\": \"$dataset\",
        \"qrels_name\": \"$qrels\",
        \"use_hard\": $use_hard,
        \"ef_search\": $ef,
        \"mmr\": $mmr,
        \"mmr_lambda\": $lambda
      }" 2>&1)
    
    job_id=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('job_id', 'NONE'))" 2>/dev/null || echo "NONE")
    echo "$job_id:$policy:$dataset:$use_hard"
}

job1=$(submit "fiqa_10k_v1" "fiqa_qrels_10k_v1" "false" "baseline" "$baseline_ef" "$baseline_conc" "$baseline_topk" "$baseline_mmr" "$baseline_lambda")
echo "  Gold Baseline: ${job1%%:*}"

job2=$(submit "fiqa_10k_v1" "fiqa_qrels_10k_v1" "false" "latency_v1" "$latency_ef" "$latency_conc" "$latency_topk" "$latency_mmr" "$latency_lambda")
echo "  Gold Latency:  ${job2%%:*}"

job3=$(submit "fiqa_10k_v1" "fiqa_qrels_10k_v1" "true" "baseline" "$baseline_ef" "$baseline_conc" "$baseline_topk" "$baseline_mmr" "$baseline_lambda")
echo "  Hard Baseline: ${job3%%:*}"

job4=$(submit "fiqa_10k_v1" "fiqa_qrels_10k_v1" "true" "latency_v1" "$latency_ef" "$latency_conc" "$latency_topk" "$latency_mmr" "$latency_lambda")
echo "  Hard Latency:  ${job4%%:*}"

# Save job list
echo "$job1"$'\n'"$job2"$'\n'"$job3"$'\n'"$job4" > /tmp/ab_jobs.txt

echo ""
echo "━━━ Waiting 60s for jobs to complete ━━━"
sleep 60

# Collect results immediately
echo ""
echo "━━━ Collecting results ━━━"

python3 << 'COLLECT'
import json
import subprocess
import sys

jobs = []
with open('/tmp/ab_jobs.txt') as f:
    for line in f:
        if line.strip() and ':' in line:
            jobs.append(line.strip())

results = []

for job_entry in jobs:
    parts = job_entry.split(':')
    if len(parts) < 4:
        continue
    
    job_id, policy, dataset, use_hard = parts
    
    if job_id == 'NONE':
        print(f"✗ {policy}/{dataset}: submission failed", file=sys.stderr)
        continue
    
    # Read metrics
    cmd = ['docker', 'compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.dev.yml',
           'exec', '-T', 'rag-api', 'cat', f'/app/.runs/{job_id}/metrics.json']
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, cwd='/home/andy/searchforge')
        metrics = json.loads(output)
        
        overall = metrics.get('metrics', {})
        
        result = {
            'job_id': job_id,
            'policy': policy,
            'dataset': 'hard' if use_hard == 'true' else 'gold',
            'recall_at_10': overall.get('recall_at_10', 0),
            'p95_ms': overall.get('p95_ms', 0),
            'qps': overall.get('qps', 0),
            'status': 'ok'
        }
        
        results.append(result)
        print(f"✓ {policy}/{result['dataset']}: recall={result['recall_at_10']:.3f}, p95={result['p95_ms']:.0f}ms", file=sys.stderr)
        
    except Exception as e:
        print(f"✗ {job_id}: {e}", file=sys.stderr)

# Save
with open('reports/ab_latency_results.json', 'w') as f:
    json.dump({'experiments': results, 'total': len(results)}, f, indent=2)

# Validation
baseline_gold = next((r for r in results if r['policy'] == 'baseline' and r['dataset'] == 'gold'), None)
latency_gold = next((r for r in results if r['policy'] == 'latency_v1' and r['dataset'] == 'gold'), None)

rollback_needed = False
reasons = []

if latency_gold and baseline_gold:
    if latency_gold['p95_ms'] > 1000:
        rollback_needed = True
        reasons.append(f"P95={latency_gold['p95_ms']:.0f}ms > 1000ms")
    
    if latency_gold['recall_at_10'] < baseline_gold['recall_at_10'] - 0.02:
        rollback_needed = True
        reasons.append(f"Recall drop={baseline_gold['recall_at_10'] - latency_gold['recall_at_10']:.3f} > 0.02")

if rollback_needed:
    print("\n" + "="*60, file=sys.stderr)
    print("🔴 ROLLBACK NEEDED", file=sys.stderr)
    print("="*60, file=sys.stderr)
    for r in reasons:
        print(f"   {r}", file=sys.stderr)
    
    # Rollback
    subprocess.run(['cp', 'configs/policies/policy_baseline.json', 'configs/policies/current_policy.json'],
                   cwd='/home/andy/searchforge', check=True)
    print("✅ Rolled back: current_policy.json <- policy_baseline.json", file=sys.stderr)
    sys.exit(1)
else:
    print("\n✅ Validation PASSED", file=sys.stderr)
COLLECT

echo ""
echo "✅ A/B Validation Complete"
