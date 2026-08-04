# LangSmith Golden Evals V1 — Closeout

**Tag:** `langsmith-golden-evals-v1`  
**Commit:** `3f11b89`  
**Branch:** `stage2/langsmith-tracing-golden-evals`  
**Date:** 2026-08-04

## What 20/20 means

Offline **golden-suite correctness** against `tests/fixtures/accident_story_langgraph/` (20 fixtures):

- extracted / missing fact expectations
- max ≤3 questions
- unknown injury not coerced to no
- conflict + fallback contracts
- redacted `_trace_metadata` allow-list

## What 20/20 does **not** mean

- Not proof of real-pilot model accuracy on live CA claims
- Not Production readiness
- Online LangSmith UI validation remains **optional** unless credentials/project are configured

## Evidence

- `docs/evidence/langsmith-pr-b/latest-eval-report.md`
- `docs/evidence/langsmith-pr-b/REDACTION_POLICY.md`
- Command: `PYTHONPATH=. python3 scripts/run_accident_story_langsmith_eval.py --dataset accident_story_v1`

## Safety

Production / waterwoods untouched. Next: Pilot Safety PR C on `stage2/pilot-safety-observability`.
