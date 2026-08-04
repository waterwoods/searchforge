# LangSmith unsafe-trace cleanup (redacted)

See `CLEANUP_REPORT.json`.

## Automated

- `delete_run` is **not** available on the installed LangSmith client.
- `update_run` redaction was attempted; many historical runs returned `LangSmithConflictError`.
- **Post-fix marker check:** current `accident_story.*` runs do **not** leak raw story markers.

## Exact manual cleanup action

1. Open the configured LangSmith project (credentials local / approved QA only — never commit keys).
2. Filter runs named: `normalize_story`, `extract_fact_proposals`, `validate_proposals`,
   `derive_missing_facts`, `draft_followup_questions`, `apply_safety_guardrails`,
   `build_customer_confirmation_proposal`, `LangGraph`.
3. Approximate window: traces created before pilot-safety commit `2ef3065` / tag `accident-story-pilot-safety-v1`.
4. Delete those runs or move them into a dedicated quarantine project.
5. Keep redacted `accident_story.*` runs.

## Why new runs are safe

- Node/root `@maybe_traceable` uses `process_inputs` / `process_outputs` redaction.
- LangGraph `app.invoke` is wrapped in `tracing_context(enabled=False)` to block full-state auto-traces.
- Kill switch: `ACCIDENT_STORY_LANGSMITH_TRACING=0`.
