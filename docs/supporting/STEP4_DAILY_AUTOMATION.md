# Step 4: Daily Automation for Auto Insurance RAG

## Overview

This document describes the daily automation pipeline for crawling, embedding, and updating the auto insurance RAG system.

## Architecture

The daily automation consists of 4 main steps:

1. **Ingest/Crawl**: Fetch pages from configured URLs, extract text, chunk documents
2. **Diff Filter**: Remove unchanged documents (compare with yesterday's corpus)
3. **Embed and Upsert**: Generate embeddings and upsert to Qdrant collection `auto_insurance_v2_clean`
4. **Evaluation**: Run RAG evaluation and generate reports

## Files

### Scripts
- `scripts/run_auto_insurance_daily.sh` - Main runner script
- `scripts/daily_diff_filter.py` - Filters unchanged documents

### Configuration
- `results/auto_insurance/daily_targets.json` - Target URLs and settings

### Outputs
All outputs are stored in `results/auto_insurance/daily/YYYY-MM-DD/`:
- `corpus_raw.jsonl` - Raw crawled documents
- `corpus_filtered.jsonl` - Filtered documents (unchanged removed)
- `run.log` - Full execution log
- `EVAL_REPORT.md` - Evaluation results
- `DAILY_REPORT.md` - Daily summary report
- `FAILED.md` - Failure report (if any step fails)

## Manual Execution

### Prerequisites

1. **Environment Variables**:
   ```bash
   export QDRANT_URL="https://your-qdrant-url"
   export QDRANT_API_KEY="your-api-key"
   ```

   Or load from `.env.cloudrun`:
   ```bash
   source .env.cloudrun  # if it exists
   ```

2. **Python Dependencies**: Ensure all required packages are installed (see main project requirements)

3. **Config File**: Ensure `results/auto_insurance/daily_targets.json` exists with target URLs

### Run Manually

```bash
cd ~/searchforge
bash scripts/run_auto_insurance_daily.sh
```

The script will:
- Create a date-stamped directory under `results/auto_insurance/daily/`
- Run all pipeline steps sequentially
- Generate reports and logs
- Exit with appropriate codes:
  - `0` - Success
  - `10` - Ingest failed
  - `20` - Upsert failed
  - `30` - Evaluation failed

### Check Results

```bash
# View daily report
cat results/auto_insurance/daily/$(date +%Y-%m-%d)/DAILY_REPORT.md

# View evaluation results
cat results/auto_insurance/daily/$(date +%Y-%m-%d)/EVAL_REPORT.md

# View full log
tail -f results/auto_insurance/daily/$(date +%Y-%m-%d)/run.log
```

## Scheduling

### WSL (Linux Cron)

1. Edit crontab:
   ```bash
   crontab -e
   ```

2. Add daily job (runs at 2 AM):
   ```cron
   0 2 * * * cd /home/andy/searchforge && bash scripts/run_auto_insurance_daily.sh >> /home/andy/searchforge/results/auto_insurance/daily/cron.log 2>&1
   ```

3. Or run at a specific time (e.g., 3 AM):
   ```cron
   0 3 * * * cd /home/andy/searchforge && bash scripts/run_auto_insurance_daily.sh >> /home/andy/searchforge/results/auto_insurance/daily/cron.log 2>&1
   ```

### Windows Task Scheduler

1. Open Task Scheduler (search "Task Scheduler" in Windows)

2. Create Basic Task:
   - Name: "Auto Insurance Daily RAG Update"
   - Trigger: Daily at desired time
   - Action: Start a program
   - Program: `wsl`
   - Arguments: `bash -c "cd /home/andy/searchforge && bash scripts/run_auto_insurance_daily.sh"`

3. Or use PowerShell command:
   ```powershell
   wsl bash -c "cd /home/andy/searchforge && bash scripts/run_auto_insurance_daily.sh"
   ```

4. Set working directory (optional): `C:\Users\<username>\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu*\LocalState\rootfs\home\andy\searchforge`

## Configuration

### Target URLs

Edit `results/auto_insurance/daily_targets.json`:

```json
{
  "target_urls": [
    "https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/",
    "https://www.insurance.ca.gov/01-consumers/105-type/95-guides/auto/"
  ],
  "max_pages_per_source": 50,
  "allowed_domains": [
    "dmv.ca.gov",
    "insurance.ca.gov",
    "geico.com",
    "progressive.com"
  ]
}
```

### Limits

- `max_pages_per_source`: Maximum pages to crawl per source (default: 50 for MVP)
- `allowed_domains`: Domain allowlist (must match domains in target URLs)

## Monitoring and Logs

### Check Logs

```bash
# Today's log
cat results/auto_insurance/daily/$(date +%Y-%m-%d)/run.log

# Yesterday's log
cat results/auto_insurance/daily/$(date -d yesterday +%Y-%m-%d)/run.log

# Search for errors
grep -i error results/auto_insurance/daily/*/run.log
```

### Check Artifacts

```bash
# List all daily runs
ls -la results/auto_insurance/daily/

# Check specific date
ls -la results/auto_insurance/daily/2026-02-20/

# Count documents
wc -l results/auto_insurance/daily/2026-02-20/corpus_raw.jsonl
```

### Failure Handling

If a step fails, check:
1. `FAILED.md` in the daily directory for error details
2. `run.log` for full error trace
3. Environment variables (QDRANT_URL, QDRANT_API_KEY)
4. Network connectivity
5. Qdrant collection status

## Acceptance Criteria

The pipeline passes if:

1. ✅ Ingest produces `corpus_raw.jsonl` with > 0 documents
2. ✅ Diff filter produces `corpus_filtered.jsonl`
3. ✅ Upsert completes without errors (check logs)
4. ✅ Evaluation completes and generates `EVAL_REPORT.md`
5. ✅ `DAILY_REPORT.md` is generated with SUCCESS status

### Performance Targets (MVP)

- Total runtime: ≤ 15 minutes for MVP settings (50 pages max)
- Documents processed: 10-50 pages per run
- Filter rate: 0-50% (depending on content changes)

## Troubleshooting

### Ingest Fails

- Check network connectivity
- Verify target URLs are accessible
- Check robots.txt compliance
- Review `run.log` for specific errors

### Upsert Fails

- Verify QDRANT_URL and QDRANT_API_KEY are set
- Check Qdrant service status
- Verify collection `auto_insurance_v2_clean` exists
- Check embedding model availability

### Evaluation Fails

- Verify collection has documents
- Check embedding model matches upsert model
- Review evaluation logs for specific query failures

### Diff Filter Issues

- If yesterday's corpus doesn't exist, filter will pass through all documents (expected for first run)
- Check file permissions on daily directories

## Next Steps

1. **Production Alerts**: Implement webhook/email alerts in failure handler
2. **Monitoring Dashboard**: Create dashboard for daily run status
3. **Batch Size Tuning**: Optimize embedding batch size for performance
4. **Content Change Detection**: Enhance diff filter with more sophisticated change detection

## Related Documentation

- `pipelines/README_AUTO_INSURANCE.md` - Pipeline details
- `docs/archive/OPENCLAW_STEP2_SMOKETEST.md` - OpenClaw integration
- `docs/archive/OPENCLAW_MVP_SMOKETEST_RESULT.md` - Step 3 demo
