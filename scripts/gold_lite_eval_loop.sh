#!/bin/bash
set -euo pipefail

# Gold-Lite Evaluation Loop
# 完整评估循环：体检 → 生成薄金标 → 更新presets → 运行实验 → 收集指标

# Variables (adjust only if truly different)
# Detect if running locally or remotely
if [ -z "${RUNNING_REMOTELY:-}" ]; then
    export REMOTE=andy-wsl
    export RBASE=~/searchforge
    USE_SSH=true
else
    # Running on remote, don't use SSH
    export REMOTE=""
    export RBASE=$(pwd)
    USE_SSH=false
fi

export DATASET=${DATASET:-fiqa_50k_v1}
export QRELS=${QRELS:-fiqa_qrels_50k_v1}
export QRELS_GOLD=${QRELS_GOLD:-fiqa_gold_50k_v1}
export API_BASE=${API_BASE:-http://127.0.0.1:8000}

echo "=========================================="
echo "  Gold-Lite Evaluation Loop"
echo "=========================================="
echo "REMOTE: $REMOTE"
echo "RBASE: $RBASE"
echo "DATASET: $DATASET"
echo "QRELS: $QRELS"
echo "QRELS_GOLD: $QRELS_GOLD"
echo "API_BASE: $API_BASE"
echo "=========================================="
echo ""

# Helper: Print evidence on failure
print_evidence() {
    local step="$1"
    local error="$2"
    echo ""
    echo "❌ $step failed: $error"
    echo "=========================================="
    echo "Evidence:"
    case "$step" in
        "worker_check")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api sh -lc 'ps aux | grep \"python.*uvicorn\" | grep -v grep'"
                ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api sh -lc 'echo \$UVICORN_WORKERS'"
            else
                docker compose exec -T rag-api sh -lc 'ps aux | grep "python.*uvicorn" | grep -v grep' || true
                docker compose exec -T rag-api sh -lc 'echo $UVICORN_WORKERS' || true
            fi
            ;;
        "health_check")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && curl -fsS $API_BASE/api/health/embeddings 2>&1 || curl -fsS http://localhost:8000/api/health/embeddings 2>&1"
            else
                curl -fsS $API_BASE/api/health/embeddings 2>&1 || curl -fsS http://localhost:8000/api/health/embeddings 2>&1
            fi
            ;;
        "cuda_check")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api pip freeze | grep -iE '(nvidia|cuda|torch.*cuda)' || echo 'No CUDA packages found'"
            else
                docker compose exec -T rag-api pip freeze | grep -iE '(nvidia|cuda|torch.*cuda)' || echo 'No CUDA packages found'
            fi
            ;;
        "qrels_doctor")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && cat reports/qrels_doctor_${DATASET}.json 2>&1 || echo 'Report not found'"
            else
                cat reports/qrels_doctor_${DATASET}.json 2>&1 || echo 'Report not found'
            fi
            ;;
        "consistency")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && cat reports/consistency_${DATASET}.json 2>&1 || echo 'Report not found'"
            else
                cat reports/consistency_${DATASET}.json 2>&1 || echo 'Report not found'
            fi
            ;;
        "embed_doctor")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && cat reports/embed_doctor_${DATASET}.json 2>&1 || echo 'Report not found'"
            else
                cat reports/embed_doctor_${DATASET}.json 2>&1 || echo 'Report not found'
            fi
            ;;
        "experiment")
            if [ "$USE_SSH" = "true" ]; then
                ssh $REMOTE "cd $RBASE && tail -n 80 .runs/*/logs/*.log 2>&1 | head -n 160 || echo 'No logs found'"
            else
                tail -n 80 .runs/*/logs/*.log 2>&1 | head -n 160 || echo 'No logs found'
            fi
            ;;
    esac
    echo "=========================================="
}

# Phase 0: Sanity & Environment
echo "Phase 0: Sanity & Environment"
echo "-----------------------------"

echo "0.1) Verifying single worker..."
# Count actual python uvicorn processes (exclude tini and sh)
if [ "$USE_SSH" = "true" ]; then
    WORKERS=$(ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api sh -lc 'ps aux | grep python | grep uvicorn | grep -v tini | grep -v \"sh -lc\" | wc -l'")
else
    WORKERS=$(docker compose exec -T rag-api sh -lc 'ps aux | grep python | grep uvicorn | grep -v tini | grep -v "sh -lc" | wc -l' 2>/dev/null || echo "0")
fi
if [ "$WORKERS" != "1" ]; then
    echo "⚠️  Multiple workers detected: $WORKERS"
    echo "   Setting UVICORN_WORKERS=1..."
    if [ "$USE_SSH" = "true" ]; then
        ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api sh -lc 'export UVICORN_WORKERS=1'"
        ssh $REMOTE "cd $RBASE && docker compose restart rag-api"
    else
        docker compose exec -T rag-api sh -lc 'export UVICORN_WORKERS=1' || true
        docker compose restart rag-api || true
    fi
    sleep 5
    if [ "$USE_SSH" = "true" ]; then
        WORKERS=$(ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api sh -lc 'ps aux | grep python | grep uvicorn | grep -v tini | grep -v \"sh -lc\" | wc -l'")
    else
        WORKERS=$(docker compose exec -T rag-api sh -lc 'ps aux | grep python | grep uvicorn | grep -v tini | grep -v "sh -lc" | wc -l' 2>/dev/null || echo "0")
    fi
    if [ "$WORKERS" != "1" ]; then
        print_evidence "worker_check" "Still multiple workers after restart"
        exit 1
    fi
fi
echo "✅ Single worker confirmed: $WORKERS"
echo ""

echo "0.2) Health & model check..."
if [ "$USE_SSH" = "true" ]; then
    HEALTH=$(ssh $REMOTE "cd $RBASE && curl -fsS $API_BASE/api/health/embeddings 2>&1 | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d.get(\"ok\", False))' 2>/dev/null || echo 'false'")
    MODEL=$(ssh $REMOTE "cd $RBASE && curl -fsS $API_BASE/api/health/embeddings 2>&1 | python3 -c 'import sys, json; print(json.load(sys.stdin).get(\"model\", \"unknown\"))' 2>/dev/null")
else
    HEALTH=$(curl -fsS $API_BASE/api/health/embeddings 2>&1 | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d.get("ok", False))' 2>/dev/null || echo 'false')
    MODEL=$(curl -fsS $API_BASE/api/health/embeddings 2>&1 | python3 -c 'import sys, json; print(json.load(sys.stdin).get("model", "unknown"))' 2>/dev/null)
fi
if [ "$HEALTH" != "True" ]; then
    print_evidence "health_check" "Health check failed"
    exit 1
fi
echo "✅ Health check passed: model=$MODEL"
echo ""

echo "0.3) No CUDA guard..."
if [ "$USE_SSH" = "true" ]; then
    if ! ssh $REMOTE "cd $RBASE && docker compose exec -T rag-api python3 tools/guards/check_no_cuda.py" 2>&1; then
        print_evidence "cuda_check" "CUDA packages detected"
        exit 1
    fi
else
    if ! docker compose exec -T rag-api python3 tools/guards/check_no_cuda.py 2>&1; then
        print_evidence "cuda_check" "CUDA packages detected"
        exit 1
    fi
fi
echo "✅ No CUDA packages found"
echo ""

# Phase 1: "体检"三件套
echo "Phase 1: Health Checks (三件套)"
echo "-------------------------------"

# Resolve qrels file path
QRELS_FILE="experiments/data/fiqa/${QRELS}.tsv"
if [ "$USE_SSH" = "true" ]; then
    if ! ssh $REMOTE "cd $RBASE && test -f $QRELS_FILE"; then
        # Try alternative paths
        for alt in "experiments/data/fiqa/${DATASET}_qrels.tsv" "data/fiqa/${QRELS}.tsv"; do
            if ssh $REMOTE "cd $RBASE && test -f $alt"; then
                QRELS_FILE="$alt"
                break
            fi
        done
    fi
else
    if [ ! -f "$QRELS_FILE" ]; then
        # Try alternative paths
        for alt in "experiments/data/fiqa/${DATASET}_qrels.tsv" "data/fiqa/${QRELS}.tsv"; do
            if [ -f "$alt" ]; then
                QRELS_FILE="$alt"
                break
            fi
        done
    fi
fi
COLLECTION="fiqa_50k_v1"  # Default, can be overridden

echo "1.A) Qrels coverage check..."
if [ "$USE_SSH" = "true" ]; then
    if ! ssh $REMOTE "cd $RBASE && python3 tools/eval/qrels_doctor.py \
      --qrels $QRELS_FILE \
      --collection $COLLECTION \
      --api $API_BASE \
      --out reports/qrels_doctor_${DATASET}.json" 2>&1; then
        print_evidence "qrels_doctor" "Coverage < 0.99 or type mismatch"
        exit 1
    fi
else
    if ! python3 tools/eval/qrels_doctor.py \
      --qrels $QRELS_FILE \
      --collection $COLLECTION \
      --api $API_BASE \
      --out reports/qrels_doctor_${DATASET}.json 2>&1; then
        print_evidence "qrels_doctor" "Coverage < 0.99 or type mismatch"
        exit 1
    fi
fi
echo "✅ Qrels coverage check passed"
echo ""

echo "1.B) Data consistency check..."
if [ "$USE_SSH" = "true" ]; then
    if ! ssh $REMOTE "cd $RBASE && python3 tools/eval/consistency_check.py \
      --dataset-name $DATASET \
      --qrels-name $QRELS \
      --out reports/consistency_${DATASET}.json" 2>&1; then
        print_evidence "consistency" "Field mismatch"
        exit 1
    fi
else
    if ! python3 tools/eval/consistency_check.py \
      --dataset-name $DATASET \
      --qrels-name $QRELS \
      --out reports/consistency_${DATASET}.json 2>&1; then
        print_evidence "consistency" "Field mismatch"
        exit 1
    fi
fi
echo "✅ Data consistency check passed"
echo ""

echo "1.C) Embedding model consistency check..."
if [ "$USE_SSH" = "true" ]; then
    if ! ssh $REMOTE "cd $RBASE && python3 tools/eval/embed_doctor.py \
      --api-url $API_BASE \
      --collection $COLLECTION \
      --dataset-name $DATASET \
      --out reports/embed_doctor_${DATASET}.json" 2>&1; then
        print_evidence "embed_doctor" "Model/dimension mismatch"
        exit 1
    fi
else
    if ! python3 tools/eval/embed_doctor.py \
      --api-url $API_BASE \
      --collection $COLLECTION \
      --dataset-name $DATASET \
      --out reports/embed_doctor_${DATASET}.json 2>&1; then
        print_evidence "embed_doctor" "Model/dimension mismatch"
        exit 1
    fi
fi
echo "✅ Embedding model consistency check passed"
echo ""

# Phase 2: Generate gold candidates
echo "Phase 2: Generate Gold Candidates"
echo "---------------------------------"

echo "2.1) Building candidates (merge vec+bm25, dedup by doc_id), sample 300..."
if ! ssh $REMOTE "cd $RBASE && python3 tools/eval/generate_gold_candidates.py \
  --dataset-name $DATASET \
  --qrels-name $QRELS \
  --api-base $API_BASE \
  --limit 300 \
  --out reports/gold_candidates_${DATASET}.csv" 2>&1; then
    echo "❌ Candidate generation failed"
    exit 1
fi
echo "✅ Candidates generated: reports/gold_candidates_${DATASET}.csv"
echo ""

echo "2.2) Human labeling required..."
echo "⚠️  Please open reports/gold_candidates_${DATASET}.csv and mark obvious positives with label=1"
echo "   Keep it lightweight (200-500 rows)"
read -p "Press Enter after labeling is complete..."
echo ""

# Phase 3: Finalize gold qrels and update presets
echo "Phase 3: Finalize Gold Qrels & Update Presets"
echo "----------------------------------------------"

echo "3.1) Finalizing gold qrels..."
if ! ssh $REMOTE "cd $RBASE && python3 tools/eval/gold_finalize.py \
  --labels reports/gold_candidates_${DATASET}.csv \
  --out reports/qrels_gold_${DATASET}.tsv" 2>&1; then
    echo "❌ Gold qrels generation failed"
    exit 1
fi
echo "✅ Gold qrels generated: reports/qrels_gold_${DATASET}.tsv"
echo ""

echo "3.2) Updating presets..."
if ! ssh $REMOTE "cd $RBASE && DATASET_NAME=$DATASET QRELS_NAME=$QRELS_GOLD python3 tools/eval/update_presets_gold.py \
  --presets-file configs/presets_v10.json \
  --gold-qrels-name $QRELS_GOLD \
  --dataset-name $DATASET \
  --out configs/presets_v10.json" 2>&1; then
    echo "❌ Preset update failed"
    exit 1
fi
echo "✅ Presets updated"
echo ""

echo "3.3) Restarting API to load presets..."
ssh $REMOTE "cd $RBASE && docker compose restart rag-api"
sleep 5
echo "✅ API restarted"
echo ""

# Phase 4: Minimal experiments
echo "Phase 4: Minimal Experiments"
echo "----------------------------"

echo "4.1) Submitting experiments (Baseline fast/off × top_k∈{10,20})..."
ssh $REMOTE "cd $RBASE && API_BASE=$API_BASE DATASET=$DATASET QRELS=$QRELS_GOLD bash -" <<'REMOTE_SCRIPT'
    JOBS_FILE="/tmp/gold_lite_jobs.txt"
    > "$JOBS_FILE"
    
    submit() {
        local name="$1"
        local payload="$2"
        echo "Submitting $name..."
        JOB_ID=$(curl -fsS -H 'content-type: application/json' \
            -d "$payload" \
            "${API_BASE}/api/experiment/run" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")
        
        if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
            echo "❌ Failed to submit $name"
            return 1
        fi
        
        echo "$JOB_ID|$name" >> "$JOBS_FILE"
        echo "✅ Submitted $name: $JOB_ID"
    }
    
    # Submit 4 jobs: fast/off × top_k∈{10,20}
    submit "baseline_k10" "{\"sample\":200,\"repeats\":1,\"fast_mode\":false,\"dataset_name\":\"${DATASET}\",\"qrels_name\":\"${QRELS}\",\"top_k\":10}"
    submit "baseline_k20" "{\"sample\":200,\"repeats\":1,\"fast_mode\":false,\"dataset_name\":\"${DATASET}\",\"qrels_name\":\"${QRELS}\",\"top_k\":20}"
    submit "fast_k10" "{\"sample\":200,\"repeats\":1,\"fast_mode\":true,\"dataset_name\":\"${DATASET}\",\"qrels_name\":\"${QRELS}\",\"top_k\":10}"
    submit "fast_k20" "{\"sample\":200,\"repeats\":1,\"fast_mode\":true,\"dataset_name\":\"${DATASET}\",\"qrels_name\":\"${QRELS}\",\"top_k\":20}"
    
    echo "✅ Submitted $(wc -l < $JOBS_FILE) jobs"
REMOTE_SCRIPT
echo ""

echo "4.2) Polling until done..."
ssh $REMOTE "cd $RBASE && API_BASE=$API_BASE bash -" <<'REMOTE_SCRIPT'
    JOBS_FILE="/tmp/gold_lite_jobs.txt"
    
    poll_job() {
        local job_id="$1"
        local name="$2"
        local max_iterations=120
        local iteration=0
        
        while [ $iteration -lt $max_iterations ]; do
            STATUS=$(curl -fsS "${API_BASE}/api/experiment/status/${job_id}" 2>/dev/null | \
                python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('job', {}).get('status') or d.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
            
            if [ "$STATUS" = "SUCCEEDED" ]; then
                echo "✅ $name ($job_id): SUCCEEDED"
                return 0
            elif [ "$STATUS" = "FAILED" ]; then
                echo "❌ $name ($job_id): FAILED"
                return 1
            fi
            
            if [ $((iteration % 10)) -eq 0 ]; then
                echo "⏳ $name ($job_id): $STATUS"
            fi
            
            sleep 2
            iteration=$((iteration + 1))
        done
        
        echo "⏱️  $name ($job_id): TIMEOUT"
        # Print last 80 lines of logs
        echo "Last 80 lines of logs:"
        curl -fsS "${API_BASE}/api/experiment/logs/${job_id}?tail=80" 2>/dev/null | tail -n 80 || echo "Could not fetch logs"
        return 2
    }
    
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
    
    echo "Summary: ✅ Succeeded: $SUCCEEDED, ❌ Failed: $FAILED, ⏱️  Timeout: $TIMEOUT"
REMOTE_SCRIPT

if [ $? -ne 0 ]; then
    print_evidence "experiment" "Some jobs failed or timed out"
    # Continue anyway to collect metrics
fi
echo ""

# Phase 5: Collect metrics
echo "Phase 5: Collect Metrics & Winners"
echo "-----------------------------------"

echo "5.1) Collecting metrics..."
if ! ssh $REMOTE "cd $RBASE && python3 scripts/collect_metrics.py --out reports/winners.json" 2>&1; then
    echo "❌ Metrics collection failed"
    exit 1
fi
echo "✅ Metrics collected"
echo ""

echo "5.2) Printing results..."
ssh $REMOTE "cd $RBASE && cat reports/winners.json | python3 -m json.tool"
echo ""

echo "=========================================="
echo "✅ Gold-Lite Evaluation Loop Complete!"
echo "=========================================="
echo ""
echo "Deliverables:"
echo "  - reports/qrels_doctor_${DATASET}.json"
echo "  - reports/consistency_${DATASET}.json"
echo "  - reports/embed_doctor_${DATASET}.json"
echo "  - reports/gold_candidates_${DATASET}.csv"
echo "  - reports/qrels_gold_${DATASET}.tsv"
echo "  - reports/winners.json"
echo ""

