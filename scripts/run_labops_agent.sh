#!/bin/bash
# run_labops_agent.sh - One-liner runner for LabOps Agent V1
# ===========================================================
# Autonomous COMBO experiment orchestration.
#
# Usage:
#   ./scripts/run_labops_agent.sh                    # Normal run (safe mode)
#   ./scripts/run_labops_agent.sh --auto-apply       # Auto-apply flags on PASS
#   ./scripts/run_labops_agent.sh --dry-run          # Dry run (no execution)
#   ./scripts/run_labops_agent.sh --resume           # Resume from checkpoint (TODO)
#   ./scripts/run_labops_agent.sh --config custom.yaml  # Custom config
#
# Output:
#   - reports/LABOPS_AGENT_SUMMARY.txt (≤60 lines)
#   - agents/labops/state/history.jsonl (append-only)

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEFAULT_CONFIG="agents/labops/plan/plan_combo.yaml"

# Parse arguments
CONFIG_PATH="$DEFAULT_CONFIG"
DRY_RUN=""
RESUME=""
AUTO_APPLY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-apply)
            AUTO_APPLY="--auto-apply"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --resume)
            RESUME="--resume"
            shift
            ;;
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--auto-apply] [--dry-run] [--resume] [--config PATH]"
            exit 1
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================================"
echo "LABOPS AGENT V1 - RUNNER"
echo "======================================================================"
echo "Project Root: $PROJECT_ROOT"
echo "Config: $CONFIG_PATH"
echo "Mode: ${DRY_RUN:-LIVE}${RESUME:+ (RESUME)}"
echo "======================================================================"
echo

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} python3 is required but not installed"
    exit 1
fi

# Check if PyYAML is available
if ! python3 -c "import yaml" 2>/dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} PyYAML not found. Installing..."
    pip3 install PyYAML >/dev/null 2>&1 || {
        echo -e "${RED}[ERROR]${NC} Failed to install PyYAML"
        exit 1
    }
fi

# Check if requests is available (optional, falls back to urllib)
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} requests library not found (will use urllib fallback)"
fi

# Run agent
cd "$PROJECT_ROOT"

echo -e "${BLUE}[INFO]${NC} Starting LabOps Agent..."
echo

python3 -m agents.labops.agent_runner \
    --config "$CONFIG_PATH" \
    $AUTO_APPLY \
    $DRY_RUN \
    $RESUME

EXIT_CODE=$?

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS]${NC} Agent run completed"
    echo
    echo "View summary:"
    echo "  cat reports/LABOPS_AGENT_SUMMARY.txt"
    echo
    echo "View history:"
    echo "  tail agents/labops/state/history.jsonl"
else
    echo -e "${RED}[FAILED]${NC} Agent run failed (exit code: $EXIT_CODE)"
    echo
    echo "Check report:"
    echo "  cat reports/LABOPS_AGENT_SUMMARY.txt"
fi

echo "======================================================================"

exit $EXIT_CODE

