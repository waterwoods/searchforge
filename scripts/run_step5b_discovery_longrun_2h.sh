#!/bin/bash
# Step 5B Long-Run Discovery: 2-hour discovery job with checkpointing
# Safe for long-running terminal sessions with crash-resume capability

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration from environment variables (with defaults)
DISCOVERY_RUNTIME_MIN="${DISCOVERY_RUNTIME_MIN:-120}"
DISCOVERY_PER_DOMAIN_DELAY_SEC="${DISCOVERY_PER_DOMAIN_DELAY_SEC:-2.0}"
DISCOVERY_GLOBAL_DELAY_SEC="${DISCOVERY_GLOBAL_DELAY_SEC:-0.2}"
DISCOVERY_MAX_CANDIDATES="${DISCOVERY_MAX_CANDIDATES:-500}"
DISCOVERY_VERIFY_TOP_K="${DISCOVERY_VERIFY_TOP_K:-25}"
DISCOVERY_VERIFY_PAGES_PER_DOMAIN="${DISCOVERY_VERIFY_PAGES_PER_DOMAIN:-3}"

# Create timestamped run directory
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
RUN_DIR="$REPO_DIR/results/auto_insurance_discovery/runs/$TIMESTAMP"
mkdir -p "$RUN_DIR"

# Log file
RUN_LOG="$RUN_DIR/RUN_LOG.txt"
CHECKPOINTS_FILE="$RUN_DIR/CHECKPOINTS.md"

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$RUN_LOG"
}

# Function to write checkpoint
write_checkpoint() {
    local checkpoint_time=$(date +'%Y-%m-%d %H:%M:%S')
    local elapsed_minutes=$(( ($(date +%s) - START_TIME) / 60 ))
    
    {
        echo ""
        echo "## Checkpoint: $checkpoint_time"
        echo ""
        echo "- Elapsed: ${elapsed_minutes} minutes"
        echo "- Candidates: $(python3 -c "import json; print(len(json.load(open('$RUN_DIR/candidates.json'))))" 2>/dev/null || echo "0")"
        echo "- Passing: $(python3 -c "import json; print(len(json.load(open('$RUN_DIR/passing.json'))))" 2>/dev/null || echo "0")"
        echo ""
    } >> "$CHECKPOINTS_FILE"
    
    log "Checkpoint written (${elapsed_minutes} min elapsed)"
}

# Trap signals for graceful shutdown
trap 'log "Interrupt received, finishing current operation..."; write_checkpoint; exit 130' INT TERM

# Initialize
START_TIME=$(date +%s)
log "=========================================="
log "Step 5B Long-Run Discovery"
log "=========================================="
log ""
log "Configuration:"
log "  Runtime: ${DISCOVERY_RUNTIME_MIN} minutes"
log "  Max candidates: ${DISCOVERY_MAX_CANDIDATES}"
log "  Per-domain delay: ${DISCOVERY_PER_DOMAIN_DELAY_SEC}s"
log "  Global delay: ${DISCOVERY_GLOBAL_DELAY_SEC}s"
log "  Verify top-K: ${DISCOVERY_VERIFY_TOP_K}"
log "  Verify pages/domain: ${DISCOVERY_VERIFY_PAGES_PER_DOMAIN}"
log ""
log "Run directory: $RUN_DIR"
log ""

# Initialize CHECKPOINTS.md
{
    echo "# Discovery Run Checkpoints"
    echo ""
    echo "Run started: $(date +'%Y-%m-%d %H:%M:%S')"
    echo "Runtime limit: ${DISCOVERY_RUNTIME_MIN} minutes"
    echo ""
} > "$CHECKPOINTS_FILE"

# Background process to write checkpoints every 10 minutes
(
    while true; do
        sleep 600  # 10 minutes
        if [ -f "$RUN_DIR/candidates.json" ]; then
            write_checkpoint
        fi
    done
) &
CHECKPOINT_PID=$!

# Step 1: Discovery
log "Step 1: Starting discovery..."
log "----------------------------------------"

python3 "$SCRIPT_DIR/discover_auto_insurance_sources.py" \
    --max-runtime-minutes "$DISCOVERY_RUNTIME_MIN" \
    --max-candidates "$DISCOVERY_MAX_CANDIDATES" \
    --per-domain-delay "$DISCOVERY_PER_DOMAIN_DELAY_SEC" \
    --global-delay "$DISCOVERY_GLOBAL_DELAY_SEC" \
    --checkpoint-every-sec 600 \
    --output-dir "$RUN_DIR" \
    2>&1 | tee -a "$RUN_LOG"

DISCOVERY_EXIT_CODE=${PIPESTATUS[0]}

# Stop checkpoint background process
kill $CHECKPOINT_PID 2>/dev/null || true

if [ $DISCOVERY_EXIT_CODE -ne 0 ]; then
    log "WARNING: Discovery exited with code $DISCOVERY_EXIT_CODE"
    log "Partial results may be available in $RUN_DIR"
fi

log ""
log "Step 1 complete (exit code: $DISCOVERY_EXIT_CODE)"
log ""

# Step 2: Filter to passing (if candidates.json exists)
if [ -f "$RUN_DIR/candidates.json" ]; then
    log "Step 2: Filtering to passing candidates..."
    log "----------------------------------------"
    
    python3 -c "
import json
from collections import defaultdict

with open('$RUN_DIR/candidates.json', 'r') as f:
    candidates = json.load(f)

passing = []
domain_counts = defaultdict(int)

for candidate in candidates:
    if candidate['blocked_by_robots']:
        continue
    if candidate['score'] < 15.0:
        continue
    
    domain = candidate['domain']
    if domain_counts[domain] >= 5:
        continue
    
    passing.append(candidate)
    domain_counts[domain] += 1

with open('$RUN_DIR/passing.json', 'w') as f:
    json.dump(passing, f, indent=2, ensure_ascii=False)

print(f'Filtered {len(passing)} passing candidates from {len(candidates)} total')
" 2>&1 | tee -a "$RUN_LOG"
    
    log "Step 2 complete"
    log ""
else
    log "WARNING: candidates.json not found, skipping filtering"
    log ""
fi

# Step 3: Generate report (if candidates.json exists)
if [ -f "$RUN_DIR/candidates.json" ] && [ -f "$RUN_DIR/passing.json" ]; then
    log "Step 3: Generating report..."
    log "----------------------------------------"
    
    python3 -c "
import json
from collections import defaultdict
from datetime import datetime

with open('$RUN_DIR/candidates.json', 'r') as f:
    candidates = json.load(f)

with open('$RUN_DIR/passing.json', 'r') as f:
    passing = json.load(f)

report = []
report.append('# Auto Insurance Source Discovery Report')
report.append('')
report.append(f'Generated: {datetime.now().isoformat()}')
report.append('')
report.append('## Summary')
report.append('')
report.append(f'- Total candidates discovered: {len(candidates)}')
report.append(f'- Passing candidates: {len(passing)}')
report.append('')

# Domain breakdown
domain_counts = defaultdict(int)
for c in candidates:
    domain_counts[c['domain']] += 1
report.append('## Candidates by Domain')
report.append('')
for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
    report.append(f'- {domain}: {count} candidates')
report.append('')

# Top candidates
report.append('## Top 10 Candidates')
report.append('')
for i, c in enumerate(candidates[:10], 1):
    report.append(f'{i}. **{c[\"title\"][:60]}**')
    report.append(f'   - URL: {c[\"url\"]}')
    report.append(f'   - Score: {c[\"score\"]}')
    report.append(f'   - Domain: {c[\"domain\"]}')
    report.append(f'   - Content: {c[\"content_length\"]} chars')
    report.append(f'   - Reasons: {\", \".join(c[\"reasons\"])}')
    report.append('')

# Passing candidates
report.append('## Passing Candidates')
report.append('')
for i, c in enumerate(passing, 1):
    report.append(f'{i}. **{c[\"title\"][:60]}**')
    report.append(f'   - URL: {c[\"url\"]}')
    report.append(f'   - Score: {c[\"score\"]}')
    report.append('')

with open('$RUN_DIR/REPORT.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print('Report generated')
" 2>&1 | tee -a "$RUN_LOG"
    
    log "Step 3 complete"
    log ""
fi

# Step 4: Verification (if passing.json exists)
if [ -f "$RUN_DIR/passing.json" ]; then
    log "Step 4: Verifying discovered sources..."
    log "----------------------------------------"
    
    python3 "$SCRIPT_DIR/verify_discovered_sources.py" \
        --input-passing-json "$RUN_DIR/passing.json" \
        --top-k "$DISCOVERY_VERIFY_TOP_K" \
        --pages-per-domain "$DISCOVERY_VERIFY_PAGES_PER_DOMAIN" \
        --output-dir "$RUN_DIR" \
        2>&1 | tee -a "$RUN_LOG"
    
    log "Step 4 complete"
    log ""
else
    log "WARNING: passing.json not found, skipping verification"
    log ""
fi

# Generate run summary
END_TIME=$(date +%s)
ELAPSED_SECONDS=$((END_TIME - START_TIME))
ELAPSED_MINUTES=$((ELAPSED_SECONDS / 60))

CANDIDATES_COUNT=0
PASSING_COUNT=0
VERIFY_COUNT=0

if [ -f "$RUN_DIR/candidates.json" ]; then
    CANDIDATES_COUNT=$(python3 -c "import json; print(len(json.load(open('$RUN_DIR/candidates.json'))))" 2>/dev/null || echo "0")
fi

if [ -f "$RUN_DIR/passing.json" ]; then
    PASSING_COUNT=$(python3 -c "import json; print(len(json.load(open('$RUN_DIR/passing.json'))))" 2>/dev/null || echo "0")
fi

if [ -f "$RUN_DIR/verify_corpus.jsonl" ]; then
    VERIFY_COUNT=$(wc -l < "$RUN_DIR/verify_corpus.jsonl" 2>/dev/null || echo "0")
fi

# Write run summary
python3 -c "
import json
from datetime import datetime

summary = {
    'run_id': '$TIMESTAMP',
    'started_at': '$(date -d @$START_TIME +%Y-%m-%dT%H:%M:%S)',
    'ended_at': '$(date -d @$END_TIME +%Y-%m-%dT%H:%M:%S)',
    'elapsed_seconds': $ELAPSED_SECONDS,
    'elapsed_minutes': $ELAPSED_MINUTES,
    'configuration': {
        'runtime_minutes': $DISCOVERY_RUNTIME_MIN,
        'max_candidates': $DISCOVERY_MAX_CANDIDATES,
        'per_domain_delay_sec': $DISCOVERY_PER_DOMAIN_DELAY_SEC,
        'global_delay_sec': $DISCOVERY_GLOBAL_DELAY_SEC,
        'verify_top_k': $DISCOVERY_VERIFY_TOP_K,
        'verify_pages_per_domain': $DISCOVERY_VERIFY_PAGES_PER_DOMAIN
    },
    'results': {
        'candidates_count': $CANDIDATES_COUNT,
        'passing_count': $PASSING_COUNT,
        'verify_documents_count': $VERIFY_COUNT
    },
    'exit_code': $DISCOVERY_EXIT_CODE
}

with open('$RUN_DIR/run_summary.json', 'w') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
" 2>/dev/null || true

# Final checkpoint
write_checkpoint

# Final summary
log ""
log "=========================================="
log "Long-Run Discovery Complete"
log "=========================================="
log ""
log "Run directory: $RUN_DIR"
log "Elapsed time: ${ELAPSED_MINUTES} minutes"
log ""
log "Results:"
log "  Candidates: $CANDIDATES_COUNT"
log "  Passing: $PASSING_COUNT"
log "  Verify documents: $VERIFY_COUNT"
log ""
log "Files created:"
ls -lh "$RUN_DIR"/*.{json,jsonl,md,txt} 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' | tee -a "$RUN_LOG"
log ""
log "=========================================="

exit $DISCOVERY_EXIT_CODE
