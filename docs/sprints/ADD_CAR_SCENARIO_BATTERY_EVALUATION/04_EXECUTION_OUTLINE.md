# Execution Outline — Add-Car Scenario Battery Evaluation Sprint

## Loop 1 — Design

1. Lock scenario types (clean / messy / edge) per blueprint.
2. Author `scenario_battery.json` with IDs, turns, and rationale fields.
3. Review for **realism** (would a broker recognize this as their inbox?).

## Loop 2 — Run

1. Ensure **`LLM_GENERATION_ENABLED=false`** for reproducible baseline (or document otherwise).
2. Run:

   `PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py --json`

3. Save output to `run_results_rule_path.json` (committed for this sprint).

## Loop 3 — Inspect

For each scenario:

- Read **final** `issue_category`, `handoff_ready`, `quote_ready_status`, `follow_up_type`.
- Read **every turn** `client_reply_draft` and `broker_next_step`.
- Compare to `expected_good_behavior` in JSON.

## Loop 4 — Classify

Apply `02_EVALUATION_CRITERIA_SPEC.md` labels: Strong / Acceptable / Weak / Trust-breaking.

## Loop 5 — Prioritize

Map top findings to `03_FIX_PRIORITY_SPEC.md` buckets (fix-now / fix-next / acceptable / defer).

## Loop 6 — Summarize

Produce `06_FINAL_REPORT.md` with broker readiness verdict + 中文宏观总结 + copy-paste founder block.

## Optional: regression hook

When changing `triage.py` for Add-Car:

- Re-run this battery before broker demos.
- If ACE* pack is also maintained, run `scripts/run_add_car_edge_case_simulations.py` as a secondary check.
