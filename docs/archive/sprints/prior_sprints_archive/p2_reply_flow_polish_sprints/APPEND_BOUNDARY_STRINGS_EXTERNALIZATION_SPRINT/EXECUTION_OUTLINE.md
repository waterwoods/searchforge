# Execution Outline

1. **Audit** — Enumerate customer-visible strings in `_apply_append_case_boundary`; confirm `ab_10` Client B leak path (`BOUNDARY_COPY_LEAK_AUDIT_SPEC.md`).
2. **Design** — Add `stitched.append_boundary` schema; defaults in code; no cross-client fallback (`EXTERNALIZATION_DESIGN_SPEC.md`).
3. **Implement** — `_APPEND_BOUNDARY_DEFAULTS`, `_merged_append_boundary_copy`, pass `client_id` into `_apply_append_case_boundary`; document in `config_loader.py`.
4. **Client B pack** — Fill `append_boundary` in `configs/clients/socal_precision/handoff_phrases.json`.
5. **Cross-client battery** — Update `ab_10` expectations (B: `本所`, must not `办公室` / `陈奎`).
6. **New A/B battery** — `append_boundary_ab_scenario_battery.json` + `run_append_boundary_ab_scenarios.py`.
7. **Guardrail** — Add `[12b]` to `scripts/guardrail_inbox_triage.sh`.
8. **Validate** — `run_append_boundary_ab_scenarios.py`, `run_cross_client_ab_scenarios.py`, `run_case_boundary_battery.py`, full `guardrail_inbox_triage.sh`.
9. **Document** — Blueprint, acceptance, founder notes, final report (this folder).

## Not in this sprint

UI build (no frontend change), OCR, carrier API, LangGraph replacement.
