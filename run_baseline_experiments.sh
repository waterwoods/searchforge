#!/usr/bin/env bash
set -euo pipefail

API=http://localhost:8000
DATA=fiqa_50k_v1
QRELS=fiqa_qrels_50k_v1
JOBS=()

submit() {
  TK=$1
  FAST=$2
  FAST_STR="false"
  [ "$FAST" = "1" ] && FAST_STR="true"
  
  RESP=$(curl -fsS -X POST "$API/api/experiment/run" \
    -H "Content-Type: application/json" \
    -d "{\"sample\":200,\"repeats\":1,\"fast_mode\":$FAST_STR,\"dataset_name\":\"$DATA\",\"qrels_name\":\"$QRELS\",\"top_k\":$TK}")
  
  JID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
  echo "[SUBMIT] top_k=$TK fast=$FAST_STR -> $JID"
  JOBS+=("$JID")
}

submit 10 0
submit 20 0
submit 10 1
submit 20 1

echo "[INFO] Submitted ${#JOBS[@]} jobs: ${JOBS[*]}"

# Poll for completion
for jid in "${JOBS[@]}"; do
  echo "[POLL] $jid"
  for i in $(seq 1 180); do
    ST=$(curl -fsS "$API/api/experiment/status/$jid" | python3 -c "import sys,json; print(json.load(sys.stdin)['job']['status'])")
    echo "  [$i] $ST"
    [[ "$ST" =~ ^(SUCCEEDED|FAILED)$ ]] && break
    sleep 2
  done
done

echo "[INFO] All jobs finished"

