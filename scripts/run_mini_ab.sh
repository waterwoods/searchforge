#!/usr/bin/env bash
# run_mini_ab.sh - Mini A/B test runner (3min default)
set -euo pipefail

# Parse flags
QPS=6
WINDOW=90
ROUNDS=1
SEED=42

while [[ $# -gt 0 ]]; do
  case $1 in
    --qps) QPS="$2"; shift 2 ;;
    --window) WINDOW="$2"; shift 2 ;;
    --rounds) ROUNDS="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

EXP_ID="mini_ab_$(date +%s)"
BASE_URL="http://localhost:8011"
WARMUP_SEC=20

echo "=== Mini A/B Test ==="
echo "Exp: $EXP_ID | QPS: $QPS | Window: ${WINDOW}s | Seed: $SEED"

# Seeded query list (simple rotation for demo)
QUERIES=("portfolio management" "financial planning" "risk assessment" "asset allocation" "retirement savings" "market analysis" "investment strategy" "dividend yield")

# Helper: send request
send_req() {
  local phase=$1
  local qidx=$2
  local query="${QUERIES[$((qidx % ${#QUERIES[@]}))]}"
  
  curl -sf -X POST "${BASE_URL}/search" \
    -H "Content-Type: application/json" \
    -H "X-Lab-Exp: $EXP_ID" \
    -H "X-Lab-Phase: $phase" \
    -H "X-TopK: 10" \
    -d "{\"query\":\"$query\",\"top_k\":10}" > /dev/null 2>&1 || true
}

# Run A/B test
START_TIME=$(date +%s)
COUNTER=0

while [[ $(($(date +%s) - START_TIME)) -lt $WINDOW ]]; do
  # Alternate A/B in same seeded stream
  send_req "A" $COUNTER &
  sleep 0.05
  send_req "B" $COUNTER &
  sleep 0.05
  
  COUNTER=$((COUNTER + 1))
  
  # Rate limit: ~6 QPS total = 0.16s between pairs
  sleep 0.06
done

wait
echo "Load complete. Processing metrics..."

# Wait for Redis writes to settle
sleep 2

# Compute metrics using redis_report.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METRICS=$(python3 "$SCRIPT_DIR/redis_report.py" "$EXP_ID" --warmup $WARMUP_SEC)

# Extract key values
P95_A=$(echo "$METRICS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('p95_a', 0))")
P95_B=$(echo "$METRICS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('p95_b', 0))")
DELTA_PCT=$(echo "$METRICS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('delta_p95_pct', 0))")
ERR_PCT=$(echo "$METRICS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('err_pct', 0))")
SAMPLES_A=$(echo "$METRICS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('samples_a', 0))")
SAMPLES_B=$(echo "$METRICS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('samples_b', 0))")

# Check imbalance
IMBALANCE=0
if [[ $SAMPLES_A -gt 0 ]]; then
  IMBALANCE=$(python3 -c "print(abs($SAMPLES_B - $SAMPLES_A) / $SAMPLES_A * 100)")
fi

# Summary (6 lines)
echo "=== Results ==="
echo "P95: A=${P95_A}ms B=${P95_B}ms Δ=${DELTA_PCT}%"
echo "Err: ${ERR_PCT}% | Samples: A=$SAMPLES_A B=$SAMPLES_B"
echo "Imbalance: ${IMBALANCE}%"

# Check alarm conditions
ALARM=false
if (( $(echo "$ERR_PCT > 1" | bc -l) )); then
  ALARM=true
  echo "ALERT: Error rate ${ERR_PCT}% > 1%"
fi
if (( $(echo "$IMBALANCE > 5" | bc -l) )); then
  ALARM=true
  echo "ALERT: A/B imbalance ${IMBALANCE}% > 5%"
fi

# Call alarm hook if needed
if [[ "$ALARM" == "true" ]]; then
  python3 -c "
import sys
sys.path.insert(0, '$(dirname "$SCRIPT_DIR")')
from backend_core.alarm import maybe_alarm
stats = {
  'err_pct': $ERR_PCT,
  'ab_imbalance_pct': $IMBALANCE,
  'exp_id': '$EXP_ID'
}
maybe_alarm(stats)
"
fi

# Fail if imbalance too high
if (( $(echo "$IMBALANCE > 5" | bc -l) )); then
  echo "=== FAIL (imbalance) ==="
  exit 1
fi

echo "=== PASS ==="
exit 0

