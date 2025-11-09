#!/bin/bash
#
# Chunking Strategy Comparison - Convenience Wrapper
#
# This script runs the complete chunking comparison pipeline:
# 1. Build three collections (Para/Sent/Window)
# 2. Health checks
# 3. Experiments
# 4. Analysis
#
# Usage:
#   bash scripts/run_chunk_comparison.sh [OPTIONS]
#
# Options:
#   --api-url URL         API base URL (default: http://andy-wsl:8000)
#   --sample N            Sample N queries for fast testing
#   --skip-build          Skip collection building
#   --skip-health         Skip health checks
#   --recreate            Recreate collections if they exist
#   --help                Show this help message
#

set -euo pipefail

# Default values
API_URL="http://andy-wsl:8000"
SAMPLE_QUERIES=""
SKIP_BUILD=""
SKIP_HEALTH=""
RECREATE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --sample)
            SAMPLE_QUERIES="--sample-queries $2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD="--skip-build"
            shift
            ;;
        --skip-health)
            SKIP_HEALTH="--skip-health"
            shift
            ;;
        --recreate)
            RECREATE="--recreate"
            shift
            ;;
        --help)
            echo "Usage: bash scripts/run_chunk_comparison.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --api-url URL         API base URL (default: http://andy-wsl:8000)"
            echo "  --sample N            Sample N queries for fast testing"
            echo "  --skip-build          Skip collection building"
            echo "  --skip-health         Skip health checks"
            echo "  --recreate            Recreate collections if they exist"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  # Full pipeline"
            echo "  bash scripts/run_chunk_comparison.sh --api-url http://andy-wsl:8000"
            echo ""
            echo "  # Fast test (100 queries)"
            echo "  bash scripts/run_chunk_comparison.sh --sample 100 --recreate"
            echo ""
            echo "  # Skip building (use existing collections)"
            echo "  bash scripts/run_chunk_comparison.sh --skip-build"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print configuration
echo "============================================"
echo "CHUNKING STRATEGY COMPARISON"
echo "============================================"
echo "API URL: $API_URL"
echo "Sample queries: ${SAMPLE_QUERIES:-all}"
echo "Skip build: ${SKIP_BUILD:-no}"
echo "Skip health: ${SKIP_HEALTH:-no}"
echo "Recreate: ${RECREATE:-no}"
echo "============================================"
echo ""

# Check Python is available
if ! command -v python &> /dev/null; then
    echo "ERROR: python not found in PATH"
    exit 1
fi

# Check if API is reachable
echo "Checking API health..."
if ! curl -sf "${API_URL}/api/health" > /dev/null 2>&1; then
    echo "WARNING: API at ${API_URL} not reachable"
    echo "Please start the API server first:"
    echo "  docker-compose up -d"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run pipeline
echo ""
echo "Starting pipeline..."
echo ""

python experiments/run_chunk_comparison.py \
    --api-url "$API_URL" \
    $SAMPLE_QUERIES \
    $SKIP_BUILD \
    $SKIP_HEALTH \
    $RECREATE

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ PIPELINE COMPLETED SUCCESSFULLY"
    echo "============================================"
    echo ""
    echo "View results:"
    echo "  - Winners: cat reports/winners_chunk.json"
    echo "  - Recommendations: cat reports/chunk_recommendations.txt"
    echo "  - Charts: ls reports/chunk_charts/"
    echo ""
else
    echo ""
    echo "============================================"
    echo "❌ PIPELINE FAILED"
    echo "============================================"
    echo ""
    echo "Check logs above for errors"
    exit 1
fi

