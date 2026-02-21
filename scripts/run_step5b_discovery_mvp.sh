#!/bin/bash
# Step 5B MVP: Auto-discover new insurance information sources
# Runs discovery + verification pipeline end-to-end

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$REPO_DIR/results/auto_insurance_discovery"

echo "=========================================="
echo "Step 5B MVP: Auto-Insurance Source Discovery"
echo "=========================================="
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Discovery
echo "Step 1: Discovering candidate sources..."
echo "----------------------------------------"
python3 "$SCRIPT_DIR/discover_auto_insurance_sources.py"
echo ""

# Step 2: Verification
echo "Step 2: Verifying discovered sources..."
echo "----------------------------------------"
python3 "$SCRIPT_DIR/verify_discovered_sources.py"
echo ""

# Show results
echo "=========================================="
echo "Results"
echo "=========================================="
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR"/*.{json,jsonl,md} 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

# Show summary
if [ -f "$OUTPUT_DIR/REPORT.md" ]; then
    echo "Report preview (first 40 lines):"
    echo "---"
    head -n 40 "$OUTPUT_DIR/REPORT.md"
    echo "---"
    echo ""
fi

# Show passing candidates count
if [ -f "$OUTPUT_DIR/passing.json" ]; then
    PASSING_COUNT=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_DIR/passing.json'))))" 2>/dev/null || echo "0")
    echo "Passing candidates: $PASSING_COUNT"
    echo ""
fi

echo "=========================================="
echo "MVP Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review: $OUTPUT_DIR/REPORT.md"
echo "  2. Check passing candidates: $OUTPUT_DIR/passing.json"
echo "  3. Review verification corpus: $OUTPUT_DIR/verify_corpus.jsonl"
echo "  4. (Optional) Append to data_sources.json if passing domains are safe"
echo ""
