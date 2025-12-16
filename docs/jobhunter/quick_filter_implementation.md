# Quick Profile Mismatch Filter Implementation

## Overview

The quick filter is a lightweight heuristic that detects obvious profile/JD mismatches (e.g., Financial Advisor JD for Data Engineer profile) and skips expensive LLM nodes to save costs and time.

## When Quick Filter Activates

The filter activates when:
- **Profile**: Data Engineer (GCP) or LLM/Agent Engineer
- **JD Type**: Sales/financial-advisory positions (Financial Advisor, Financial Specialist, etc.)
- **Threshold**: `non_tech_count >= 3` AND `tech_count <= 2`

### Detection Rules

For **Data Engineer profile**:
- **Tech keywords**: data engineer, etl, pipeline, warehouse, bigquery, snowflake, airflow, spark, dbt, sql, gcp, etc.
- **Non-tech keywords**: financial advisor, financial specialist, sales, prospect, clients, wealth management, commissions, insurance, portfolio, investment, trading, series 7, series 63, cfp, etc.
- **Rule**: `non_tech_count >= 3 AND data_count <= 2` → `skip_deep_analysis = True`

For **LLM/Agent Engineer profile**:
- **Tech keywords**: llm, large language model, langgraph, agent, agents, evaluation, rag, retrieval, etc.
- **Non-tech keywords**: Same as Data Engineer profile
- **Rule**: `non_tech_count >= 3 AND llm_count <= 2` → `skip_deep_analysis = True`

## What Gets Skipped

When `skip_deep_analysis = True`, the following heavy LLM nodes are short-circuited:
- `interpret_jd` - JD interpretation (saves ~10-15s)
- `lifecycle_reflection` - Lifecycle analysis (saves ~5-10s)
- `spotlight_story` - Spotlight story generation (saves ~8-12s)
- `core_signals` - Core signals extraction (saves ~6-10s)
- `evidence_align` - Evidence snippet attachment (saves ~1-2s)

**Nodes that still run**:
- `check_constraints` - Always runs (lightweight, < 1ms)
- `analyze_fit` - Always runs (returns low score 1/10 with SKIP recommendation)

## Output

When quick filter is active:
- **Match Score**: 1/10 (fixed)
- **Category**: C (Not a Good Fit)
- **Recommendation**: SKIP
- **Reasoning**: Built from `profile_mismatch_reasons` in constraints
- **JD Summary**: Minimal summary with SKIP recommendation and mismatch warning

## Implementation Details

### Files Modified

1. **`schemas.py`**:
   - Added `profile_mismatch_score`, `profile_mismatch_reasons`, `skip_deep_analysis` to `ConstraintCheckResult`
   - Added `skip_deep_analysis` to `JDAnalysisState`

2. **`jd_constraints.py`**:
   - Implemented `_estimate_profile_mismatch()` heuristic
   - Wired into `check_basic_constraints()` with profile_id support
   - Auto-detects profile_id from profile text if not provided

3. **`jd_analysis_graph.py`**:
   - All heavy LLM nodes check `state.skip_deep_analysis` and short-circuit
   - `node_interpret_jd` creates minimal jd_summary when skipped
   - `node_analyze_fit` returns low score (1/10) when `skip_deep_analysis=True`

4. **`routes/jobhunter.py`**:
   - Route handler sets `match_score=1` and `category="C"` for quick filter cases
   - Builds `reasoning_summary` from `constraints.profile_mismatch_reasons`

5. **CLI & UI**:
   - CLI shows quick filter warning in Markdown output
   - UI shows yellow Alert in both "JD Summary" and "Fit Analysis" tabs

## Testing

Test with Financial Advisor JD:
```bash
python -m experiments.jobhunter.jd_explainer_cli \
  --from-text-file tmp/jd_financial_advisor_test.txt \
  --use-default-profile
```

Expected behavior:
- All heavy LLM nodes skipped (< 1ms each)
- Only `check_constraints` and `analyze_fit` execute
- Match score: 1/10, Recommendation: SKIP
- Quick filter warning displayed

## Future Improvements

- Extend to more profile types (e.g., Frontend Engineer, DevOps Engineer)
- Fine-tune thresholds based on real-world data
- Add more sophisticated keyword matching (e.g., n-grams, semantic similarity)
