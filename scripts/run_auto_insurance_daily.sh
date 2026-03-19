#!/bin/bash
# Auto Insurance Daily Automation Runner
# ======================================
# Runs daily crawl, embed, upsert, and evaluation pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# Configuration
CONFIG_FILE="${REPO_DIR}/results/auto_insurance/daily_targets.json"
DATE_STR=$(date +%Y-%m-%d)
DAILY_DIR="${REPO_DIR}/results/auto_insurance/daily/${DATE_STR}"
LOG_FILE="${DAILY_DIR}/run.log"
YESTERDAY_DATE=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null || echo "")
YESTERDAY_DIR="${REPO_DIR}/results/auto_insurance/daily/${YESTERDAY_DATE}"

# Exit codes
EXIT_SUCCESS=0
EXIT_INGEST_FAILED=10
EXIT_UPSERT_FAILED=20
EXIT_EVAL_FAILED=30

# Create daily directory
mkdir -p "$DAILY_DIR"

# Load environment variables from .env.cloudrun with export
set -a
[ -f ".env.cloudrun" ] && source ".env.cloudrun"
set +a

# Set quality gate min_chars for chunks (default 240, can be overridden)
# Note: Ingest uses 800 for page-level, quality gate uses 240 for chunk-level
# Backward compatibility: if QUALITY_GATE_MIN_CHARS is set, it takes priority
: "${QUALITY_GATE_MIN_CHARS_CHUNK:=240}"
export QUALITY_GATE_MIN_CHARS_CHUNK
# If user explicitly set QUALITY_GATE_MIN_CHARS, use it (backward compatible)
if [ -n "${QUALITY_GATE_MIN_CHARS:-}" ]; then
    export QUALITY_GATE_MIN_CHARS
else
    # Use chunk threshold as default
    export QUALITY_GATE_MIN_CHARS="$QUALITY_GATE_MIN_CHARS_CHUNK"
fi

# Validate required environment variables
if [ -z "${QDRANT_URL:-}" ]; then
    echo "ERROR: QDRANT_URL environment variable is not set"
    echo "Please ensure .env.cloudrun exists and contains QDRANT_URL"
    exit 1
fi

if [ -z "${QDRANT_API_KEY:-}" ]; then
    echo "WARNING: QDRANT_API_KEY environment variable is not set"
    echo "Connection may fail if authentication is required"
fi

# Mask and display QDRANT_URL (show host only, not full URL with key)
QDRANT_HOST=$(echo "$QDRANT_URL" | sed -E 's|https?://([^/]+).*|\1|')
echo "Qdrant Host: $QDRANT_HOST"
echo "Collection: auto_insurance_v2_clean"
echo "Ingest Min Chars (page-level): 800"
echo "Quality Gate Min Chars (chunk-level): $QUALITY_GATE_MIN_CHARS"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Function to write failure report
write_failure_report() {
    local step="$1"
    local error_log="$2"
    local exit_code="$3"
    
    cat > "${DAILY_DIR}/FAILED.md" << EOF
# Daily Automation Failure Report

**Date**: ${DATE_STR}
**Failed Step**: ${step}
**Exit Code**: ${exit_code}
**Timestamp**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Error Details

\`\`\`
$(tail -50 "$error_log" 2>/dev/null || echo "No error log available")
\`\`\`

## Next Actions

1. Check the full log: \`cat ${LOG_FILE}\`
2. Verify environment variables are set (QDRANT_URL, QDRANT_API_KEY)
3. Check network connectivity
4. Review ingest/upsert/eval logs in ${DAILY_DIR}/
5. Re-run manually: \`bash ${SCRIPT_DIR}/run_auto_insurance_daily.sh\`

## TODO: Alert Hook

A webhook/email alert function should be called here in production:
\`\`\`python
# TODO: Implement alert hook
# send_alert(step="${step}", error_log="${error_log}", exit_code=${exit_code})
\`\`\`
EOF
    
    echo ""
    echo "❌ FAILED: ${step}" | tee -a "$LOG_FILE"
    echo "   See ${DAILY_DIR}/FAILED.md for details" | tee -a "$LOG_FILE"
}

# Function to check if step succeeded
check_step() {
    local step_name="$1"
    local exit_code="$2"
    local log_file="$3"
    
    if [ $exit_code -ne 0 ]; then
        write_failure_report "$step_name" "$log_file" "$exit_code"
        return $exit_code
    fi
    return 0
}

# Start logging
log "=========================================="
log "Auto Insurance Daily Automation"
log "Date: ${DATE_STR}"
log "=========================================="
log ""

# Step 1: Ingest/Crawl
log "Step 1: Ingest/Crawl"
log "Config: ${CONFIG_FILE}"
log "Output: ${DAILY_DIR}/corpus_raw.jsonl"
log ""

if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR: Config file not found: ${CONFIG_FILE}"
    write_failure_report "Config Check" "$LOG_FILE" 1
    exit $EXIT_INGEST_FAILED
fi

python3 pipelines/auto_insurance_ingest.py \
    --config "$CONFIG_FILE" \
    --output "${DAILY_DIR}/corpus_raw.jsonl" \
    --max-pages-per-source 50 \
    --min-chars 800 \
    --summary-dir "$DAILY_DIR" \
    2>&1 | tee -a "$LOG_FILE"

INGEST_EXIT=${PIPESTATUS[0]}
if ! check_step "Ingest" $INGEST_EXIT "$LOG_FILE"; then
    exit $EXIT_INGEST_FAILED
fi

if [ ! -f "${DAILY_DIR}/corpus_raw.jsonl" ] || [ ! -s "${DAILY_DIR}/corpus_raw.jsonl" ]; then
    log "ERROR: Ingest produced no output or empty file"
    write_failure_report "Ingest Validation" "$LOG_FILE" 1
    exit $EXIT_INGEST_FAILED
fi

DOC_COUNT=$(wc -l < "${DAILY_DIR}/corpus_raw.jsonl" | tr -d ' ')
log "✅ Ingest completed: ${DOC_COUNT} documents"
log ""

# Step 2: Diff Filter
log "Step 2: Diff Filter (remove unchanged content)"
log ""

if [ -n "$YESTERDAY_DATE" ] && [ -f "${YESTERDAY_DIR}/corpus_raw.jsonl" ]; then
    log "Comparing with yesterday's corpus: ${YESTERDAY_DIR}/corpus_raw.jsonl"
    python3 scripts/daily_diff_filter.py \
        "${DAILY_DIR}/corpus_raw.jsonl" \
        "${YESTERDAY_DIR}/corpus_raw.jsonl" \
        "${DAILY_DIR}/corpus_filtered.jsonl" \
        2>&1 | tee -a "$LOG_FILE"
    
    FILTER_EXIT=${PIPESTATUS[0]}
    if [ $FILTER_EXIT -ne 0 ]; then
        log "WARNING: Diff filter failed, using raw corpus"
        cp "${DAILY_DIR}/corpus_raw.jsonl" "${DAILY_DIR}/corpus_filtered.jsonl"
    fi
else
    log "No yesterday's corpus found, using raw corpus (first run)"
    cp "${DAILY_DIR}/corpus_raw.jsonl" "${DAILY_DIR}/corpus_filtered.jsonl"
fi

FILTERED_COUNT=$(wc -l < "${DAILY_DIR}/corpus_filtered.jsonl" | tr -d ' ')
log "✅ Filter completed: ${FILTERED_COUNT} documents to embed"
log ""

# Step 2.5: Quality Gate
log "Step 2.5: Quality Gate (filter bad data before upsert)"
log ""

python3 pipelines/quality_gate_auto_insurance.py \
    --input "${DAILY_DIR}/corpus_filtered.jsonl" \
    --output-corpus "${DAILY_DIR}/corpus_gated.jsonl" \
    --output-dropped "${DAILY_DIR}/dropped.jsonl" \
    --report-dir "$DAILY_DIR" \
    --config "$CONFIG_FILE" \
    --min-chars "$QUALITY_GATE_MIN_CHARS" \
    2>&1 | tee -a "$LOG_FILE"

GATE_EXIT=${PIPESTATUS[0]}
if [ $GATE_EXIT -ne 0 ]; then
    log "ERROR: Quality gate failed"
    write_failure_report "Quality Gate" "$LOG_FILE" $GATE_EXIT
    exit $EXIT_UPSERT_FAILED
fi

if [ ! -f "${DAILY_DIR}/corpus_gated.jsonl" ] || [ ! -s "${DAILY_DIR}/corpus_gated.jsonl" ]; then
    log "ERROR: Quality gate produced no output or empty file"
    write_failure_report "Quality Gate Validation" "$LOG_FILE" 1
    exit $EXIT_UPSERT_FAILED
fi

GATED_COUNT=$(wc -l < "${DAILY_DIR}/corpus_gated.jsonl" | tr -d ' ')
DROPPED_COUNT=$(wc -l < "${DAILY_DIR}/dropped.jsonl" | tr -d ' ' 2>/dev/null || echo "0")
log "✅ Quality gate completed: ${GATED_COUNT} passed, ${DROPPED_COUNT} dropped"
log ""

# Step 3: Embed and Upsert
log "Step 3: Embed and Upsert to Qdrant"
log "Collection: auto_insurance_v2_clean"
log ""

# Environment variables already validated at script start

python3 pipelines/embed_and_upsert.py \
    --input "${DAILY_DIR}/corpus_gated.jsonl" \
    --collection auto_insurance_v2_clean \
    --batch-size 64 \
    --report-dir "$DAILY_DIR" \
    2>&1 | tee -a "$LOG_FILE"

UPSERT_EXIT=${PIPESTATUS[0]}
if ! check_step "Upsert" $UPSERT_EXIT "$LOG_FILE"; then
    exit $EXIT_UPSERT_FAILED
fi

log "✅ Upsert completed"
log ""

# Step 4: Evaluation
log "Step 4: RAG Evaluation"
log ""

EVAL_STATUS="PASS"
python3 scripts/eval_auto_insurance_rag.py \
    --collection auto_insurance_v2_clean \
    --report-dir "$DAILY_DIR" \
    2>&1 | tee -a "$LOG_FILE" || true

EVAL_EXIT=${PIPESTATUS[0]}
if [ $EVAL_EXIT -ne 0 ]; then
    EVAL_STATUS="FAIL"
    log "⚠️  Evaluation failed (exit code: ${EVAL_EXIT}), but continuing to generate daily report"
    write_failure_report "Evaluation" "$LOG_FILE" $EVAL_EXIT
else
    log "✅ Evaluation completed"
fi
log ""

# Step 5: Generate Daily Report
log "Step 5: Generating Daily Report"
log ""

# Load quality gate stats if available
GATED_COUNT=${GATED_COUNT:-0}
DROPPED_COUNT=${DROPPED_COUNT:-0}
GATE_PASS_RATE="N/A"
if [ -f "${DAILY_DIR}/run_summary.json" ]; then
    GATE_PASS_RATE=$(python3 -c "import json; d=json.load(open('${DAILY_DIR}/run_summary.json')); print(f\"{d.get('quality_gate', {}).get('pass_rate', 0):.1f}%\")" 2>/dev/null || echo "N/A")
fi

# Determine overall status
OVERALL_STATUS="SUCCESS"
if [ "$EVAL_STATUS" = "FAIL" ]; then
    OVERALL_STATUS="PARTIAL (Eval Failed)"
fi

cat > "${DAILY_DIR}/DAILY_REPORT.md" << EOF
# Daily Automation Report

**Date**: ${DATE_STR}
**Generated**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Summary

$(if [ "$OVERALL_STATUS" = "SUCCESS" ]; then echo "✅ **Status**: SUCCESS"; else echo "⚠️ **Status**: ${OVERALL_STATUS}"; fi)

## Step Results

### 1. Ingest/Crawl
- **Input**: ${CONFIG_FILE}
- **Output**: corpus_raw.jsonl
- **Documents Created**: ${DOC_COUNT}

### 2. Diff Filter
- **Input**: corpus_raw.jsonl
- **Output**: corpus_filtered.jsonl
- **Filtered Documents**: ${FILTERED_COUNT}

### 2.5. Quality Gate
- **Input**: corpus_filtered.jsonl
- **Output**: corpus_gated.jsonl
- **Passed**: ${GATED_COUNT}
- **Dropped**: ${DROPPED_COUNT}
- **Pass Rate**: ${GATE_PASS_RATE}
- **Report**: See FILTER_REPORT.md

### 3. Embed and Upsert
- **Collection**: auto_insurance_v2_clean
- **Input**: corpus_gated.jsonl
- **Status**: ✅ Completed
- **Report**: See UPSERT_V2_CLEAN_REPORT.md (if generated)

### 4. Evaluation
- **Collection**: auto_insurance_v2_clean
- **Status**: $(if [ "$EVAL_STATUS" = "PASS" ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi)
- **Report**: See EVAL_REPORT.md (if generated)

## Files Generated

- \`corpus_raw.jsonl\` - Raw crawled documents
- \`corpus_filtered.jsonl\` - Filtered documents (unchanged removed)
- \`corpus_gated.jsonl\` - Quality-gated documents (passed filters)
- \`dropped.jsonl\` - Dropped documents with reasons
- \`run.log\` - Full execution log
- \`run_summary.json\` - Quality gate statistics
- \`FILTER_REPORT.md\` - Quality gate filter report
- \`EVAL_REPORT.md\` - Evaluation results (if generated)
- \`DAILY_REPORT.md\` - This report

## Next Steps

1. Review quality gate results: \`cat ${DAILY_DIR}/FILTER_REPORT.md\`
2. Check dropped documents: \`head -n 10 ${DAILY_DIR}/dropped.jsonl\`
3. Review evaluation results: \`cat ${DAILY_DIR}/EVAL_REPORT.md\` (if available)
4. Check collection status in Qdrant dashboard
5. Monitor for any errors in run.log

---
*Generated by auto_insurance_daily automation*
EOF

log "✅ Daily report generated: ${DAILY_DIR}/DAILY_REPORT.md"
log ""

# Final summary
log "=========================================="
log "Daily Automation Complete"
log "=========================================="
log "Date: ${DATE_STR}"
log "Documents: ${DOC_COUNT} raw, ${FILTERED_COUNT} diff-filtered, ${GATED_COUNT} quality-gated"
log "Status: ${OVERALL_STATUS}"
log ""
log "Reports:"
log "  - Daily Report: ${DAILY_DIR}/DAILY_REPORT.md"
log "  - Quality Gate: ${DAILY_DIR}/FILTER_REPORT.md"
if [ "$EVAL_STATUS" = "PASS" ]; then
    log "  - Evaluation: ${DAILY_DIR}/EVAL_REPORT.md"
fi
log "  - Full Log: ${LOG_FILE}"
log ""

# Exit with success even if eval failed (as per requirements)
exit $EXIT_SUCCESS
