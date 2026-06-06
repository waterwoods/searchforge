# Execution Outline

## Workstreams

1. **Audit** — Read `triage.py` add-car extractors, next-ask, handoff replies, template ordering.
2. **Scenario design** — ACE pack grounded in sprint-required messy behaviors.
3. **Implement** — Smallest code changes with highest broker-facing ROI.
4. **Simulate** — ACE runner + full `run_multi_turn_simulations.py` + guardrail bundle.
5. **Review** — Broker-confidence checklist (doc 04) + founder inspection (doc 08).

## Multi-loop plan (executed)

| Loop | Activity |
|------|----------|
| 1 | Baseline audit; run existing add-car + mixed packs; note fragile spots (vehicle concrete, premium vs add-car). |
| 2 | Implement fix-now items; add ACE scenarios; tune `expected_handoff_after_turn`. |
| 3 | Re-run guardrail + stress + handoff timing; confirm 0 weak multi-turn. |
| 4 | **Skipped** — No additional fix justified without new evidence; stopping avoids scope creep. |

## Validation strategy

- `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `bash scripts/guardrail_inbox_triage.sh` (superset)
- Spot: `PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py` and `run_handoff_timing_simulations.py`

## Deployment strategy

- **Backend:** If production Unified Intake uses this repo’s `fiqa_api`, deploy the API revision that contains this sprint’s `triage.py` changes.
- **Frontend:** No changes this sprint — **no** UI redeploy required for these fixes.
- **This workspace session:** Production deploy not executed; validation was **local / guardrail**. Founder should redeploy backend when ready to expose changes to Chen Kui review environment.
