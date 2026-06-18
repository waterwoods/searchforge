# P16 Append Integrity — Reproduction

**Date:** 2026-06-06  
**Sprint:** P16-APPEND-INTEGRITY-SPRINT — Phase 1  
**Scenario:** AC05 audit path (English turns, formal submit, append name/phone)

---

## Conversation script

| Turn | Customer message |
|------|------------------|
| 1 | I bought a 2024 Tesla Model Y and want to add it to my policy. |
| 2 | I already sent the insurance card photo by WeChat. |
| 3 | VIN 7SAYGDEE5PA123456 / ZIP 90024 / Delivery date next Wednesday / I am the primary driver |
| — | **Formal submit** |
| Append | Name: Li Hua / Phone: 949-555-1234 |

---

## Before append (formal submit — saved case)

```json
{
  "collected_fields": [
    "year", "make_model", "vin", "zip", "delivery_date", "primary_driver",
    "insurance_status_new_customer", "customer_says_materials_sent"
  ],
  "still_needed_fields": ["name", "phone", "notice_image"],
  "office_broker_next_step": "联系客户补齐姓名、电话、notice_image，然后出报价"
}
```

---

## After append — **PRE-FIX regression** (demonstrated)

Reproduction method: run `append_follow_up_message()` with triage output that drops `delivery_date` (occurs when `reply_truth_context` lacks `persisted_collected_fields`, or triage re-extract fails relative delivery on re-scan).

```json
{
  "collected_fields": [
    "year", "make_model", "vin", "zip", "primary_driver",
    "insurance_status_new_customer", "customer_says_materials_sent", "phone"
  ],
  "still_needed_fields": ["notice_image", "delivery_date"],
  "office_broker_next_step": "联系客户补齐提车日期、姓名、电话，然后出报价"
}
```

### Exact regression

| Field | Before | After (bug) | Expected |
|-------|--------|-------------|----------|
| `delivery_date` in `collected_fields` | ✅ present | ❌ **missing** | ✅ present |
| `delivery_date` in `still_needed_fields` | ❌ absent | ❌ **reintroduced** | ❌ absent |
| `vin` | ✅ | ✅ | ✅ |
| `zip` | ✅ | ✅ | ✅ |
| `primary_driver` | ✅ | ✅ | ✅ |
| `name` | still_needed | missing from collected | collected |
| `phone` | still_needed | collected | collected |
| `office_broker_next_step` | 补齐姓名、电话 | **regressed** — asks 提车日期 again | 补齐 notice_image only |

---

## Triage-only trigger (no store)

`reply_truth_context` with `formal_submitted_at` but **without** `persisted_collected_fields`:

```
collected_fields: [year, make_model, vin, zip, primary_driver, ..., phone]
still_needed_fields: [delivery_date, notice_image]
```

Relative `next Wednesday` fails strict truth re-acceptance on append turn; reconcile has nothing to merge.

---

## After append — **POST-FIX** (same scenario)

```json
{
  "collected_fields": [
    "year", "make_model", "vin", "zip", "delivery_date", "primary_driver",
    "insurance_status_new_customer", "customer_says_materials_sent", "name", "phone"
  ],
  "still_needed_fields": ["notice_image"],
  "office_broker_next_step": "联系客户补齐notice_image，然后出报价"
}
```

---

## Reproduction commands

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 -m pytest tests/test_append_field_integrity.py -q
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16_append_simulation_battery.py
```

---

*Phase 1 complete.*
