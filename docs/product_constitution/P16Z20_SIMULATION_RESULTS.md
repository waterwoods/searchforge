# P16-Z20 Phase 2 — Customer Builder Simulation Results

**Date:** 2026-06-03  
**Sprint:** P16-Z20 Add-Car Commercial Simulation  
**Method:** `triage_conversation()` via `scripts/run_p16z20_add_car_simulation.py`  
**Settings:** `LLM_GENERATION_ENABLED=0`, `client_id=chen_kui` (deterministic rules path)  
**Raw JSON:** `docs/product_constitution/.p16z20_results/simulation_results.json`

---

## Pipeline exercised

```
Customer Message (WeChat turns)
       ↓
Customer Builder (triage_conversation — same path as CustomerEntryTab)
       ↓
Draft Case (service_type, collected_fields, still_needed_fields, broker_next_step)
```

No new services. No API server required — direct import of existing triage engine.

---

## Aggregate scores

| Metric | Value |
|--------|-------|
| Scenarios run | 20 |
| Routed to `add_car` | 19 / 20 (95%) |
| Average case quality | **81.6 / 100** |
| `handoff_ready` on final turn | 15 / 20 |
| `action_ready` on final turn | 15 / 20 |

---

## Per-scenario results

| ID | service_type | Quality | collected_fields (sample) | still_needed_fields | broker_next_step (truncated) |
|----|--------------|---------|---------------------------|---------------------|------------------------------|
| AC01 | add_car | 89 | year, make_model, vin, zip, primary_driver… | delivery_date | Confirm missing driver/ZIP/VIN; quote same day |
| AC02 | add_car | 89 | year, make_model, vin, zip, primary_driver… | delivery_date | Confirm missing driver/ZIP/VIN; quote same day |
| AC03 | add_car | 81 | year, make_model, zip, primary_driver… | vin, delivery_date | Confirm missing driver/ZIP/VIN; quote same day |
| AC04 | add_car | 81 | year, make_model, vin, zip | delivery_date, primary_driver, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC05 | add_car | **92** | year, make_model, vin, zip, delivery_date, primary_driver… | name, phone | **Run quote for 2024 Tesla Model Y** |
| AC06 | add_car | 82 | year, make_model, vin, zip | delivery_date, primary_driver, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC07 | add_car | **92** | year, make_model, vin, zip, primary_driver | delivery_date, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC08 | add_car | 87 | year, make_model, vin, zip, primary_driver | delivery_date, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC09 | add_car | **92** | year, make_model, vin, zip, delivery_date, primary_driver… | name, phone | **Run quote for 2023 Toyota Highlander** |
| AC10 | add_car | 89 | year, make_model, vin, zip, primary_driver, name… | delivery_date | Confirm missing driver/ZIP/VIN; quote same day |
| AC11 | add_car | 73 | insurance_status_add_to_existing | all structural slots | Confirm missing driver/ZIP/VIN; quote same day |
| AC12 | add_car | 73 | insurance_status_new_customer | all structural slots | Confirm missing driver/ZIP/VIN; quote same day |
| AC13 | add_car | 89 | year, make_model, vin, zip, primary_driver… | delivery_date, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC14 | add_car | 87 | year, make_model, vin, zip, primary_driver, policy_number | delivery_date, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC15 | add_car | 65 | year, make_model, vin, zip, primary_driver… | delivery_date, name, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC16 | add_car | 82 | year, make_model, vin, zip, customer_says_materials_sent… | delivery_date, primary_driver, name, phone | Verify resubmitted items received |
| AC17 | add_car | 81 | year, make_model, zip, primary_driver, name | vin, delivery_date | Confirm missing driver/ZIP/VIN; quote same day |
| AC18 | add_car | 87 | year, make_model, vin, zip, primary_driver… | delivery_date | Confirm missing driver/ZIP/VIN; quote same day |
| AC19 | add_car | 86 | make_model, vin, zip, primary_driver, name | year, delivery_date, phone | Confirm missing driver/ZIP/VIN; quote same day |
| AC20 | **remove_car** | **35** | vehicle, year, make_model, sale_date | transfer_proof | Verify resubmitted items (wrong lane) |

---

## Case quality rubric (0–100)

| Component | Weight | What it measures |
|-----------|--------|------------------|
| Route correctness | 20 | `service_type == add_car` |
| Collected coverage | 30 | Expected slots present vs scenario intent |
| Still-needed accuracy | 20 | Missing VIN/driver/etc. correctly flagged |
| Broker next step | 15 | Actionable, non-generic |
| Vehicle summary + readiness | 15 | `primary_vehicle_summary`, handoff/action_ready |

---

## Notable patterns

**Strengths**

- VIN extraction reliable when provided (17/19 add_car cases collect VIN when in text)
- Multi-turn merge works (AC13 resolves VIN on turn 3; AC05 materials + VIN on turn 3)
- Mixed CN/EN handled (AC09 score 92)
- Teen driver captured (AC07 score 92 after turn 2)
- Insurance-card / materials-sent signals captured (`customer_says_materials_sent`)

**Weaknesses**

- **AC20 boundary failure:** Turn 4 "旧车能不能拿掉" flips lane to `remove_car` — known mixed-intent bug (Role D ADD_CAR_B)
- **AC11/AC12 minimal openers:** Route correct but zero vehicle extraction on single-word intake
- **AC07 turn 1:** First English line alone routes `unclear` — needs second turn
- **delivery_date** often in `still_needed` even when customer said "下周五" / "next week" — date normalization gap
- **broker_next_step** mostly generic English unless `action_ready` triggers vehicle-specific quote line

---

## Verdict (Phase 2)

Customer Builder produces **usable draft cases on 19/20 Add-Car intents** with average quality **81.6**. One high-risk mixed-intent scenario (AC20) fails commercially — same class as existing Role D B-scenario known gap.
