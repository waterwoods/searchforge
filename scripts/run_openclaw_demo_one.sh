#!/bin/bash
# OpenClaw Step 3 MVP Demo: Fetch, extract, and summarize one webpage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$REPO_DIR/results/openclaw_demo"

echo "=========================================="
echo "OpenClaw Step 3 MVP Demo"
echo "=========================================="
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Fetch and extract
echo "Step 1: Fetching and extracting text..."
python3 "$SCRIPT_DIR/fetch_extract_one.py"
echo ""

# Step 2: Summarize
echo "Step 2: Summarizing with Ollama..."
python3 "$SCRIPT_DIR/summarize_one.py"
echo ""

# Show results
echo "=========================================="
echo "Results"
echo "=========================================="
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR"/*.{json,html,txt,md} 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

# Show preview of extracted text
if [ -f "$OUTPUT_DIR/extracted.txt" ]; then
    echo "Extracted text preview (first 500 chars):"
    echo "---"
    head -c 500 "$OUTPUT_DIR/extracted.txt"
    echo ""
    echo "---"
    echo ""
fi

# Show preview of summary
if [ -f "$OUTPUT_DIR/summary.md" ]; then
    echo "Summary preview (first 30 lines):"
    echo "---"
    head -n 30 "$OUTPUT_DIR/summary.md"
    echo "---"
    echo ""
fi

echo "=========================================="
echo "Demo complete!"
echo "=========================================="
echo ""
echo "Output files are in: $OUTPUT_DIR"
