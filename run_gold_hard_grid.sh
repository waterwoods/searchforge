#!/usr/bin/env bash
set -euo pipefail

API=${API:-http://localhost:8000}
OUTDIR=${OUTDIR:-reports}
JOBS_FILE="$OUTDIR/jobs_gold_hard.list"

mkdir -p "$OUTDIR"

log(){ printf "\n\033[1;36m[%-8s]\033[0m %s\n" "$1" "$2"; }

submit() {
  local dataset="$1"
  local qrels="$2"
  local top_k="$3"
  local fast="$4"
  
  FAST_STR="false"
  [ "$fast" = "1" ] && FAST_STR="true"
  
  # For gold: use sample=200 (standard), for hard: omit sample (use all 150 queries)
  # Convert shell boolean to Python boolean
  if [ "$FAST_STR" = "true" ]; then
    FAST_PY="True"
  else
    FAST_PY="False"
  fi
  
  if [[ "$qrels" == *"hard"* ]]; then
    # Hard queries: omit sample field (will use all queries in the hard set)
    BODY=$(python3 -c "
import json
print(json.dumps({
    'dataset_name': '$dataset',
    'qrels_name': '$qrels',
    'fast_mode': $FAST_PY,
    'top_k': int('$top_k'),
    'repeats': 1
}))
")
  else
    # Gold queries: use sample=200
    BODY=$(python3 -c "
import json
print(json.dumps({
    'dataset_name': '$dataset',
    'qrels_name': '$qrels',
    'fast_mode': $FAST_PY,
    'top_k': int('$top_k'),
    'sample': 200,
    'repeats': 1
}))
")
  fi
  
  log SUBMIT "dataset=$dataset qrels=$qrels top_k=$top_k fast=$FAST_STR"
  
  RESP=$(curl -fsS -H 'content-type: application/json' -d "$BODY" "$API/api/experiment/run" 2>&1)
  echo "$RESP" >&2
  
  echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null | tail -1
}

log START "Running Gold + Hard experiment grid"

# Gold experiments: dataset=fiqa_50k_v1, qrels=fiqa_qrels_50k_v1
# We'll use sample=200 from recent runs (gold qrels)
GOLD_JOBS=()
GOLD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_50k_v1" "5" "0"))
GOLD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_50k_v1" "10" "0"))
GOLD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_50k_v1" "5" "1"))
GOLD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_50k_v1" "10" "1"))

# Hard experiments: dataset=fiqa_50k_v1, qrels=fiqa_qrels_hard_50k_v1
# Use hard queries (150)
HARD_JOBS=()
HARD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_hard_50k_v1" "5" "0"))
HARD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_hard_50k_v1" "10" "0"))
HARD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_hard_50k_v1" "5" "1"))
HARD_JOBS+=($(submit "fiqa_50k_v1" "fiqa_qrels_hard_50k_v1" "10" "1"))

ALL_JOBS=("${GOLD_JOBS[@]}" "${HARD_JOBS[@]}")

echo "${ALL_JOBS[@]}" > "$JOBS_FILE"
log JOBS "Submitted ${#ALL_JOBS[@]} jobs: $(cat $JOBS_FILE)"

# Poll for completion
poll() {
  local id="$1"
  log POLL "job=$id"
  for i in $(seq 1 180); do
    ST_RESP=$(curl -fsS "$API/api/experiment/status/$id" 2>&1)
    st=$(echo "$ST_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    echo "  #$i state=$st"
    case "$st" in
      SUCCEEDED|FAILED) break;;
    esac
    sleep 2
  done
}

for J in "${ALL_JOBS[@]}"; do
  poll "$J"
done

log DONE "All jobs finished"

