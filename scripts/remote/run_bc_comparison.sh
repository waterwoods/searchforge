#!/bin/bash
# =============================================================================
# B/C Scenario Comparison Runner (Single vs Multi-knob)
# =============================================================================
set -euo pipefail

# === Remote Configuration ===
REMOTE_USER_HOST="${REMOTE_USER_HOST:-andy@100.67.88.114}"
REMOTE_BASE="${REMOTE_BASE:-~/searchforge}"
TIMESTAMP=$(date +%Y%m%d_%H%M)

# === Experiment Configuration ===
BUCKET=10
QPS=12
SINGLE_DURATION=600   # 10 minutes
MULTI_DURATION=2700   # 45 minutes

# === Colors for output ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================="
echo "🚀 B/C Scenario Comparison Runner"
echo "=============================================="
echo -e "Remote: ${REMOTE_USER_HOST}"
echo -e "Timestamp: ${TIMESTAMP}"
echo -e "Single-knob: ${SINGLE_DURATION}s (10m)"
echo -e "Multi-knob: ${MULTI_DURATION}s (45m)"
echo -e "===============================================${NC}\n"

# === Step 1: Prechecks ===
echo -e "${YELLOW}[Step 1/5] Running prechecks on remote...${NC}"

# Check if remote is reachable
if ! ssh -o ConnectTimeout=5 "${REMOTE_USER_HOST}" "echo 'Connected'" >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to remote host${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Remote host reachable${NC}"

# Upload the patched run_long.sh script
echo -e "${YELLOW}Uploading patched run_long.sh...${NC}"
scp scripts/remote/run_long.sh "${REMOTE_USER_HOST}:${REMOTE_BASE}/scripts/remote/"
echo -e "${GREEN}✓ Script uploaded${NC}"

# Start qdrant if not running
echo -e "${YELLOW}Starting qdrant...${NC}"
ssh "${REMOTE_USER_HOST}" "cd ${REMOTE_BASE} && docker compose up -d qdrant && sleep 5"
echo -e "${GREEN}✓ Qdrant started${NC}"

# Check if collection exists
echo -e "${YELLOW}Checking collection beir_fiqa_full_ta...${NC}"
COLLECTION_EXISTS=$(ssh "${REMOTE_USER_HOST}" "cd ${REMOTE_BASE} && python3 -c \"
from qdrant_client import QdrantClient
client = QdrantClient('localhost', port=6333)
collections = [c.name for c in client.get_collections().collections]
print('1' if 'beir_fiqa_full_ta' in collections else '0')
\" 2>/dev/null || echo '0'")

if [ "${COLLECTION_EXISTS}" = "0" ]; then
    echo -e "${YELLOW}⚠️  Collection not found, populating...${NC}"
    ssh "${REMOTE_USER_HOST}" "cd ${REMOTE_BASE} && python3 data/populate_qdrant.py"
    echo -e "${GREEN}✓ Collection populated${NC}"
else
    echo -e "${GREEN}✓ Collection exists${NC}"
fi

echo ""

# === Step 2: Run Experiments ===
echo -e "${YELLOW}[Step 2/5] Launching experiments in tmux sessions...${NC}"

for SCENARIO in B C; do
    echo -e "\n${BLUE}=== Scenario ${SCENARIO} ===${NC}"
    
    # Single-knob baseline (10m)
    SESSION_SINGLE="autotuner_${SCENARIO}_single"
    PACK_ROOT_SINGLE="~/runs/${TIMESTAMP}_${SCENARIO}_single"
    
    echo -e "${YELLOW}Launching single-knob baseline (10m)...${NC}"
    ssh "${REMOTE_USER_HOST}" "tmux new-session -d -s ${SESSION_SINGLE} \
        \"export REMOTE_BASE=${REMOTE_BASE} && \
         export PACK_ROOT=${PACK_ROOT_SINGLE} && \
         export BUCKET=${BUCKET} && \
         export QPS=${QPS} && \
         export SCENARIOS=${SCENARIO} && \
         export RUN_SINGLE=1 && \
         export RUN_MULTI=0 && \
         export SINGLE_DURATION=${SINGLE_DURATION} && \
         cd ${REMOTE_BASE} && \
         bash scripts/remote/run_long.sh; \
         echo 'DONE:${PACK_ROOT_SINGLE}' >> /tmp/autotuner_${SCENARIO}_single.status; \
         exec bash\""
    echo -e "${GREEN}✓ Session ${SESSION_SINGLE} started${NC}"
    
    # Multi-knob full run (45m)
    SESSION_MULTI="autotuner_${SCENARIO}_multi"
    PACK_ROOT_MULTI="~/runs/${TIMESTAMP}_${SCENARIO}_multi"
    
    echo -e "${YELLOW}Launching multi-knob run (45m)...${NC}"
    ssh "${REMOTE_USER_HOST}" "tmux new-session -d -s ${SESSION_MULTI} \
        \"export REMOTE_BASE=${REMOTE_BASE} && \
         export PACK_ROOT=${PACK_ROOT_MULTI} && \
         export BUCKET=${BUCKET} && \
         export QPS=${QPS} && \
         export SCENARIOS=${SCENARIO} && \
         export RUN_SINGLE=0 && \
         export RUN_MULTI=1 && \
         export MULTI_DURATION=${MULTI_DURATION} && \
         cd ${REMOTE_BASE} && \
         bash scripts/remote/run_long.sh; \
         echo 'DONE:${PACK_ROOT_MULTI}' >> /tmp/autotuner_${SCENARIO}_multi.status; \
         exec bash\""
    echo -e "${GREEN}✓ Session ${SESSION_MULTI} started${NC}"
done

echo -e "\n${GREEN}✓ All 4 sessions launched (2 scenarios × 2 phases)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Monitor with:"
echo -e "  ssh ${REMOTE_USER_HOST} tmux ls"
echo -e "  ssh ${REMOTE_USER_HOST} tmux attach -t autotuner_B_single"
echo -e "  ssh ${REMOTE_USER_HOST} tmux attach -t autotuner_B_multi"
echo -e "  ssh ${REMOTE_USER_HOST} tmux attach -t autotuner_C_single"
echo -e "  ssh ${REMOTE_USER_HOST} tmux attach -t autotuner_C_multi"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# === Step 3: Wait for Completion ===
echo -e "${YELLOW}[Step 3/5] Waiting for experiments to complete...${NC}"
echo -e "${YELLOW}Expected completion times:${NC}"
echo -e "  Single-knob (10m): ~10 minutes"
echo -e "  Multi-knob (45m): ~45 minutes"
echo ""

WAIT_COUNT=0
MAX_WAIT=180  # 3 hours max wait (in minutes)
CHECK_INTERVAL=60  # Check every minute

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    B_SINGLE_DONE=$(ssh "${REMOTE_USER_HOST}" "[ -f /tmp/autotuner_B_single.status ] && echo 1 || echo 0")
    B_MULTI_DONE=$(ssh "${REMOTE_USER_HOST}" "[ -f /tmp/autotuner_B_multi.status ] && echo 1 || echo 0")
    C_SINGLE_DONE=$(ssh "${REMOTE_USER_HOST}" "[ -f /tmp/autotuner_C_single.status ] && echo 1 || echo 0")
    C_MULTI_DONE=$(ssh "${REMOTE_USER_HOST}" "[ -f /tmp/autotuner_C_multi.status ] && echo 1 || echo 0")
    
    ELAPSED_MIN=$((WAIT_COUNT))
    echo -e "${BLUE}[${ELAPSED_MIN}m elapsed]${NC} Status: B_single=${B_SINGLE_DONE} B_multi=${B_MULTI_DONE} C_single=${C_SINGLE_DONE} C_multi=${C_MULTI_DONE}"
    
    if [ "$B_SINGLE_DONE" = "1" ] && [ "$B_MULTI_DONE" = "1" ] && \
       [ "$C_SINGLE_DONE" = "1" ] && [ "$C_MULTI_DONE" = "1" ]; then
        echo -e "${GREEN}✓ All experiments completed!${NC}"
        break
    fi
    
    sleep $CHECK_INTERVAL
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ Timeout waiting for experiments${NC}"
    echo -e "${YELLOW}⚠️  Some experiments may still be running. Check tmux sessions manually.${NC}"
    exit 1
fi

echo ""

# === Step 4: Rsync Results Back ===
echo -e "${YELLOW}[Step 4/5] Syncing results back to local...${NC}"

LOCAL_RESULTS_DIR="${HOME}/Downloads/autotuner_runs/${TIMESTAMP}"
mkdir -p "${LOCAL_RESULTS_DIR}"

for SCENARIO in B C; do
    for PHASE in single multi; do
        REMOTE_PATH="~/runs/${TIMESTAMP}_${SCENARIO}_${PHASE}"
        LOCAL_PATH="${LOCAL_RESULTS_DIR}/${SCENARIO}_${PHASE}"
        
        echo -e "${YELLOW}Syncing ${SCENARIO}_${PHASE}...${NC}"
        rsync -avz --progress "${REMOTE_USER_HOST}:${REMOTE_PATH}/" "${LOCAL_PATH}/"
        echo -e "${GREEN}✓ ${SCENARIO}_${PHASE} synced${NC}"
    done
done

echo -e "${GREEN}✓ All results synced to: ${LOCAL_RESULTS_DIR}${NC}"
echo ""

# === Step 5: Open Results and Generate Verdict ===
echo -e "${YELLOW}[Step 5/5] Opening results and generating verdicts...${NC}"

for SCENARIO in B C; do
    for PHASE in single multi; do
        INDEX_HTML="${LOCAL_RESULTS_DIR}/${SCENARIO}_${PHASE}/index.html"
        if [ -f "${INDEX_HTML}" ]; then
            echo -e "${GREEN}Opening ${SCENARIO}_${PHASE}/index.html${NC}"
            open "${INDEX_HTML}" 2>/dev/null || echo "  (Use: open ${INDEX_HTML})"
        fi
    done
done

echo ""
echo -e "${BLUE}=============================================="
echo "📊 EXPERIMENT SUMMARY"
echo "=============================================="
echo -e "Results location: ${LOCAL_RESULTS_DIR}"
echo -e ""
echo -e "Next steps:"
echo -e "1. Review the opened HTML reports"
echo -e "2. Compare single vs multi-knob results for each scenario"
echo -e "3. Key metrics to examine:"
echo -e "   - ΔP95 latency improvement"
echo -e "   - ΔRecall@10 change"
echo -e "   - p-value (statistical significance)"
echo -e "   - safety_rate (should be ≥0.99)"
echo -e "   - apply_rate (should be ≥0.95)"
echo -e "   - buckets_used (more = better coverage)"
echo -e "=============================================="
echo -e "${GREEN}✅ WORKFLOW COMPLETE${NC}"
echo -e "==============================================\n"

# Print Chinese verdicts (placeholders - will be filled from actual results)
echo -e "${YELLOW}📋 快速判决 (待人工审查结果后填写):${NC}"
echo -e "场景B (High-Recall/High-Latency):"
echo -e "  Single(10m): [待查看] | Multi(45m): [待查看]"
echo -e "  对比: ΔP95=?ms, ΔRecall=?, p=?, safety=?, apply=?, buckets=?"
echo -e ""
echo -e "场景C (Low-Latency/Low-Recall):"
echo -e "  Single(10m): [待查看] | Multi(45m): [待查看]"
echo -e "  对比: ΔP95=?ms, ΔRecall=?, p=?, safety=?, apply=?, buckets=?"
echo ""
