#!/usr/bin/env bash
#
# test_metrics_quick.sh - Quick Metrics Test (2-3 min, API-only)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Validates: 1) /readyz, 2) /api/metrics/mini, 3) Redis ingestion,
#            4) Outputs ≤10 lines summary, 5) No /ops/* dependencies
#
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. DEFAULT PARAMETERS (overridable via args)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API="${API:-http://127.0.0.1:8011}"
EXP_ID="${EXP_ID:-metrics_quick_$(date +%s)}"
QPS="${QPS:-4}"
WINDOW="${WINDOW:-60}"
POLL="${POLL:-3}"
WARMUP="${WARMUP:-15}"

# Parse optional args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --exp)     EXP_ID="$2"; shift 2 ;;
    --qps)     QPS="$2"; shift 2 ;;
    --window)  WINDOW="$2"; shift 2 ;;
    --api)     API="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. DEPENDENCY CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
for cmd in curl jq redis-cli; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "❌ Missing dependency: $cmd"
    [[ "$cmd" == "jq" ]] && echo "   Install: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 2
  fi
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. TEMP FILE CLEANUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TMPFILE=$(mktemp /tmp/metrics_quick.XXXXXX)
trap 'rm -f "$TMPFILE"' EXIT

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. PREFLIGHT CHECK (≤5s)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if ! curl -4 -fsSL --max-time 3 "$API/readyz" | jq -e '.ok==true' &>/dev/null; then
  echo "❌ /readyz failed or returned ok!=true"
  exit 1
fi
echo "✓ /readyz OK"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. WARMUP (15s) - Generate traffic for real-time metrics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$WARMUP" -gt 0 ]]; then
  for i in {1..20}; do
    curl -4 -fsSL --max-time 3 -X POST "$API/search" \
      -H 'Content-Type: application/json' \
      -H "X-Lab-Exp: $EXP_ID" \
      -H 'X-Lab-Phase: A' \
      -d '{"query":"ping","top_k":5}' >/dev/null 2>&1 || true
  done
  sleep 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. RUN & POLL (WINDOW seconds)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
t0=$(date +%s)
REDIS_KEY="lab:exp:$EXP_ID:raw"
LAST_REDIS_COUNT=0
NO_DATA_THRESHOLD=30  # If no data for 30s, fail
LAST_DATA_TIME=$t0
METRICS_DATA=""

# Background traffic generator (light load)
(
  interval=$(awk "BEGIN {print 1.0/$QPS}")
  while [[ $(( $(date +%s) - t0 )) -lt $WINDOW ]]; do
    curl -4 -fsSL --max-time 3 -X POST "$API/search" \
      -H 'Content-Type: application/json' \
      -H "X-Lab-Exp: $EXP_ID" \
      -H 'X-Lab-Phase: A' \
      -d '{"query":"test query","top_k":5}' >/dev/null 2>&1 || true
    sleep "$interval"
  done
) &
TRAFFIC_PID=$!

# Poll metrics
while [[ $(( $(date +%s) - t0 )) -lt $WINDOW ]]; do
  sleep "$POLL"
  
  # Check Redis ingestion
  REDIS_COUNT=$(redis-cli llen "$REDIS_KEY" 2>/dev/null || echo "0")
  if [[ "$REDIS_COUNT" -gt "$LAST_REDIS_COUNT" ]]; then
    LAST_REDIS_COUNT=$REDIS_COUNT
    LAST_DATA_TIME=$(date +%s)
  fi
  
  # Check for data starvation
  if [[ $(( $(date +%s) - LAST_DATA_TIME )) -gt $NO_DATA_THRESHOLD ]]; then
    kill $TRAFFIC_PID 2>/dev/null || true
    echo "❌ No data flowing into Redis for ${NO_DATA_THRESHOLD}s"
    exit 3
  fi
  
  # Poll metrics endpoint
  METRICS_DATA=$(curl -fsSL --max-time 3 "$API/api/metrics/mini?exp_id=$EXP_ID&window_sec=30" 2>/dev/null || echo "{}")
done

# Wait for traffic generator to finish
wait $TRAFFIC_PID 2>/dev/null || true

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. CALCULATE & JUDGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P95=$(echo "$METRICS_DATA" | jq -r '.p95_ms // 0')
QPS_MEASURED=$(echo "$METRICS_DATA" | jq -r '.qps // 0')
ERR_PCT=$(echo "$METRICS_DATA" | jq -r '.err_pct // 0')
ROUTE_MILVUS=$(echo "$METRICS_DATA" | jq -r '.route_share.milvus // 0')

VERDICT="PASS"
REASON=""

if (( $(echo "$ERR_PCT >= 1" | bc -l) )); then
  VERDICT="FAIL"
  REASON="err_pct >= 1%"
elif (( $(echo "$QPS_MEASURED <= 0" | bc -l) )); then
  VERDICT="FAIL"
  REASON="qps <= 0"
elif (( $(echo "$P95 <= 0" | bc -l) )); then
  VERDICT="FAIL"
  REASON="p95_ms <= 0"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. OUTPUT (≤10 lines)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT=$(cat <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 METRICS QUICK TEST (${WINDOW}s)
Exp: $EXP_ID
P95: ${P95}ms | QPS: ${QPS_MEASURED}/s | Err%: ${ERR_PCT}% | Route(Milvus): ${ROUTE_MILVUS}%
Redis samples: $LAST_REDIS_COUNT (last 30s observed)
Verdict: $VERDICT $([ -n "$REASON" ] && echo " ($REASON)" || echo "")
API: $API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
)

echo "$OUTPUT"

# Optional: Save to log file
LOGFILE="/tmp/metrics_quick_$(date +%s).log"
echo "$OUTPUT" > "$LOGFILE"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. EXIT CODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$VERDICT" == "PASS" ]]; then
  exit 0
else
  exit 4
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VERIFICATION SNIPPET (expected output example):
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# $ bash scripts/test_metrics_quick.sh
# ✓ /readyz OK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 METRICS QUICK TEST (60s)
# Exp: metrics_quick_1760830999
# P95: 38.7ms | QPS: 2.9/s | Err%: 0.0% | Route(Milvus): 100%
# Redis samples: 480 (last 30s observed)
# Verdict: PASS
# API: http://127.0.0.1:8011
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

