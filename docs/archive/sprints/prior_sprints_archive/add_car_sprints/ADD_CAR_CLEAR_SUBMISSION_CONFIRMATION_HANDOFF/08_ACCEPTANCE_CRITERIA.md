# Acceptance Criteria

## Must pass

- [ ] Add-Car `handoff_ready` closure card shows **received snapshot** (tags) when `collected_fields` and/or `quote_ready_status` present.
- [ ] Office **follow-up expectation** line visible for Add-Car closure (config-driven).
- [ ] `handoff_phrases.add_car` (zh/en) stresses **formal submission** without violating triage brevity.
- [ ] First screen submit button reads **提交加车请求** when `selectedButtonIntent === 'add_car'`.
- [ ] New `ui_copy` keys are **whitelisted** in `get_ui_copy` (not stripped).
- [ ] `bash scripts/guardrail_inbox_triage.sh` passes.
- [ ] `cd ui && npm run build` passes if UI changed.
- [ ] `PYTHONPATH=. python3 scripts/run_add_car_submission_confirmation_sprint_scenarios.py` passes.

## Product judgment (manual)

- [ ] Founder can answer audit Q1–Q6 more positively than baseline for Add-Car.
- [ ] Tone remains **operational**, not chatty.

## Explicit non-requirements

- New API fields, new persistence columns, new LLM paths.
