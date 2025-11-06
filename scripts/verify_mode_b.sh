#!/bin/bash
# Quick Mode B verification script

API_BASE="${API_BASE:-http://localhost:8001}"

echo "=== Black Swan Mode B Configuration Verification ==="
echo ""

# 1. Check .env equivalent (environment)
echo "1. Environment Variables:"
echo "   PLAY_B_DURATION_SEC: ${PLAY_B_DURATION_SEC:-<not set, default 180>}"
echo "   HEAVY_NUM_CANDIDATES: ${HEAVY_NUM_CANDIDATES:-<not set, default 1500>}"
echo "   HEAVY_RERANK_TOPK: ${HEAVY_RERANK_TOPK:-<not set, default 300>}"
echo "   HEAVY_QUERY_BANK: ${HEAVY_QUERY_BANK:-<not set, default data/fiqa_queries.txt>}"
echo ""

# 2. Check backend config
echo "2. Backend Configuration:"
curl -s "${API_BASE}/ops/black_swan/config" | jq -r '
  "   current_mode: " + (.current_mode // "null"),
  "   use_real: " + (.use_real|tostring),
  "   playbook_params.heavy_params: " + (.playbook_params.heavy_params|tostring),
  "   playbook_params.burst_duration: " + (.playbook_params.burst_duration|tostring),
  "   playbook_params.num_candidates: " + (.playbook_params.num_candidates|tostring),
  "   playbook_params.rerank_topk: " + (.playbook_params.rerank_topk|tostring)
'
echo ""

# 3. Check runtime status
echo "3. Runtime Status:"
curl -s "${API_BASE}/ops/black_swan/status" | jq -r '
  "   mode: " + (.mode // "null"),
  "   running: " + (.running|tostring),
  "   phase: " + (.phase // "null"),
  "   playbook_params.burst_duration: " + (.playbook_params.burst_duration|tostring),
  "   playbook_params.heavy_params: " + (.playbook_params.heavy_params|tostring)
'
echo ""

# 4. Check last report
LAST_REPORT=$(ls -t reports/black_swan_*.json 2>/dev/null | grep -v "_before\|_trip\|_after\|_last_http" | head -1)
if [ -n "$LAST_REPORT" ]; then
  echo "4. Last Report ($LAST_REPORT):"
  jq -r '
    "   test_config.load_duration_sec: " + (.test_config.load_duration_sec|tostring),
    "   playbook_params: " + (if .playbook_params then "present" else "MISSING" end)
  ' "$LAST_REPORT"
else
  echo "4. Last Report: No report found"
fi
echo ""

# 5. Check FIQA query bank
QUERY_BANK="data/fiqa_queries.txt"
if [ -f "$QUERY_BANK" ]; then
  LINE_COUNT=$(wc -l < "$QUERY_BANK")
  echo "5. FIQA Query Bank:"
  echo "   Path: $QUERY_BANK"
  echo "   Lines: $LINE_COUNT"
  echo "   Sample (first line):"
  head -1 "$QUERY_BANK" | sed 's/^/     /'
else
  echo "5. FIQA Query Bank: NOT FOUND at $QUERY_BANK"
fi
echo ""

echo "=== Summary Table ==="
printf "| %-20s | %-15s | %-10s | %-40s |\n" "Source" "duration_sec" "heavy" "queries_path"
printf "|%s|%s|%s|%s|\n" "$(printf '%.0s-' {1..22})" "$(printf '%.0s-' {1..17})" "$(printf '%.0s-' {1..12})" "$(printf '%.0s-' {1..42})"

# Backend config
BACKEND_DURATION=$(curl -s "${API_BASE}/ops/black_swan/config" | jq -r '.playbook_params.burst_duration // "N/A"')
BACKEND_HEAVY=$(curl -s "${API_BASE}/ops/black_swan/config" | jq -r '.playbook_params.heavy_params // "N/A"')
printf "| %-20s | %-15s | %-10s | %-40s |\n" "backend config" "$BACKEND_DURATION" "$BACKEND_HEAVY" "data/fiqa_queries.txt"

# Runtime status
STATUS_DURATION=$(curl -s "${API_BASE}/ops/black_swan/status" | jq -r '.playbook_params.burst_duration // "N/A"')
STATUS_HEAVY=$(curl -s "${API_BASE}/ops/black_swan/status" | jq -r '.playbook_params.heavy_params // "N/A"')
printf "| %-20s | %-15s | %-10s | %-40s |\n" "runtime status" "$STATUS_DURATION" "$STATUS_HEAVY" "data/fiqa_queries.txt"

# Last report
if [ -n "$LAST_REPORT" ]; then
  REPORT_DURATION=$(jq -r '.test_config.load_duration_sec // "N/A"' "$LAST_REPORT")
  REPORT_PLAYBOOK=$(jq -r '.playbook_params.heavy_params // "MISSING"' "$LAST_REPORT")
  printf "| %-20s | %-15s | %-10s | %-40s |\n" "report" "$REPORT_DURATION" "$REPORT_PLAYBOOK" "N/A (not in report)"
fi

echo ""

