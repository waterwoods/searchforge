# Execution Outline

1. **Audit** — Scan `triage.py` draft and next-ask paths; list high-frequency residuals (see Audit Spec).
2. **Prioritize** — Select ≤4 families (see Priority Spec).
3. **Implement** — Add `_stitched_customer_visible_line`, `_maybe_append_add_car_price_caveat`; wire payment/premium tails; extend `reply_templates.json`; update `socal_precision` JSON.
4. **Unify paths** — Apply caveat helper in `_get_next_ask_for_add_car` so multi-turn flows match single-turn drafts.
5. **Scenario pack** — Author `residual_copy_ab_scenario_battery.json` + runner.
6. **Guardrail** — Add step `[12c]` to `scripts/guardrail_inbox_triage.sh`.
7. **Validate** — Run guardrail; run `run_add_car_scenario_battery.py`; spot-check `run_cross_client_ab_scenarios.py` (included in guardrail).
8. **Document** — Acceptance criteria, founder notes, final report (incl. 中文总结).
