# Add-Car Edge-Case Hardening + Broker Confidence Sprint — Index

**Sprint folder:** `docs/sprints/ADD_CAR_EDGE_CASE_BROKER_CONFIDENCE_SPRINT/`  
**Theme:** Harden flagship Add-Car against messy real customer behavior before Chen Kui–style broker review.

| # | Document | Purpose |
|---|----------|---------|
| 01 | [01_ADD_CAR_EDGE_CASE_HARDENING_BLUEPRINT.md](./01_ADD_CAR_EDGE_CASE_HARDENING_BLUEPRINT.md) | Why now, scope, non-goals |
| 02 | [02_ADD_CAR_MESSY_CUSTOMER_BEHAVIOR_SPEC.md](./02_ADD_CAR_MESSY_CUSTOMER_BEHAVIOR_SPEC.md) | Realistic messy patterns |
| 03 | [03_ADD_CAR_EDGE_CASE_SCENARIO_PACK.md](./03_ADD_CAR_EDGE_CASE_SCENARIO_PACK.md) | ACE01–ACE12 + expectations |
| 04 | [04_ADD_CAR_BROKER_CONFIDENCE_CRITERIA_SPEC.md](./04_ADD_CAR_BROKER_CONFIDENCE_CRITERIA_SPEC.md) | What “trustworthy” means |
| 05 | [05_ADD_CAR_FIX_NOW_FIX_NEXT_ACCEPTABLE_DEFER_SPEC.md](./05_ADD_CAR_FIX_NOW_FIX_NEXT_ACCEPTABLE_DEFER_SPEC.md) | Prioritized issue buckets |
| 06 | [06_EXECUTION_OUTLINE.md](./06_EXECUTION_OUTLINE.md) | Loops, validation, deploy notes |
| 07 | [07_ACCEPTANCE_CRITERIA.md](./07_ACCEPTANCE_CRITERIA.md) | Sprint done-ness |
| 08 | [08_FOUNDER_INSPECTION_NOTES.md](./08_FOUNDER_INSPECTION_NOTES.md) | What Andy should click-test |
| 09 | [09_FINAL_REPORT.md](./09_FINAL_REPORT.md) | Consolidated outcomes |

**Code / config touched**

- `services/fiqa_api/inbox_triage/triage.py` — vehicle summary bugfix, add-car vs premium priority, price-sensitivity line on add-car path, correction markers.
- `configs/customer_entry_multi_turn_simulations.json` — ACE01–ACE12 scenarios.
- `scripts/run_add_car_edge_case_simulations.py` — focused runner for ACE* sims.

**Validation run (local):** `bash scripts/guardrail_inbox_triage.sh` — PASS (includes multi-turn, stress, handoff).
