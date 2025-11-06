#!/usr/bin/env bash
#
# verify_summary.sh - Verify /ops/summary endpoint returns timeline data
#
# This script:
# 1. Triggers Black Swan Mode B for 30s
# 2. Waits 10s for metrics to accumulate
# 3. Fetches /ops/summary and validates timeline data
# 4. Outputs verification report to reports/SUMMARY_FIX_MINI.txt

set -euo pipefail

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8011}"
OUTPUT_DIR="reports"
OUTPUT_FILE="${OUTPUT_DIR}/SUMMARY_FIX_MINI.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

# Clear previous report
> "${OUTPUT_FILE}"

log_report() {
    echo "$1" | tee -a "${OUTPUT_FILE}"
}

log_info "Starting /ops/summary verification..."
log_report "========================================="
log_report "P95 & Recall Summary Fix Verification"
log_report "========================================="
log_report "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
log_report "Backend: ${BACKEND_URL}"
log_report ""

# Step 1: Check if backend is reachable
log_info "Step 1: Checking backend health..."
if ! response=$(curl -s -f "${BACKEND_URL}/healthz" 2>&1); then
    log_error "Backend not reachable at ${BACKEND_URL}"
    log_report "❌ Backend health check failed"
    log_report "   Error: ${response}"
    exit 1
fi
log_report "✅ Backend is healthy"
log_report ""

# Step 2: Trigger Black Swan Mode B
log_info "Step 2: Triggering Black Swan Mode B (30s)..."
bs_response=$(curl -s -X POST "${BACKEND_URL}/ops/black_swan" \
    -H 'Content-Type: application/json' \
    -d '{"mode":"B","duration_sec":30}' || echo '{"ok":false,"error":"request_failed"}')

bs_ok=$(echo "${bs_response}" | jq -r '.ok // false')
bs_run_id=$(echo "${bs_response}" | jq -r '.run_id // "unknown"')

if [ "${bs_ok}" != "true" ]; then
    log_warn "Black Swan trigger returned ok=false (may already be running)"
    log_report "⚠️  Black Swan trigger: $(echo "${bs_response}" | jq -r '.error // "unknown"')"
else
    log_info "Black Swan started: run_id=${bs_run_id}"
    log_report "✅ Black Swan Mode B triggered"
    log_report "   Run ID: ${bs_run_id}"
fi
log_report ""

# Step 3: Wait for metrics to accumulate
log_info "Step 3: Waiting 10s for metrics to accumulate..."
for i in {10..1}; do
    echo -ne "  Waiting... ${i}s remaining\r"
    sleep 1
done
echo ""
log_report "✅ Waited 10s for metrics"
log_report ""

# Step 4: Fetch /ops/summary
log_info "Step 4: Fetching /ops/summary..."
summary_response=$(curl -s "${BACKEND_URL}/ops/summary" || echo '{"ok":false,"error":"request_failed"}')

# Save raw response for debugging
echo "${summary_response}" | jq '.' > "${OUTPUT_DIR}/summary_raw.json" 2>/dev/null || true

# Parse response
ok=$(echo "${summary_response}" | jq -r '.ok // false')
timeline_count=$(echo "${summary_response}" | jq -r '.timeline | length // 0')
degraded=$(echo "${summary_response}" | jq -r '.degraded.redis // false')

log_report "--- /ops/summary Response ---"
log_report "ok: ${ok}"
log_report "timeline entries: ${timeline_count}"
log_report "degraded (Redis): ${degraded}"
log_report ""

# Validate response
errors=0

# Check 1: ok == true
if [ "${ok}" != "true" ]; then
    log_error "Response has ok=false"
    log_report "❌ FAIL: ok == false"
    ((errors++))
else
    log_report "✅ PASS: ok == true"
fi

# Check 2: timeline.length >= 5
if [ "${timeline_count}" -lt 5 ]; then
    log_error "Timeline has < 5 entries (got ${timeline_count})"
    log_report "❌ FAIL: timeline.length < 5 (got ${timeline_count})"
    ((errors++))
else
    log_report "✅ PASS: timeline.length >= 5 (got ${timeline_count})"
fi

# Check 3: Timeline has p95_ms values
p95_count=$(echo "${summary_response}" | jq -r '[.timeline[] | select(.p95_ms != null)] | length // 0')
if [ "${p95_count}" -ge 1 ]; then
    log_report "✅ PASS: Found ${p95_count} p95_ms values in timeline"
else
    log_error "No p95_ms values found in timeline"
    log_report "❌ FAIL: No p95_ms values in timeline"
    ((errors++))
fi

# Check 4: Timeline has recall_at_10 values (optional, may be null if no real queries)
recall_count=$(echo "${summary_response}" | jq -r '[.timeline[] | select(.recall_at_10 != null)] | length // 0')
if [ "${recall_count}" -ge 1 ]; then
    log_report "✅ PASS: Found ${recall_count} recall_at_10 values in timeline"
else
    log_warn "No recall_at_10 values in timeline (may be expected if no real queries)"
    log_report "⚠️  WARN: No recall_at_10 values in timeline"
fi

log_report ""

# Show sample timeline points
log_report "--- Sample Timeline Points (first 3) ---"
echo "${summary_response}" | jq -r '.timeline[0:3][]? | "  t: \(.t), p95_ms: \(.p95_ms), recall_at_10: \(.recall_at_10)"' >> "${OUTPUT_FILE}" || log_report "  (no timeline data)"
log_report ""

# Show window60s summary
log_report "--- window60s Summary ---"
p95_window=$(echo "${summary_response}" | jq -r '.window60s.p95_ms // "null"')
recall_window=$(echo "${summary_response}" | jq -r '.window60s.recall_at_10 // "null"')
tps_window=$(echo "${summary_response}" | jq -r '.window60s.tps // 0')
samples_window=$(echo "${summary_response}" | jq -r '.window60s.samples // 0')

log_report "  p95_ms: ${p95_window}"
log_report "  recall_at_10: ${recall_window}"
log_report "  tps: ${tps_window}"
log_report "  samples: ${samples_window}"
log_report ""

# Final verdict
log_report "========================================="
if [ "${errors}" -eq 0 ]; then
    log_info "Verification PASSED ✅"
    log_report "✅ Verification PASSED"
    log_report ""
    log_report "Next steps:"
    log_report "1. Refresh frontend at http://localhost:3000"
    log_report "2. Observe P95 and Recall@10 charts populate within 10-20s"
    log_report "3. Verify no React errors in browser console"
else
    log_error "Verification FAILED with ${errors} error(s) ❌"
    log_report "❌ Verification FAILED (${errors} errors)"
    log_report ""
    log_report "See ${OUTPUT_DIR}/summary_raw.json for full response"
fi
log_report "========================================="
log_report ""
log_report "Report saved to: ${OUTPUT_FILE}"

# Exit with appropriate code
exit "${errors}"

