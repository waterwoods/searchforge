# LangSmith PR B — Tracing + Golden Dataset + Evaluators

**Branch:** `stage2/langsmith-tracing-golden-evals`  
**Prerequisite:** Guided Intake Founder PASS (`guided-intake-ux-v1-founder-pass`)  
**Environment:** QA / lab only — Production / waterwoods untouched

## Deliverables

1. Node-level LangSmith instrumentation (`accident_story.*` run names)
2. Strict redaction policy (this folder)
3. Golden dataset: 20 fixtures in `tests/fixtures/accident_story_langgraph/`
4. Offline evaluators in `accident_story_assistant/evaluators.py`
5. CI/local command:

```bash
PYTHONPATH=. python3 scripts/run_accident_story_langsmith_eval.py --dataset accident_story_v1
PYTHONPATH=. python3 -m pytest tests/test_accident_story_langgraph.py tests/test_accident_story_langsmith_eval.py -q
```

## Latest offline result

See `latest-eval-report.md` — target **20/20 PASS**.
