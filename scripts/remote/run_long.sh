#!/bin/bash
# =============================================================================
# Remote Long-Run Script for AutoTuner (tmux-safe)
# =============================================================================
set -euo pipefail

# === Configuration ===
DURATION=${DURATION:-3600}
QPS=${QPS:-12}
BUCKET=${BUCKET:-10}
SCENARIOS=${SCENARIOS:-"A"}
PACK_ROOT=${PACK_ROOT:-~/runs/$(date +%Y%m%d_%H%M)}
REMOTE_BASE=${REMOTE_BASE:-~/searchforge}

# === New: Phase control ===
RUN_SINGLE=${RUN_SINGLE:-1}
RUN_MULTI=${RUN_MULTI:-1}
SINGLE_DURATION=${SINGLE_DURATION:-${DURATION}}
MULTI_DURATION=${MULTI_DURATION:-${DURATION}}

echo "==============================================="
echo "🚀 Starting AutoTuner Long-Run"
echo "==============================================="
echo "Run single-knob: ${RUN_SINGLE} (${SINGLE_DURATION}s)"
echo "Run multi-knob: ${RUN_MULTI} (${MULTI_DURATION}s)"
echo "QPS: ${QPS}"
echo "Bucket: ${BUCKET}s"
echo "Scenarios: ${SCENARIOS}"
echo "Output directory: ${PACK_ROOT}"
echo "==============================================="

# Create output directory structure
mkdir -p "${PACK_ROOT}/logs"
cd "${REMOTE_BASE}"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Run each scenario sequentially
for SC in ${SCENARIOS}; do
    echo ""
    echo ">>> [$(date '+%Y-%m-%d %H:%M:%S')] Starting scenario ${SC}..."
    
    # Phase 1: Single-knob baseline
    if [ "${RUN_SINGLE}" = "1" ]; then
        echo ">>> [$(date '+%Y-%m-%d %H:%M:%S')] Phase 1: Single-knob (${SINGLE_DURATION}s)..."
        echo ">>> Logs: ${PACK_ROOT}/logs/${SC}_single.log"
        
        python3 scripts/run_demo_pack.py \
            --mode live \
            --scenario "${SC}" \
            --duration-sec "${SINGLE_DURATION}" \
            --bucket-sec "${BUCKET}" \
            --qps "${QPS}" \
            --pack-out "${PACK_ROOT}" \
            --notes "Alienware long run ${SC} single-knob" \
            > "${PACK_ROOT}/logs/${SC}_single.log" 2>&1
        
        echo ">>> [$(date '+%Y-%m-%d %H:%M:%S')] Phase 1 completed ✓"
    fi
    
    # Phase 2: Multi-knob with brain
    if [ "${RUN_MULTI}" = "1" ]; then
        echo ">>> [$(date '+%Y-%m-%d %H:%M:%S')] Phase 2: Multi-knob (${MULTI_DURATION}s)..."
        echo ">>> Logs: ${PACK_ROOT}/logs/${SC}_multi.log"
        
        python3 scripts/run_demo_pack.py \
            --mode live \
            --scenario "${SC}" \
            --duration-sec "${MULTI_DURATION}" \
            --bucket-sec "${BUCKET}" \
            --qps "${QPS}" \
            --pack-out "${PACK_ROOT}" \
            --notes "Alienware long run ${SC} multi-knob" \
            > "${PACK_ROOT}/logs/${SC}_multi.log" 2>&1
        
        echo ">>> [$(date '+%Y-%m-%d %H:%M:%S')] Phase 2 completed ✓"
    fi
    
    echo ">>> [$(date '+%Y-%m-%d %H:%M:%S')] Scenario ${SC} completed ✓"
done

# Package results
echo ""
echo ">>> Packaging results..."
cd "${PACK_ROOT}/.."
BASENAME=$(basename "${PACK_ROOT}")
tar -czf "${BASENAME}.tgz" "${BASENAME}"
echo ">>> Package created: ${PACK_ROOT}.tgz"

# Final summary
echo ""
echo "==============================================="
echo "✅ ALL SCENARIOS COMPLETED"
echo "==============================================="
echo "Output directory: ${PACK_ROOT}"
echo "Package: ${PACK_ROOT}.tgz"
echo "Scenarios run: ${SCENARIOS}"
echo "End time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==============================================="
echo "DONE:${PACK_ROOT}"
