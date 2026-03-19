# Prompt 4 Acceptance Checklist

## A) Data Quality Hardening

- [x] Binary file extension filtering (`.pdf`, `.xlsx`, etc.)
- [x] Content-Type validation (only `text/html`, `text/plain`, `application/xhtml+xml`)
- [x] Binary text detection (high ratio of non-printable chars)
- [x] Minimum text length check (>= 800 chars, configurable)
- [x] Language filtering (only `en`, `zh`, `es`)
- [x] Filtering counters (`dropped_binary_ext`, `dropped_content_type`, `dropped_too_short`, `dropped_lang`, `dropped_fetch_failed`)
- [x] Run summary JSON (`results/auto_insurance/ingest_run_summary.json`)
- [x] CLI flags: `--min-chars`, `--deny-ext`, `--strict-content-type`

## B) Data Expansion

- [x] Expanded `data_sources.json` with more topic URLs for ds_001, ds_002, ds_004, ds_005
- [x] Topics covered: coverage, liability limits, claims, SR-22, uninsured motorist, comprehensive/collision, discounts, policy changes, cancellation/nonrenewal, proof of insurance
- [x] Incremental crawling support (append mode, `--site` flag)
- [x] Run directory structure (`results/auto_insurance/runs/<timestamp>/`)
- [x] Only compliant sources (allowlist domains, respect robots.txt)

## C) Evaluation Suite

- [x] Evaluation script: `scripts/eval_auto_insurance_rag.py`
- [x] Loads environment from `.env.cloudrun`
- [x] Uses same embedding model as `embed_and_upsert.py`
- [x] 20+ evaluation queries (8 English, 8 Chinese, 4 Spanish, 4+ business)
- [x] Hit@5 calculation with relevance heuristics
- [x] Keyword-based relevance checking
- [x] Domain authority boost (dmv.ca.gov, insurance.ca.gov)
- [x] Per-query metrics: best_score, relevant_count_in_top5, top1_domain, latency_ms
- [x] Aggregate metrics: avg_hit@5, %queries_with_>=3_relevant, avg_latency, language breakdown
- [x] Reports: `EVAL_REPORT.md` (human-readable) and `EVAL_REPORT.json` (machine-readable)
- [x] Acceptance criteria check (>=70% queries with 3+ relevant, avg_hit@5 >= 0.6)
- [x] Worst queries identification with hints

## D) Automation

- [x] Automation script: `scripts/run_auto_insurance_refresh.sh`
- [x] Preflight env check (uses `check_qdrant_env.py`)
- [x] Incremental crawl with append mode
- [x] Embed and upsert to `auto_insurance_v2_clean`
- [x] Run evaluation
- [x] Exit non-zero if evaluation fails
- [x] Idempotent (safe to re-run)
- [x] Never prints secrets
- [x] Logs to `results/auto_insurance/runs/<timestamp>/`
- [x] Operator documentation: `docs/supporting/OPERATOR_PROMPT4.md`
- [x] OpenClaw handoff prompt included

## E) Backend Demo Readiness

- [x] Metrics endpoint: `GET /api/metrics/auto-insurance-eval`
- [x] Returns latest aggregate metrics from `EVAL_REPORT.json`
- [x] Safe defaults if file missing (never 404)
- [x] Includes message if operator action needed

## F) Documentation & Final Checks

- [x] Acceptance checklist (this file)
- [x] Completion summary: `docs/supporting/PROMPT4_COMPLETION_SUMMARY.md`
- [x] Scripts are executable
- [x] No hard-coded secrets (all via dotenv/environment)
- [x] Respects robots.txt
- [x] Strict allowlist domains

## Verification Steps

1. **Run full refresh**:
   ```bash
   ./scripts/run_auto_insurance_refresh.sh
   ```

2. **Check evaluation report**:
   ```bash
   cat results/auto_insurance/EVAL_REPORT.md
   ```

3. **Test metrics endpoint**:
   ```bash
   curl http://localhost:8000/api/metrics/auto-insurance-eval
   ```

4. **Verify collection**:
   - Check Qdrant Cloud dashboard
   - Collection: `auto_insurance_v2_clean`
   - Points should be >= JSONL line count

5. **Check data quality**:
   - Review `ingest_run_summary.json` for drop reasons
   - Verify no binary files in corpus
   - Check domain distribution

## Acceptance Criteria

- ✅ All deliverables implemented
- ✅ Evaluation passes (>=70% queries with 3+ relevant, avg_hit@5 >= 0.6)
- ✅ No binary files in corpus
- ✅ All documents from allowlist domains
- ✅ Automation script runs successfully
- ✅ Metrics endpoint returns data
