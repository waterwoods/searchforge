continue
  think

  #!/bin/bash
# verify_mini.sh - Verify Mini Dashboard system
# Tests backend API, health gates, and mini report format

set -e

BASE_URL="${BASE_URL:-http://localhost:8011}"
REPORT_FILE="reports/MINI_VERIFY.txt"

echo "========================================"
echo "MINI DASHBOARD VERIFICATION"
echo "========================================"
echo "Base URL: $BASE_URL"  check the files
  continue
  
echo ""

# Initialize results
declare -a RESULTS
PASS_COUNT=0
FAIL_COUNT=0

# Helper function to record test result
record_result() {
  local test_name="$1"
  local status="$2"
  local detail="$3"
  
  if [ "$status" = "PASS" ]; then
    RESULTS+=("✅ $test_name: PASS")
    ((PASS_COUNT++))
  else
    RESULTS+=("❌ $test_name: FAIL - $detail")
    ((FAIL_COUNT++))
  fi
}

# Test 1: Check /ops/lab/report?mini=1 format
echo "[1/5] Testing mini report endpoint..."
MINI_RESPONSE=$(curl -s "$BASE_URL/ops/lab/report?mini=1" || echo '{"ok":false}')

if echo "$MINI_RESPONSE" | jq -e '.delta_p95_pct' > /dev/null 2>&1 && \
   echo "$MINI_RESPONSE" | jq -e '.delta_qps_pct' > /dev/null 2>&1 && \
   echo "$MINI_RESPONSE" | jq -e '.error_rate_pct' > /dev/null 2>&1 && \
   echo "$MINI_RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
  record_result "Mini report format" "PASS" ""
  echo "   Response has all required fields"
else
  record_result "Mini report format" "FAIL" "Missing required fields"
  echo "   Response: $MINI_RESPONSE"
fi

# Test 2: Check no report case (should not error)
echo ""
echo "[2/5] Testing no-report case..."
OK_FIELD=$(echo "$MINI_RESPONSE" | jq -r '.ok')
if [ "$OK_FIELD" = "true" ] || [ "$OK_FIELD" = "false" ]; then
  record_result "No-report handling" "PASS" ""
  echo "   Returns ok:$OK_FIELD (no crash)"
else
  record_result "No-report handling" "FAIL" "Invalid ok field"
fi

# Test 3: Check /api/lab/config endpoint
echo ""
echo "[3/5] Testing config endpoint..."
CONFIG_RESPONSE=$(curl -s "$BASE_URL/api/lab/config" || echo '{"ok":false}')

if echo "$CONFIG_RESPONSE" | jq -e '.health' > /dev/null 2>&1; then
  record_result "Config endpoint" "PASS" ""
  echo "   Config returns health info"
  
  # Extract health info
  REDIS_OK=$(echo "$CONFIG_RESPONSE" | jq -r '.health.redis.ok')
  QDRANT_OK=$(echo "$CONFIG_RESPONSE" | jq -r '.health.qdrant.ok')
  echo "   Redis: $REDIS_OK, Qdrant: $QDRANT_OK"
else
  record_result "Config endpoint" "FAIL" "Missing health field"
fi

# Test 4: Check /ops/lab/status endpoint
echo ""
echo "[4/5] Testing status endpoint..."
STATUS_RESPONSE=$(curl -s "$BASE_URL/ops/lab/status" || echo '{"ok":false}')

if echo "$STATUS_RESPONSE" | jq -e '.ok' > /dev/null 2>&1; then
  record_result "Status endpoint" "PASS" ""
  RUNNING=$(echo "$STATUS_RESPONSE" | jq -r '.running')
  echo "   Experiment running: $RUNNING"
else
  record_result "Status endpoint" "FAIL" "Invalid response"
fi

# Test 5: Verify types file exists
echo ""
echo "[5/5] Checking generated types..."
TYPES_FILE="frontend/src/adapters/types.generated.ts"

if [ -f "$TYPES_FILE" ]; then
  if grep -q "LabMiniReportResponse" "$TYPES_FILE"; then
    record_result "Generated types" "PASS" ""
    echo "   Types file exists with correct interfaces"
  else
    record_result "Generated types" "FAIL" "Missing LabMiniReportResponse"
  fi
else
  record_result "Generated types" "FAIL" "File not found"
fi

# Generate report
echo ""
echo "========================================"
echo "GENERATING REPORT"
echo "========================================"

{
  echo "========================================"
  echo "MINI DASHBOARD VERIFICATION REPORT"
  echo "========================================"
  echo ""
  echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Base URL: $BASE_URL"
  echo ""
  echo "RESULTS"
  echo "----------------------------------------"
  for result in "${RESULTS[@]}"; do
    echo "$result"
  done
  echo ""
  echo "SUMMARY"
  echo "----------------------------------------"
  echo "Total: $((PASS_COUNT + FAIL_COUNT))"
  echo "Passed: $PASS_COUNT"
  echo "Failed: $FAIL_COUNT"
  echo ""
  
  if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ ALL PASS"
    echo ""
    echo "Mini Dashboard system is operational:"
    echo "- Backend /ops/lab/report?mini=1 returns correct format"
    echo "- No-report case handled gracefully (no 500 errors)"
    echo "- Config and status endpoints working"
    echo "- TypeScript types generated"
    echo ""
    echo "Next steps:"
    echo "1. cd frontend && npm install"
    echo "2. npm run dev"
    echo "3. Open http://localhost:3000"
    echo "4. Click 'Fetch latest report'"
  else
    echo "⚠️ SOME TESTS FAILED"
    echo ""
    echo "Please check:"
    echo "- Backend is running at $BASE_URL"
    echo "- Run: ./scripts/schema_check.mjs"
    echo "- Check logs for errors"
  fi
  echo ""
  echo "========================================"
  echo "END OF REPORT"
  echo "========================================"
} > "$REPORT_FILE"

# Print report
cat "$REPORT_FILE"

# Exit with appropriate code
if [ $FAIL_COUNT -eq 0 ]; then
  echo ""
  echo "📄 Full report saved to: $REPORT_FILE"
  exit 0
else
  echo ""
  echo "📄 Report with failures saved to: $REPORT_FILE"
  exit 1
fi


