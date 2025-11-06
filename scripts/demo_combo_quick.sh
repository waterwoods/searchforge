#!/bin/bash
# demo_combo_quick.sh - Quick Demo (5 minutes) of 20-Minute Combo Test
# =====================================================================
# Fast demonstration of full system integration for testing/demo purposes
#
# Usage:
#   ./scripts/demo_combo_quick.sh                    # 5-minute demo
#   ./scripts/demo_combo_quick.sh --with-agent       # With Agent V3

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WITH_AGENT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-agent)
            WITH_AGENT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo
echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║        QUICK DEMO: 5-Minute Combo Test                     ║${NC}"
echo -e "${BOLD}${CYAN}║        (Fast preview of 20-minute full test)               ║${NC}"
echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo

cd "$PROJECT_ROOT"

echo -e "${GREEN}📋 Demo Configuration:${NC}"
echo "  • Duration: 5 minutes (for demo)"
echo "  • QPS: 2 (light load)"
echo "  • Agent: $WITH_AGENT"
echo

# Run quick test
AGENT_FLAG=""
if [ "$WITH_AGENT" = true ]; then
    AGENT_FLAG="--with-agent --agent-version v3"
fi

./scripts/run_combo_20min.sh \
    --qps 2 \
    --window 300 \
    $AGENT_FLAG

echo
echo -e "${BOLD}${GREEN}✨ Quick Demo Complete!${NC}"
echo
echo "For the full 20-minute test, run:"
echo "  ${YELLOW}./scripts/run_combo_20min.sh --with-agent --agent-version v3${NC}"
echo

