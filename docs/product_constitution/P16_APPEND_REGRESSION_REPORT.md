# P16 Append Integrity — Regression Report

**Date:** 2026-06-06  
**Sprint:** P16-APPEND-INTEGRITY-SPRINT — Phase 5

---

## AC acceptance cases

| Case | Check | Result |
|------|-------|--------|
| **AC03** | VIN-missing Honda Chinese — `service_type=add_car`, structured fields | ✅ PASS |
| **AC05** | Tesla insurance card — `service_type=add_car`, 8 collected slots | ✅ PASS |
| **AC07** | Teen driver Honda English — `service_type=add_car`, 5 collected slots | ✅ PASS |
| **AC05 append** | Name/phone append preserves vin, zip, delivery_date, driver | ✅ PASS |

### AC05 append detail

**Before append:**
- `collected_fields`: year, make_model, vin, zip, **delivery_date**, primary_driver, …
- `still_needed_fields`: name, phone, notice_image
- `office_broker_next_step`: 联系客户补齐姓名、电话、notice_image，然后出报价

**After append:**
- `collected_fields`: … **delivery_date**, primary_driver, **name, phone**
- `still_needed_fields`: notice_image
- `office_broker_next_step`: 联系客户补齐notice_image，然后出报价

---

## Flow regression matrix

| Flow | Test | Result |
|------|------|--------|
| **Continue Case** | Session + case binding via triage route (scenario pack) | ✅ 64/64 scenarios |
| **Start New Case** | Greenfield triage AC03/05/07 | ✅ PASS |
| **History Restore** | `get_case_for_read` + append uses persisted `collected_fields` in ctx | ✅ PASS (merge defense) |
| **Formal Submit** | `save_case` preserves collected/still | ✅ PASS |
| **Append** | `append_follow_up_message` additive merge | ✅ PASS (`test_append_field_integrity`) |
| **Pre/post submit copy** | `run_pre_post_submit_reply_regression.py` | ✅ PASS |

---

## Automated suites executed

| Suite | Command | Result |
|-------|---------|--------|
| Append integrity unit tests | `pytest tests/test_append_field_integrity.py` | 3/3 PASS |
| Persisted coherence | `pytest tests/test_add_car_persisted_coherence.py` | 8/8 PASS |
| Scenario pack | `run_inbox_triage_scenarios.py` | 64/64 PASS |
| Pre/post submit replies | `run_pre_post_submit_reply_regression.py` | ALL PASS |
| Append simulation battery | `run_p16_append_simulation_battery.py` | 22/22 PASS |

---

## Regressions introduced by this fix

**None observed** in executed suites.

---

*Phase 5 complete.*
