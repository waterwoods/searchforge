#!/bin/bash
# =============================================================================
# Remote Status Check Script
# =============================================================================
set -euo pipefail

SESSION=${SESSION:-"autotuner_long"}
PACK_ROOT=${PACK_ROOT:-~/runs/*}

echo "==============================================="
echo "📊 AutoTuner Remote Status"
echo "==============================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check tmux session
echo "=== TMUX Session Status ==="
if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "✓ Session '${SESSION}' is ACTIVE"
    tmux list-sessions | grep "${SESSION}" || true
else
    echo "○ Session '${SESSION}' not found (IDLE)"
fi

echo ""
echo "=== Recent Logs ==="

# Find the most recent run directory
LATEST_DIR=$(ls -td ${PACK_ROOT} 2>/dev/null | head -n 1 || echo "")

if [ -z "${LATEST_DIR}" ]; then
    echo "No run directories found"
else
    echo "Latest run: ${LATEST_DIR}"
    echo ""
    
    # Show logs from all scenarios
    for LOG in "${LATEST_DIR}"/logs/*.log; do
        if [ -f "${LOG}" ]; then
            echo "--- $(basename ${LOG}) (last 20 lines) ---"
            tail -n 20 "${LOG}" 2>/dev/null || echo "Cannot read log"
            echo ""
        fi
    done
    
    # Check if package exists
    if [ -f "${LATEST_DIR}.tgz" ]; then
        echo "✓ Results package ready: ${LATEST_DIR}.tgz"
        ls -lh "${LATEST_DIR}.tgz"
    fi
fi

echo "==============================================="
