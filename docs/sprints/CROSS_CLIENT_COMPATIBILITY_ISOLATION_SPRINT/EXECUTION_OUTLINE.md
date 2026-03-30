# Execution Outline

## Loop 1 — Audit

1. Read `triage.py` handoff assembly, `_get_prospective_send_materials_lead`, append boundary.
2. Read `config_loader.py` for client defaults and handoff fallback behavior.
3. Diff `chen_kui` vs `socal_precision` JSON packs.
4. Record leaks → `CLIENT_ISOLATION_AUDIT_SPEC.md`.

## Loop 2 — Test design

1. Author `cross_client_ab_scenario_battery.json` (12 scenarios).
2. Implement `scripts/run_cross_client_ab_scenarios.py` (explicit `client_id`, no LLM).

## Loop 3 — Low-risk externalization

1. Add `get_stitched_handoff_phrases()` — **no** Chen fallback for `stitched`.
2. Wire `triage.py`: materials-sent, why-still-chasing, prospective-send; pass `client_id` into `_get_next_ask_for_add_car` / `_get_prospective_send_materials_lead`.
3. Populate `stitched` for both clients (A mirrors old defaults; B uses 本所/事务所 tone).

## Loop 4 — Regression validation

1. `bash scripts/guardrail_inbox_triage.sh` (includes new step `[12]`).
2. Confirm `LLM_GENERATION_ENABLED=0` for A/B runner.

## Loop 5 — Summarize

1. `FINAL_REPORT.md` + founder notes.
2. Optional tables: comparison, leak checklist, externalize/keep.

## Time budget

Target 60–120 minutes wall clock for human review; automation ~minutes when guardrails green.
