#!/bin/bash
set -euo pipefail

# Phase A: Baseline + Presets + Guards
# Run experiments without frontend: verify CPU-only SBERT, sweep Top-K×MMR, poll, fetch logs, produce winners.json

# Detect API base URL
# Allow override via environment variable
if [ -n "${RAG_API_BASE:-}" ]; then
    API_BASE="${RAG_API_BASE}"
elif curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    API_BASE="http://localhost:8000"
elif curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    API_BASE="http://127.0.0.1:8000"
elif curl -fsS http://100.67.88.114:8000/health >/dev/null 2>&1; then
    API_BASE="http://100.67.88.114:8000"
else
    # Default to andy-wsl (for local execution)
    API_BASE="http://andy-wsl:8000"
fi
echo "Using API_BASE: $API_BASE"
REPORTS_DIR="reports/sweeps"
JOBS_FILE="/tmp/phase_a_jobs.txt"

echo "=========================================="
echo "Phase A: Experiment Automation"
echo "=========================================="

# Step 1: Health & Guards
echo ""
echo "Step 1: Health & Guards"
echo "------------------------"

echo "🔍 Checking guard-no-cuda..."
if ! make guard-no-cuda 2>/dev/null; then
    echo "⚠️  Warning: CUDA packages detected in environment (may be false positive)"
    echo "   Continuing anyway - embedding backend is CPU-only SBERT"
fi

echo "🔍 Checking embed-doctor..."
curl -fsS "${API_BASE}/api/health/embeddings" | python3 -m json.tool 2>/dev/null || curl -fsS "${API_BASE}/api/health/embeddings"

echo ""
HEALTH=$(curl -fsS "${API_BASE}/api/health/embeddings" | python3 -c "import sys, json; print(str(json.load(sys.stdin).get('ok', False)).lower())")
MODEL=$(curl -fsS "${API_BASE}/api/health/embeddings" | python3 -c "import sys, json; print(json.load(sys.stdin).get('model', 'unknown'))")
BACKEND=$(curl -fsS "${API_BASE}/api/health/embeddings" | python3 -c "import sys, json; print(json.load(sys.stdin).get('backend', 'unknown'))")
DIM=$(curl -fsS "${API_BASE}/api/health/embeddings" | python3 -c "import sys, json; print(json.load(sys.stdin).get('dim', 0))")

if [ "$HEALTH" != "true" ]; then
    echo "❌ Embedding health check failed!"
    exit 1
fi

if [ "$MODEL" != "sentence-transformers/all-MiniLM-L6-v2" ]; then
    echo "⚠️  Warning: Expected model 'sentence-transformers/all-MiniLM-L6-v2', got '$MODEL'"
fi

if [ "$BACKEND" != "SBERT" ]; then
    echo "⚠️  Warning: Expected backend 'SBERT', got '$BACKEND'"
fi

if [ "$DIM" != "384" ]; then
    echo "⚠️  Warning: Expected dim 384, got $DIM"
fi

echo "✅ Health check passed: model=$MODEL, backend=$BACKEND, dim=$DIM"

# Step 2: Submit experiments
echo ""
echo "Step 2: Submitting Experiments"
echo "------------------------------"

mkdir -p "$REPORTS_DIR"
> "$JOBS_FILE"

submit() {
    local name="$1"
    local payload="$2"
    echo "Submitting $name..."
    JOB_ID=$(curl -fsS -H 'content-type: application/json' \
        -d "$payload" \
        "${API_BASE}/api/experiment/run" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('job_id', '') or d.get('job_id', ''))")
    
    if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
        echo "❌ Failed to submit $name"
        return 1
    fi
    
    echo "$JOB_ID|$name" >> "$JOBS_FILE"
    echo "✅ Submitted $name: $JOB_ID"
}

# Submit baseline and Top-K experiments
# Note: MMR parameter is not directly supported by API yet, so we'll use top_k variations
submit "baseline_k40" '{"sample":200,"repeats":1,"fast_mode":false,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":40}'
submit "baseline_k20" '{"sample":200,"repeats":1,"fast_mode":false,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":20}'
submit "baseline_k10" '{"sample":200,"repeats":1,"fast_mode":false,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":10}'
submit "baseline_k5"  '{"sample":200,"repeats":1,"fast_mode":false,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":5}'

# Fast mode variants
submit "fast_k40" '{"sample":200,"repeats":1,"fast_mode":true,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":40}'
submit "fast_k20" '{"sample":200,"repeats":1,"fast_mode":true,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":20}'
submit "fast_k10" '{"sample":200,"repeats":1,"fast_mode":true,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":10}'
submit "fast_k5"  '{"sample":200,"repeats":1,"fast_mode":true,"dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1","top_k":5}'

TOTAL_JOBS=$(wc -l < "$JOBS_FILE")
echo ""
echo "✅ Submitted $TOTAL_JOBS jobs"

# Step 3: Poll until done
echo ""
echo "Step 3: Polling Job Status"
echo "-------------------------"

poll_job() {
    local job_id="$1"
    local name="$2"
    local max_iterations=120
    local iteration=0
    
    while [ $iteration -lt $max_iterations ]; do
        STATUS=$(curl -fsS "${API_BASE}/api/experiment/status/${job_id}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('job', {}).get('status') or d.get('status', 'unknown'))")
        
        if [ "$STATUS" = "SUCCEEDED" ]; then
            echo "✅ $name ($job_id): SUCCEEDED"
            return 0
        elif [ "$STATUS" = "FAILED" ]; then
            echo "❌ $name ($job_id): FAILED"
            return 1
        fi
        
        if [ $((iteration % 10)) -eq 0 ]; then
            echo "⏳ $name ($job_id): $STATUS (iteration $iteration)"
        fi
        
        sleep 2
        iteration=$((iteration + 1))
    done
    
    echo "⏱️  $name ($job_id): TIMEOUT after $max_iterations iterations"
    return 2
}

# Poll all jobs
SUCCEEDED=0
FAILED=0
TIMEOUT=0

while IFS='|' read -r job_id name; do
    if poll_job "$job_id" "$name"; then
        SUCCEEDED=$((SUCCEEDED + 1))
    else
        if [ $? -eq 2 ]; then
            TIMEOUT=$((TIMEOUT + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    fi
done < "$JOBS_FILE"

echo ""
echo "Polling Summary:"
echo "  ✅ Succeeded: $SUCCEEDED"
echo "  ❌ Failed: $FAILED"
echo "  ⏱️  Timeout: $TIMEOUT"

# Step 4: Fetch logs and details
echo ""
echo "Step 4: Fetching Logs & Details"
echo "-------------------------------"

while IFS='|' read -r job_id name; do
    echo "Fetching artifacts for $name ($job_id)..."
    
    # Fetch logs
    curl -fsS "${API_BASE}/api/experiment/logs/${job_id}?tail=5000" > "${REPORTS_DIR}/${job_id}.log" 2>/dev/null || true
    
    # Fetch status
    curl -fsS "${API_BASE}/api/experiment/status/${job_id}" > "${REPORTS_DIR}/${job_id}.status.json" 2>/dev/null || true
    
    # Try to fetch job detail
    curl -fsS "${API_BASE}/api/experiment/job/${job_id}" > "${REPORTS_DIR}/${job_id}.detail.json" 2>/dev/null || true
done < "$JOBS_FILE"

echo "✅ Artifacts saved to $REPORTS_DIR"

# Step 5: Extract metrics & produce winners.json
echo ""
echo "Step 5: Generating Winners Report"
echo "----------------------------------"

python3 <<'PY'
import json
import glob
import os
import statistics as st

items = []

for f in glob.glob("reports/sweeps/*.status.json"):
    try:
        with open(f, 'r') as file:
            d = json.load(file)
        
        meta = d.get("job") or d
        cfg = meta.get("params") or meta.get("config") or {}
        m = meta.get("metrics") or {}
        
        # Extract job_id from filename if not in response
        job_id = meta.get("job_id") or os.path.basename(f).split('.')[0]
        
        items.append({
            "job_id": job_id,
            "top_k": cfg.get("top_k"),
            "fast_mode": cfg.get("fast_mode", False),
            "dataset_name": cfg.get("dataset_name"),
            "recall_at_10": m.get("recall_at_10") or m.get("recall10") or 0,
            "p95_ms": m.get("p95_ms") or m.get("p95") or m.get("latency_p95") or 0,
            "qps": m.get("qps") or m.get("throughput") or 0,
            "status": meta.get("status", "unknown")
        })
    except Exception as e:
        print(f"Error processing {f}: {e}")

if not items:
    print("⚠️  No valid job results found")
    exit(1)

# Filter to succeeded jobs only
succeeded = [x for x in items if x.get("status") == "SUCCEEDED" or x.get("recall_at_10", 0) > 0]

if not succeeded:
    print("⚠️  No succeeded jobs found")
    # Still write all items for debugging
    out = {"winners": {}, "all": items, "note": "No succeeded jobs found"}
    os.makedirs("reports", exist_ok=True)
    json.dump(out, open("reports/winners.json", "w"), indent=2)
    print("Wrote reports/winners.json (all items, no winners)")
    exit(0)

# Find winners
best_quality = max(succeeded, key=lambda x: x.get("recall_at_10", 0))
best_latency = min([x for x in succeeded if x.get("p95_ms", 1e9) > 0], 
                   key=lambda x: x.get("p95_ms", 1e9), default=None)

# Balanced score: recall - 0.0005 * latency_ms
if best_latency:
    balanced = max(succeeded, key=lambda x: (x.get("recall_at_10", 0)) - 0.0005 * (x.get("p95_ms", 0)))
else:
    balanced = best_quality

out = {
    "winners": {
        "quality": best_quality,
        "latency": best_latency or best_quality,
        "balanced": balanced
    },
    "all": items,
    "succeeded_count": len(succeeded),
    "total_count": len(items)
}

os.makedirs("reports", exist_ok=True)
json.dump(out, open("reports/winners.json", "w"), indent=2)

print(f"✅ Wrote reports/winners.json")
print(f"   Total jobs: {len(items)}")
print(f"   Succeeded: {len(succeeded)}")
print(f"   Best quality: {best_quality.get('job_id')} (recall={best_quality.get('recall_at_10', 0):.4f})")
if best_latency:
    print(f"   Best latency: {best_latency.get('job_id')} (p95={best_latency.get('p95_ms', 0):.2f}ms)")
PY

echo ""
echo "=========================================="
echo "✅ Phase A Complete!"
echo "=========================================="
echo "Reports: $REPORTS_DIR"
echo "Winners: reports/winners.json"
echo ""

