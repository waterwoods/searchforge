# Step 5B Long-Run Discovery: 2-Hour Discovery Job

## Overview

The long-run discovery job is designed to run safely for extended periods (2+ hours) in a normal terminal session, with checkpointing and crash-resume safety. It discovers a large number of candidate URLs (up to 500) and verifies the top candidates.

## Quick Start

### Run the 2-Hour Job

```bash
cd ~/searchforge
bash scripts/run_step5b_discovery_longrun_2h.sh
```

The script will:
1. Create a timestamped run directory
2. Run discovery for up to 2 hours (configurable)
3. Write checkpoints every 10 minutes
4. Filter to passing candidates
5. Generate reports
6. Verify top candidates

### Configuration

Set environment variables before running:

```bash
export DISCOVERY_RUNTIME_MIN=120          # Runtime in minutes (default: 120)
export DISCOVERY_PER_DOMAIN_DELAY_SEC=2.0 # Delay between seed domains (default: 2.0)
export DISCOVERY_GLOBAL_DELAY_SEC=0.2     # Delay between candidates (default: 0.2)
export DISCOVERY_MAX_CANDIDATES=500       # Max candidates to process (default: 500)
export DISCOVERY_VERIFY_TOP_K=25          # Top K to verify (default: 25)
export DISCOVERY_VERIFY_PAGES_PER_DOMAIN=3 # Pages per domain (default: 3)

bash scripts/run_step5b_discovery_longrun_2h.sh
```

## Run Directory Structure

Each run creates a timestamped directory:

```
results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/
  ├── RUN_LOG.txt              # Full execution log
  ├── CHECKPOINTS.md            # Checkpoint history (appended every 10 min)
  ├── candidates.json           # All discovered candidates
  ├── passing.json             # Filtered passing candidates
  ├── REPORT.md                 # Human-readable report
  ├── verify_corpus.jsonl       # Verification crawl results
  ├── VERIFY_REPORT.md          # Verification report
  ├── run_summary.json          # Run metadata and summary
  └── checkpoint.json           # Latest checkpoint metadata
```

## Safe Operation

### Stopping Safely

**Press Ctrl+C** to stop the job gracefully:
- The script will finish the current operation
- Write a final checkpoint
- Save all partial results
- Exit cleanly

**Do NOT** kill the process with `kill -9` unless absolutely necessary, as this may lose recent progress.

### Inspecting Progress While Running

While the job is running, you can inspect progress:

```bash
# View latest log entries
tail -f results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/RUN_LOG.txt

# Check checkpoint history
cat results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/CHECKPOINTS.md

# Count current candidates
python3 -c "import json; print(len(json.load(open('results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/candidates.json'))))"

# View latest checkpoint
cat results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/checkpoint.json
```

### Resuming After Crash

The long-run job does **not** automatically resume from checkpoints. Instead:

1. **Check the last run directory**:
   ```bash
   ls -lt results/auto_insurance_discovery/runs/ | head -5
   ```

2. **Review partial results**:
   ```bash
   # Check what was discovered
   cat results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/run_summary.json
   ```

3. **Start a new run** (recommended):
   - Simply run the script again
   - It will create a new timestamped directory
   - Previous run's results are preserved

4. **Or continue manually** (advanced):
   - Use the checkpoint data to determine where to resume
   - Run discovery with appropriate `--max-candidates` to skip already-processed URLs
   - Note: This requires manual intervention and is not recommended

## Checkpointing

### Automatic Checkpoints

- **Every 10 minutes**: A checkpoint is written to `CHECKPOINTS.md`
- **On Ctrl+C**: Final checkpoint is written before exit
- **During discovery**: Partial `candidates.json` is written every 10 minutes

### Checkpoint Contents

Each checkpoint includes:
- Timestamp
- Elapsed time
- Current candidate count
- Current passing count

### Checkpoint Files

- `CHECKPOINTS.md`: Human-readable checkpoint history
- `checkpoint.json`: Latest checkpoint metadata (JSON format)
- `candidates.json`: Partial results (updated every 10 minutes)

## Monitoring

### Real-Time Monitoring

```bash
# Watch the log
tail -f results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/RUN_LOG.txt

# Monitor checkpoint updates
watch -n 30 'tail -20 results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/CHECKPOINTS.md'
```

### Progress Indicators

The log shows:
- Seed discovery progress
- Candidate processing progress (every 5 candidates)
- Checkpoint notifications
- Final summary

## Expected Runtime

- **2-hour run**: ~500 candidates processed
- **Processing rate**: ~4-5 candidates per minute (with delays)
- **Verification**: ~25 pages, ~2-3 minutes

## Output Files

### candidates.json
All discovered candidates with scores, reasons, and metadata.

### passing.json
Filtered candidates (score >= 15.0, max 5 per domain).

### REPORT.md
Human-readable summary with:
- Total candidates discovered
- Passing candidates
- Top 10 candidates
- Domain breakdown

### verify_corpus.jsonl
JSONL file with verified documents (one per line).

### VERIFY_REPORT.md
Verification report with:
- Pages fetched
- Documents kept
- Domain breakdown
- Document details

### run_summary.json
Run metadata:
```json
{
  "run_id": "2026-02-20_143000",
  "started_at": "2026-02-20T14:30:00",
  "ended_at": "2026-02-20T16:30:00",
  "elapsed_seconds": 7200,
  "elapsed_minutes": 120,
  "configuration": { ... },
  "results": {
    "candidates_count": 487,
    "passing_count": 42,
    "verify_documents_count": 25
  },
  "exit_code": 0
}
```

## Troubleshooting

### Job Stops Early

**Possible causes:**
- Network timeout
- Max runtime reached
- Ctrl+C pressed

**Check:**
```bash
# View exit code
cat results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/run_summary.json | grep exit_code

# Check log for errors
grep -i error results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/RUN_LOG.txt
```

### Low Candidate Count

**Possible causes:**
- Seed pages changed
- Robots.txt blocking
- Network issues

**Solutions:**
- Review `RUN_LOG.txt` for warnings
- Check `candidates.json` for robots.txt blocks
- Increase `DISCOVERY_MAX_CANDIDATES` if needed

### Checkpoints Not Writing

**Possible causes:**
- Disk full
- Permission issues
- Script crash

**Check:**
```bash
# Verify directory exists and is writable
ls -ld results/auto_insurance_discovery/runs/YYYY-MM-DD_HHMMSS/

# Check disk space
df -h results/auto_insurance_discovery/
```

## Best Practices

1. **Run in screen/tmux**: Use `screen` or `tmux` for long runs
   ```bash
   screen -S discovery
   bash scripts/run_step5b_discovery_longrun_2h.sh
   # Detach: Ctrl+A, D
   # Reattach: screen -r discovery
   ```

2. **Monitor disk space**: Ensure sufficient disk space (500MB+ recommended)

3. **Check network**: Ensure stable network connection

4. **Review results**: Always review `run_summary.json` and `REPORT.md` after completion

5. **Archive old runs**: Periodically archive old run directories to save space

## Manual Execution

The long-run job is designed to be run **manually in a WSL terminal**, not inside Cursor:

1. Open a WSL terminal
2. Navigate to the repo: `cd ~/searchforge`
3. Set environment variables (optional)
4. Run: `bash scripts/run_step5b_discovery_longrun_2h.sh`
5. Monitor progress (optional)
6. Wait for completion or stop with Ctrl+C

## Example Run

```bash
# Set configuration
export DISCOVERY_RUNTIME_MIN=120
export DISCOVERY_MAX_CANDIDATES=500

# Run in screen
screen -S discovery_2h
cd ~/searchforge
bash scripts/run_step5b_discovery_longrun_2h.sh

# Detach (Ctrl+A, D)
# Reattach later: screen -r discovery_2h

# After completion, check results
cat results/auto_insurance_discovery/runs/2026-02-20_143000/run_summary.json
```

## Next Steps

After a successful long-run:
1. Review `REPORT.md` for top candidates
2. Check `passing.json` for quality
3. Review `VERIFY_REPORT.md` for verification results
4. (Optional) Append safe candidates to `data_sources.json`
5. Archive the run directory if needed
