# P16-Z10A Phase 1 — Collected Merge Audit

**Date:** 2026-06-02  
**Sprint:** P16-Z10A Memory Core Hardening  
**SSOT:** P16-Z6 through P16-Z9, `triage.py` L6410–6520, Role D battery  
**Focus journeys:** D03, D10, D02

---

## Executive summary

Append merge was **add-car only**. All other lanes re-extracted from merged text and **cleared on the else branch**, losing persisted office truth. D03/D10/D02 failed because classification drifted lane, extractors missed zip/installment/confirmation tokens, and `persisted_collected_fields` was never passed in the battery (fixed in Z10A).

---

## TOP 20 findings

| # | Finding | Severity | Evidence |
|---|---------|----------|----------|
| 1 | Else branch wipes all collected on lane mismatch | **Critical** | `triage.py` L6489–6491 (pre-fix) |
| 2 | `persisted_collected_fields` only consumed on add-car | **Critical** | `_reconcile_add_car_lists_with_persisted_record` only |
| 3 | Battery append sim omitted `reply_truth_context` | **High** | `run_role_d_memory_battery.py` — no persisted pass-through |
| 4 | D03 zip `94588` not in structured output | **High** | `\b` regex failed on CJK-adjacent ZIP |
| 5 | D03 classified as `underwriting_followup` not `missing_document` | **High** | `核保` beat garaging markers |
| 6 | D10 stayed `unclear` all 3 days | **Critical** | Chinese 分期/恢复 not in payment classifiers |
| 7 | D10 `$200` dropped on append | **High** | No `payment_amount` extractor |
| 8 | D02 Day 3 → `underwriting_followup` | **High** | "underwriting" in status ping beat payment lane |
| 9 | D02 `#88291` not in collected | **Medium** | Confirmation # not separate from policy_number |
| 10 | D02 boundary `new_issue` on billing ping | **High** | `prior=generic` — lapse not inferred as payment domain |
| 11 | D01 weak cancel + question → `customer_question` | **Medium** | 7-day notice lost cancellation headline |
| 12 | Premium lane guard existed; remove lane did not | **High** | Y45 pattern not extended to D07 |
| 13 | Vehicle tokens in thread trigger add-car on remove follow-ups | **Critical** | D07 T2–3 summary "New quote" |
| 14 | `_is_add_vehicle_request` ranked above remove in broker_next_step | **High** | Camry in merged text won remove handoff |
| 15 | Missing-doc re-extract OK on Turn 1 but not merged with prior | **Medium** | No `_merge_persisted_collected` |
| 16 | Cancellation fields recomputed but not merged on append | **Medium** | P16-Z6 #7 deferred |
| 17 | Claim fields partial — plate in collected not summary | **Low** | D05 acceptable |
| 18 | Deadline/policy hints appended post-lane (good) | **Positive** | L6500–6512 |
| 19 | `human_confirmation_fields` reads post-wipe collected | **Medium** | Downstream noise on empty lists |
| 20 | Postgres mirror stores whatever triage emits — garbage in | **High** | Office truth = triage output |

---

## TOP 10 memory-loss locations

| # | Location | File:line | Mechanism | Journeys hit |
|---|----------|-----------|-----------|--------------|
| 1 | Else branch field wipe | `triage.py` ~6489 | `collected_fields = []` | D10, D03, D02 |
| 2 | Add-car lane on sold vehicle thread | `_effective_add_car_lane_active` | Year/make in merged text | **D07** |
| 3 | No persisted merge on non-add-car | `triage_conversation` collected block | Re-extract only | D03, D10, D02 |
| 4 | UW classifier before missing-doc | `_is_underwriting_followup_request` | `核保` wins | **D03** |
| 5 | No payment thread lane | `_rule_based_triage` | Status ping → UW | **D02** |
| 6 | Chinese installment not classified | markers + `_rule_based_triage` | → `unclear` | **D10** |
| 7 | ZIP `\b` boundary on CJK text | regex extractors | Empty zip hint | **D03** |
| 8 | Boundary split remove + materials | `_classify_append_case_boundary` | `prior=remove_car; last=add_car` | D07 T2 |
| 9 | Broker step add-car before remove | `_build_customer_question_broker_next_step` | Order of checks | D07 T2–3 |
| 10 | Battery without persisted context | `run_role_d_memory_battery.py` | Append ≠ production | All (measurement gap) |

---

## D03 — Why zip / garaging lost memory

```
Day 1: 核保说要我补garaging proof，我搬家到94588了
       → underwriting_followup (核保) → collected []
Day 2–3: materials sent → re-extract without merge → zip never structured
```

**Root causes:** (1) UW before missing-doc, (2) ZIP regex, (3) no persisted merge, (4) no `garaging_zip` token.

---

## D10 — Why installment / $200 lost memory

```
Day 1: 保单停了，我想分期付清能恢复吗？ → unclear (no 分期 marker)
Day 2: 首付$200… → unclear, collected []
Day 3: carrier confirm → still unclear, all fields wiped
```

**Root causes:** (1) Chinese payment markers missing, (2) policy_stop alone → cancel not lapse+installment, (3) else wipe, (4) no payment_amount extractor.

---

## D02 — Why paid / #88291 lost memory

```
Day 1–2: payment_lapse + already_paid_claimed ✅
Day 3: "underwriting or billing" → underwriting_followup, boundary split
       → loses payment headline, broker step generic UW
```

**Root causes:** (1) No payment thread lane, (2) `prior=generic` on lapse thread, (3) billing domain → new_issue, (4) confirmation # not extracted.

---

## Phase 1 verdict

Memory loss is **concentrated in one code path** — the collected-fields else branch and missing generic persisted merge. Fix is reuse-first extension of add-car pattern, not new architecture.
