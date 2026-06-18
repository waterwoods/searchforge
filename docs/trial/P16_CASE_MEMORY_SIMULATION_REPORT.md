# P16 Case Memory Persistence — Simulation Report

**Sprint:** P16-P2-CASE-MEMORY-PERSISTENCE-SPRINT  
**Date:** 2026-06-07  
**API (local):** `http://127.0.0.1:8001`  
**API (QA):** `https://fiqa-api-g7zatxrycq-uw.a.run.app`  
**Script:** `PYTHONPATH=. python3 scripts/run_p16_case_memory_simulation.py`

---

## Simulation A — Phone return after multi-turn (6265553001)

**Flow:**

1. `start-add-car` draft
2. Triage: `"I bought a BMW X5"` → `"2027"` → `"ZIP 92620"` (each with `case_id`)
3. `GET /api/inbox/cases/{id}` — verify messages
4. `GET /api/inbox/customer/active-case?phone=` — verify active case
5. Re-fetch case (simulate browser close / return)

**Result:** PASS

| Check | Outcome |
|-------|---------|
| Messages persisted | BMW X5, 2027, ZIP 92620 in `case_messages` |
| Active case exists | `case_id` matches |
| Reload timeline | All 3 customer messages present in order |

---

## Simulation B — Page refresh (6265553002)

**Flow:**

1. Draft + `"Tesla Model Y"`
2. Re-fetch case (simulate refresh)

**Result:** PASS — `"Tesla Model Y"` survives reload.

---

## Simulation C — New tab / phone return (6265553003)

**Flow:**

1. Draft + `"Honda Accord 2024"`
2. `active-case` lookup by phone
3. `GET /cases/{id}` from returned `case_id`

**Result:** PASS — conversation restored via case read, not session.

---

## Simulation D — Multiple supplements, timeline order (6265553004)

**Messages:**

1. `First: Lexus RX 350`
2. `Second: model year 2025`
3. `Third: ZIP 90210`
4. `Fourth: delivery next Monday, I am the primary driver`

**Result:** PASS — all four customer messages in monotonic sequence order.

**Note:** A VIN-only fourth message (`Fourth: VIN 1HGBH41JXMN109186`) correctly triggered `append_allowed=false` (vehicle-scope boundary) and was **not** persisted — expected boundary behavior, not a regression.

---

## Summary

| Sim | Phone | Scenario | Result |
|-----|-------|----------|--------|
| A | 6265553001 | Close browser / phone return | PASS |
| B | 6265553002 | Page refresh | PASS |
| C | 6265553003 | New tab / active-case return | PASS |
| D | 6265553004 | Multi-supplement timeline order | PASS |

**All simulations PASS** against local API and Cloud Run QA API (post `deploy_paid_pilot.sh`).

---

## Unit tests

```
tests/test_collecting_case_memory_persistence.py ..  [100%]  2 passed
```

- `test_collecting_triage_with_case_id_appends_case_messages`
- `test_collecting_triage_skips_append_when_append_blocked`
