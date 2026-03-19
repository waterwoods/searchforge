#!/bin/bash
# Auto Insurance RAG Refresh Automation Script
# ============================================
# One-command script to: crawl → embed → upsert → evaluate
# Safe to re-run (idempotent)
# Never prints secrets

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Configuration
COLLECTION_NAME="auto_insurance_v2_clean"
OUTPUT_JSONL="data/auto_insurance_corpus.jsonl"
CONFIG_DIR="docs/prompt2_input"
REPORT_DIR="results/auto_insurance"
RUN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="$REPORT_DIR/runs/$RUN_TIMESTAMP"

# Create run directory
mkdir -p "$RUN_DIR"

# Logging
LOG_FILE="$RUN_DIR/refresh.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "Auto Insurance RAG Refresh"
echo "=========================================="
echo "Timestamp: $(date -Iseconds)"
echo "Run directory: $RUN_DIR"
echo ""

# Step 1: Preflight env check
echo "Step 1: Preflight environment check..."
if [ -f "scripts/check_qdrant_env.py" ]; then
    python3 scripts/check_qdrant_env.py || {
        echo "❌ Environment check failed"
        exit 1
    }
else
    # Basic check
    if [ -z "${QDRANT_URL:-}" ]; then
        echo "❌ QDRANT_URL not set"
        exit 1
    fi
    echo "✅ Environment variables present"
fi
echo ""

# Step 2: Crawl incremental
echo "Step 2: Crawling data sources..."
ALLOW_DOMAINS="dmv.ca.gov,insurance.ca.gov,geico.com,progressive.com"
python3 pipelines/auto_insurance_ingest.py \
    --config-dir "$CONFIG_DIR" \
    --output "$OUTPUT_JSONL" \
    --max-pages-per-source 300 \
    --allow-domains "$ALLOW_DOMAINS" \
    --min-chars 800 \
    --strict-content-type 1 \
    --summary-dir "$REPORT_DIR" \
    2>&1 | tee "$RUN_DIR/crawl.log"

CRAWL_EXIT=${PIPESTATUS[0]}
if [ $CRAWL_EXIT -ne 0 ]; then
    echo "⚠️  Crawl completed with warnings/errors (exit code: $CRAWL_EXIT)"
fi
echo ""

# Step 3: Embed and upsert
echo "Step 3: Embedding and upserting to Qdrant..."
python3 pipelines/embed_and_upsert.py \
    --input "$OUTPUT_JSONL" \
    --collection "$COLLECTION_NAME" \
    --batch-size 64 \
    2>&1 | tee "$RUN_DIR/upsert.log"

UPSERT_EXIT=${PIPESTATUS[0]}
if [ $UPSERT_EXIT -ne 0 ]; then
    echo "❌ Embedding/upsert failed (exit code: $UPSERT_EXIT)"
    exit $UPSERT_EXIT
fi
echo ""

# Step 4: Run evaluation
echo "Step 4: Running evaluation..."
python3 scripts/eval_auto_insurance_rag.py \
    --collection "$COLLECTION_NAME" \
    --report-dir "$REPORT_DIR" \
    2>&1 | tee "$RUN_DIR/eval.log"

EVAL_EXIT=${PIPESTATUS[0]}
if [ $EVAL_EXIT -ne 0 ]; then
    echo "❌ Evaluation FAILED"
    echo ""
    echo "Check $REPORT_DIR/EVAL_REPORT.md for details"
    exit $EVAL_EXIT
fi
echo ""

# Success
echo "=========================================="
echo "✅ Refresh completed successfully"
echo "=========================================="
echo "Reports:"
echo "  - Evaluation: $REPORT_DIR/EVAL_REPORT.md"
echo "  - Upsert: $REPORT_DIR/UPSERT_V2_CLEAN_REPORT.md"
echo "  - Run logs: $RUN_DIR/"
echo ""

exit 0
