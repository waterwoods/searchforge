# Auto Insurance RAG - Operator Guide (Prompt 4)

## Overview

This guide explains how to operate the Auto Insurance RAG system after Prompt 4 implementation. The system includes automated data refresh, quality filtering, and evaluation capabilities.

**⚠️ Important for OpenClaw Automation**: Before enabling full automation, review the baseline evaluation report in `docs/supporting/PROMPT3_TRANSLATION_EVAL_BASELINE.md`. This establishes the current performance metrics (especially Chinese query hit rates) that should be used as a reference point for monitoring improvements or regressions.

## Quick Start

### Daily/Weekly Refresh

Run the automated refresh script:

```bash
./scripts/run_auto_insurance_refresh.sh
```

This script will:
1. ✅ Check environment variables
2. 🔍 Crawl data sources (incremental, append mode)
3. 🔢 Embed and upsert to Qdrant Cloud
4. 📊 Run evaluation suite
5. ❌ Exit with error code if evaluation fails

**Output locations:**
- Evaluation report: `results/auto_insurance/EVAL_REPORT.md`
- Upsert report: `results/auto_insurance/UPSERT_V2_CLEAN_REPORT.md`
- Run logs: `results/auto_insurance/runs/<timestamp>/`

### Manual Steps (if needed)

#### 1. Crawl Only

```bash
python3 pipelines/auto_insurance_ingest.py \
  --config-dir docs/prompt2_input \
  --output data/auto_insurance_corpus.jsonl \
  --max-pages-per-source 300 \
  --allow-domains dmv.ca.gov,insurance.ca.gov,geico.com,progressive.com \
  --min-chars 800 \
  --strict-content-type 1
```

#### 2. Embed and Upsert Only

```bash
python3 pipelines/embed_and_upsert.py \
  --input data/auto_insurance_corpus.jsonl \
  --collection auto_insurance_v2_clean \
  --batch-size 64
```

#### 3. Evaluate Only

```bash
python3 scripts/eval_auto_insurance_rag.py \
  --collection auto_insurance_v2_clean \
  --report-dir results/auto_insurance
```

## Interpreting Evaluation Report

### Key Metrics

1. **Average Hit@5**: Average number of relevant results in top 5 (target: >= 0.6)
2. **Queries with >=3 Relevant**: Percentage of queries with at least 3 relevant results (target: >= 70%)
3. **Average Latency**: Query response time in milliseconds

### Acceptance Criteria

✅ **PASS**: 
- avg_hit@5 >= 0.6
- >= 70% queries have 3+ relevant results

❌ **FAIL**: Either metric below threshold

### Language Breakdown

The report shows performance by language (English, Chinese, Spanish). Use this to identify if certain languages need more data.

### Worst Queries

If evaluation fails, check the "Worst Performing Queries" section. Common issues:
- **Keyword mismatch**: Query keywords don't match content keywords
- **Domain mismatch**: Results from wrong domains (not authoritative)
- **Low scores**: Vector similarity scores too low

## Troubleshooting

### Robots.txt Blocking

**Symptom**: Many URLs dropped with reason "dropped_robots_txt"

**Solution**: 
- Respect robots.txt (this is correct behavior)
- Remove blocked sources from `data_sources.json`
- Focus on sources that allow crawling (DMV, CDI, GEICO, Progressive)

### Content-Type Filtering Drops Too Much

**Symptom**: High count of "dropped_content_type"

**Solution**:
1. Check if sites are serving non-HTML content
2. Temporarily disable strict checking: `--strict-content-type 0`
3. Review dropped URLs in `ingest_run_summary.json`
4. Manually verify if dropped URLs are actually HTML

### Binary Files in Results

**Symptom**: Evaluation shows binary/corrupted text in results

**Solution**:
- Binary filtering is already enabled by default
- Check `--deny-ext` flag includes all binary extensions
- Review `dropped_binary_ext` count in summary
- If binary files still appear, increase `--min-chars` threshold

### Low Hit@5 Scores

**Symptom**: Evaluation fails with low hit@5

**Solutions**:
1. **Expand data**: Run crawl with higher `--max-pages-per-source`
2. **Check keywords**: Review relevance keyword sets in `eval_auto_insurance_rag.py`
3. **Domain authority**: Ensure authoritative domains (dmv.ca.gov, insurance.ca.gov) are prioritized
4. **Embedding model**: Verify using same model as training (check `embed_and_upsert.py`)

### Environment Variables Missing

**Symptom**: Script fails with "QDRANT_URL environment variable is required"

**Solution**:
1. Ensure `.env.cloudrun` exists in repo root
2. Run: `python3 scripts/check_qdrant_env.py` to verify
3. Check `.env.cloudrun` contains:
   ```
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your-api-key
   ```

## OpenClaw Handoff Prompt

**⚠️ IMPORTANT**: Before enabling OpenClaw automation, ensure Step 3 evaluation baseline has been established. See `docs/supporting/PROMPT3_TRANSLATION_EVAL_BASELINE.md` for baseline metrics and verification steps.

For AI agents (OpenClaw) to run this system:

```
You are tasked with maintaining the Auto Insurance RAG system.

To refresh the knowledge base:
1. Navigate to the repository root
2. Run: ./scripts/run_auto_insurance_refresh.sh
3. Wait for completion (may take 30-60 minutes)
4. Check exit code:
   - 0 = success
   - non-zero = failure (check logs in results/auto_insurance/runs/<timestamp>/)
5. Review evaluation report: results/auto_insurance/EVAL_REPORT.md
6. If evaluation FAILED:
   - Check "Worst Performing Queries" section
   - Identify keyword/domain mismatches
   - Report findings to operator

The script is idempotent (safe to re-run). It will:
- Append new documents (not overwrite)
- Deduplicate automatically
- Filter binary files and invalid content
- Respect robots.txt

Never print secrets (QDRANT_API_KEY). All sensitive values are masked in logs.
```

## Monitoring

### Check Collection Status

```bash
python3 -c "
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
load_dotenv(Path('.env.cloudrun'), override=True) if Path('.env.cloudrun').exists() else None
client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
info = client.get_collection('auto_insurance_v2_clean')
print(f'Points: {info.points_count}, Status: {info.status}')
"
```

### View Latest Evaluation Metrics

Check `results/auto_insurance/EVAL_REPORT.json` for programmatic access, or view the markdown report.

### API Endpoint

The backend provides a metrics endpoint:
```
GET /api/metrics/auto-insurance-eval
```

Returns latest evaluation metrics (if available) or safe defaults.

## Best Practices

1. **Run refresh during off-peak hours** (crawling is resource-intensive)
2. **Monitor evaluation trends** over time (track improvements/regressions)
3. **Review dropped URLs** periodically to identify new data sources
4. **Keep allowlist strict** (only official domains)
5. **Respect rate limits** (don't modify delay settings aggressively)

## File Structure

```
results/auto_insurance/
├── EVAL_REPORT.md              # Latest evaluation (human-readable)
├── EVAL_REPORT.json            # Latest evaluation (machine-readable)
├── UPSERT_V2_CLEAN_REPORT.md   # Latest upsert report
├── ingest_run_summary.json     # Latest crawl summary
└── runs/
    └── <timestamp>/
        ├── refresh.log          # Full refresh log
        ├── crawl.log            # Crawl step log
        ├── upsert.log           # Upsert step log
        └── eval.log             # Evaluation step log
```

## Support

For issues:
1. Check logs in `results/auto_insurance/runs/<latest>/`
2. Review evaluation report for specific query failures
3. Verify environment variables with `scripts/check_qdrant_env.py`
4. Check Qdrant Cloud dashboard for collection status
