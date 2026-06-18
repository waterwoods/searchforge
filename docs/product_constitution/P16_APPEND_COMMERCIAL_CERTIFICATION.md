# P16 Append Integrity — Commercial Certification

**Date:** 2026-06-06  
**Sprint:** P16-APPEND-INTEGRITY-SPRINT — Phase 6  
**Broker persona:** Chen Kui — 10 real add-car cases with return-later name/phone append

---

## Question

> If Chen Kui runs 10 real add-car cases, can any known append path lose information?

## Answer

**NO**

---

## Rationale

1. **Store-level additive merge** — `append_follow_up_message()` now unions prior `collected_fields` with fresh triage extraction. Previously captured slots (VIN, ZIP, delivery_date, driver) cannot be erased unless the customer explicitly corrects them (`add_car_merge.invalidated_slots`).

2. **still_needed guard** — Fields already in persisted `collected_fields` cannot be reintroduced to `still_needed_fields` after append.

3. **Office step coherence** — When merged `still_needed` differs from triage output (regression scenario), `office_broker_next_step` is recomputed from merged truth so brokers are not told to re-ask for delivery_date.

4. **22-scenario simulation battery** — All categories A–J pass, including deliberate triage-regression simulation.

5. **AC03/AC05/AC07** — Unchanged triage acceptance; AC05 append path verified end-to-end.

---

## Remaining blockers

None for append field integrity on the exercised paths.

**Non-append caveats (out of sprint scope, unchanged):**

- Customer append UI still requires `lastCaseId` in React state (lost on browser refresh without My Requests wiring).
- Relative delivery dates without calendar resolution remain in `still_needed` at *first* submit if never collected — append does not invent calendar dates.

---

## Confidence level

**High (95%)** for the commercial scenario: formal submit → return later → append name/phone → office record retains VIN, ZIP, delivery_date, driver.

Residual 5%: untested DB-primary-only production cutover edge cases without JSON fallback; merge runs at case_store regardless of read path.

---

*Phase 6 complete.*
