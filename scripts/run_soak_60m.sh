#!/usr/bin/env bash
# run_soak_60m.sh - 60-minute soak test with monitoring and alarms
# Runs A/B test for 60 minutes total (30 min Phase A → 30 min Phase B)
# Features:
# - Every 10s health check with alarm triggers
# - TTL refresh on each Redis write
# - Auto-snapshot on alarm
# - Compressed summary report at end

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Parse Arguments
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QPS=6
WINDOW=1800  # 30 minutes per phase
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXP_ID="soak_60m_$(date +%s)"
BASE_URL="http://localhost:8011"
WARMUP_SEC=60  # First 60 seconds are warmup
LOG_FILE="/tmp/soak_60m.log"
ALARM_CHECK_INTERVAL=10  # Check every 10 seconds
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports"

mkdir -p "$REPORTS_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Setup Logging
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log() {
  echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

> "$LOG_FILE"  # Clear log file

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🧪 60-Minute Soak Test Starting"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Exp ID: $EXP_ID"
log "QPS: $QPS | Window: ${WINDOW}s per phase | Seed: $SEED"
log "Log: $LOG_FILE"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Query Pool (Seeded)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUERIES=(
  "portfolio management"
  "financial planning"
  "risk assessment"
  "asset allocation"
  "retirement savings"
  "market analysis"
  "investment strategy"
  "dividend yield"
  "capital gains"
  "mutual funds"
  "stock valuation"
  "bond investing"
  "diversification"
  "index funds"
  "hedge funds"
  "commodities trading"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

check_alarm() {
  # Get current metrics from Redis (last 60s window)
  local metrics
  metrics=$(curl -sf "${BASE_URL}/api/metrics/mini?exp_id=$EXP_ID&window_sec=60" || echo '{}')
  
  # Check if we have data
  local samples
  samples=$(echo "$metrics" | python3 -c "import sys, json; print(json.load(sys.stdin).get('samples', 0))" 2>/dev/null || echo "0")
  
  if [[ "$samples" == "0" ]]; then
    # No data in last 60s - might be stale
    local time_since_start=$(($(date +%s) - START_TIME))
    if [[ $time_since_start -gt 90 ]]; then
      log "⚠️  WARNING: No data in last 60s (test running ${time_since_start}s)"
    fi
    return
  fi
  
  # Extract metrics
  local err_pct
  local qps
  err_pct=$(echo "$metrics" | python3 -c "import sys, json; print(json.load(sys.stdin).get('err_pct', 0))" 2>/dev/null || echo "0")
  qps=$(echo "$metrics" | python3 -c "import sys, json; print(json.load(sys.stdin).get('qps', 0))" 2>/dev/null || echo "0")
  
  # Check thresholds
  local alarm_triggered=false
  
  if (( $(echo "$err_pct > 1" | bc -l 2>/dev/null || echo "0") )); then
    log "🚨 ALARM: Error rate ${err_pct}% > 1%"
    alarm_triggered=true
  fi
  
  # Call alarm hook if needed
  if [[ "$alarm_triggered" == "true" ]]; then
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend_core.alarm import maybe_alarm
stats = {
  'err_pct': $err_pct,
  'ab_imbalance_pct': 0,
  'exp_id': '$EXP_ID',
  'qps': $qps,
  'samples': $samples
}
maybe_alarm(stats)
" 2>&1 | tee -a "$LOG_FILE"
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Background Monitoring Loop
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

start_monitoring() {
  log "📊 Starting background monitoring (every ${ALARM_CHECK_INTERVAL}s)"
  
  while true; do
    sleep "$ALARM_CHECK_INTERVAL"
    
    # Check if parent is still alive
    if ! kill -0 $$ 2>/dev/null; then
      break
    fi
    
    check_alarm
  done &
  
  MONITOR_PID=$!
  log "Monitor PID: $MONITOR_PID"
}

stop_monitoring() {
  if [[ -n "${MONITOR_PID:-}" ]]; then
    log "Stopping monitor (PID: $MONITOR_PID)"
    kill "$MONITOR_PID" 2>/dev/null || true
    wait "$MONITOR_PID" 2>/dev/null || true
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Run Load Test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

run_phase() {
  local phase=$1
  local duration=$2
  local phase_start=$(date +%s)
  local counter=0
  
  log "▶️  Starting Phase $phase (${duration}s)"
  
  while [[ $(($(date +%s) - phase_start)) -lt $duration ]]; do
    send_req "$phase" $counter &
    counter=$((counter + 1))
    
    # Rate limit to achieve target QPS
    sleep $(python3 -c "print(1.0/$QPS)")
  done
  
  # Wait for background requests to complete
  wait
  
  local phase_end=$(date +%s)
  local actual_duration=$((phase_end - phase_start))
  local actual_qps=$(python3 -c "print(round($counter / $actual_duration, 2))")
  
  log "✅ Phase $phase complete: $counter requests in ${actual_duration}s (${actual_qps} QPS)"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cleanup Handler
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cleanup() {
  log "🛑 Cleanup triggered"
  stop_monitoring
  
  # Kill any background requests
  jobs -p | xargs -r kill 2>/dev/null || true
  
  exit "${1:-0}"
}

trap 'cleanup 1' INT TERM
trap 'cleanup 0' EXIT

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Execution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

START_TIME=$(date +%s)

# Start background monitoring
start_monitoring

# Run Phase A
run_phase "A" "$WINDOW"

# Short pause between phases
log "⏸️  Transition pause (5s)"
sleep 5

# Run Phase B
run_phase "B" "$WINDOW"

# Stop monitoring
stop_monitoring

log "⏹️  Load generation complete. Processing metrics..."

# Wait for Redis writes to settle
sleep 5

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Generate Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log "📄 Generating summary report..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use redis_report.py to compute metrics
METRICS_JSON=$(python3 "$SCRIPT_DIR/redis_report.py" "$EXP_ID" --warmup $WARMUP_SEC)

# Parse key metrics
P95_A=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('p95_a', 0))")
P95_B=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('p95_b', 0))")
DELTA_PCT=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('delta_p95_pct', 0))")
ERR_PCT=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('err_pct', 0))")
SAMPLES_A=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('samples_a', 0))")
SAMPLES_B=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('samples_b', 0))")
QPS_A=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('qps_a', 0))")
QPS_B=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('qps_b', 0))")
ROUTE_MILVUS=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('route_share', {}).get('milvus', 0))")
ROUTE_FAISS=$(echo "$METRICS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('route_share', {}).get('faiss', 0))")

# Calculate imbalance
IMBALANCE=0
if [[ $(python3 -c "print($SAMPLES_A > 0)") == "True" ]]; then
  IMBALANCE=$(python3 -c "print(abs($SAMPLES_B - $SAMPLES_A) / $SAMPLES_A * 100)")
fi

# Total duration
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_MINUTES=$(python3 -c "print(round($TOTAL_DURATION / 60, 1))")

# Generate summary report (≤12 lines)
SUMMARY_FILE="$REPORTS_DIR/SOAK_60M_SUMMARY.txt"

cat > "$SUMMARY_FILE" << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 SOAK 60M TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exp: $EXP_ID | Duration: ${TOTAL_MINUTES}min
Samples: A=$SAMPLES_A B=$SAMPLES_B | Imbalance: ${IMBALANCE}%
P95: A=${P95_A}ms B=${P95_B}ms | ΔP95: ${DELTA_PCT}%
QPS: A=${QPS_A} B=${QPS_B} | Err: ${ERR_PCT}%
Route: Milvus=${ROUTE_MILVUS}% FAISS=${ROUTE_FAISS}%
Verdict: $(if (( $(echo "$ERR_PCT < 1 && $IMBALANCE < 5" | bc -l) )); then echo "✅ PASS"; else echo "❌ FAIL"; fi)
Logs: $LOG_FILE
Reports: $SUMMARY_FILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

# Display summary
cat "$SUMMARY_FILE" | tee -a "$LOG_FILE"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Final Checks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Check pass/fail criteria
PASS=true

if (( $(echo "$ERR_PCT >= 1" | bc -l) )); then
  log "❌ FAIL: Error rate ${ERR_PCT}% >= 1%"
  PASS=false
fi

if (( $(echo "$IMBALANCE > 5" | bc -l) )); then
  log "❌ FAIL: A/B imbalance ${IMBALANCE}% > 5%"
  PASS=false
fi

if [[ $SAMPLES_A -lt 1000 ]] || [[ $SAMPLES_B -lt 1000 ]]; then
  log "❌ FAIL: Insufficient samples (A=$SAMPLES_A, B=$SAMPLES_B, need >1000 each)"
  PASS=false
fi

if (( $(echo "$ROUTE_MILVUS < 90" | bc -l) )); then
  log "⚠️  WARNING: Milvus routing ${ROUTE_MILVUS}% < 90%"
fi

# Check for alerts
ALERT_COUNT=$(ls -1 "$REPORTS_DIR"/ALERT_*.txt 2>/dev/null | wc -l)
if [[ $ALERT_COUNT -gt 0 ]]; then
  log "⚠️  $ALERT_COUNT alert(s) triggered during test"
fi

if [[ "$PASS" == "true" ]]; then
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "✅ SOAK TEST PASSED"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
else
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "❌ SOAK TEST FAILED"
  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi

