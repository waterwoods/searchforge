#!/usr/bin/env bash
# run_prewarm.sh - 2-minute prewarm phase
# Generates light load to warm up caches and connections
# Uses separate exp_id to avoid polluting A/B statistics

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DURATION=${1:-120}  # Default 2 minutes
QPS=${2:-4}         # Light load
BASE_URL="http://localhost:8011"
EXP_ID="soak_60m_warm_$(date +%s)"

echo "━━━ Prewarm (${DURATION}s @ ${QPS} QPS) ━━━"
echo "Exp: $EXP_ID"

# Query pool
QUERIES=(
  "portfolio management"
  "financial planning"
  "risk assessment"
  "asset allocation"
  "retirement savings"
  "market analysis"
)

# Send request
send_req() {
  local qidx=$1
  local query="${QUERIES[$((qidx % ${#QUERIES[@]}))]}"
  
  curl -sf -X POST "${BASE_URL}/search" \
    -H "Content-Type: application/json" \
    -H "X-Lab-Exp: $EXP_ID" \
    -H "X-Lab-Phase: warmup" \
    -H "X-TopK: 10" \
    -d "{\"query\":\"$query\",\"top_k\":10}" > /dev/null 2>&1 || true
}

# Run warmup
START_TIME=$(date +%s)
COUNTER=0

while [[ $(($(date +%s) - START_TIME)) -lt $DURATION ]]; do
  send_req $COUNTER &
  COUNTER=$((COUNTER + 1))
  sleep $(python3 -c "print(1.0/$QPS)")
done

wait

echo "✅ Prewarm complete: $COUNTER requests sent"
echo "Note: Warmup data stored under exp_id=$EXP_ID (isolated from main test)"

