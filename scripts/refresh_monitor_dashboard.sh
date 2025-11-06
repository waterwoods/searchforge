#!/usr/bin/env bash
#
# refresh_monitor_dashboard.sh - Quick script to refresh monitor dashboard data
# Usage: bash scripts/refresh_monitor_dashboard.sh [exp_id] [duration]
#

set -euo pipefail

EXP_ID="${1:-monitor_demo}"
DURATION="${2:-60}"
API="http://127.0.0.1:8011"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Refreshing Monitor Dashboard Data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Experiment ID: $EXP_ID"
echo "Duration: ${DURATION}s"
echo ""

# Step 1: Verify backend is running
echo "1️⃣  Checking backend..."
if ! curl -s --max-time 3 "$API/readyz" | jq -e '.ok==true' &>/dev/null; then
  echo "❌ Backend not ready on $API"
  echo "   Start with: cd services/fiqa_api && uvicorn app_main:app --port 8011"
  exit 1
fi
echo "✅ Backend ready"

# Step 2: Run metrics quick test
echo ""
echo "2️⃣  Running metrics quick test..."
bash "$(dirname "$0")/test_metrics_quick.sh" --exp "$EXP_ID" --qps 6 --window "$DURATION" --api "$API"

# Step 3: Verify data
echo ""
echo "3️⃣  Verifying data..."
RECORDS=$(redis-cli -n 0 llen "lab:exp:$EXP_ID:raw" 2>/dev/null || echo "0")
echo "   Redis records: $RECORDS"

if [ "$RECORDS" -gt 0 ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ Dashboard data ready!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📊 View in dashboard:"
  echo "   1. Open: http://localhost:3000/monitor"
  echo "   2. Select 'Manual' mode"
  echo "   3. Enter experiment ID: $EXP_ID"
  echo ""
  echo "📈 Quick metrics check:"
  curl -s "$API/api/metrics/mini?exp_id=$EXP_ID&window_sec=60" | jq '{qps, err_pct, route_share}'
  echo ""
else
  echo "❌ No data in Redis for experiment: $EXP_ID"
  exit 1
fi

