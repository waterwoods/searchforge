# P16-Z10A Phase 7 — Reality Impact

**Date:** 2026-06-02  
**Sprint:** P16-Z10A Memory Core Hardening  
**Method:** Role D battery delta + founder journey mapping

---

## Score deltas

| Metric | Before (Z7) | After (Z10A) | Delta |
|--------|-------------|--------------|-------|
| **Role D reread** | 68.9 | **75.8** | **+6.9** |
| **Role D memory** | 60.7 | 62.3 | +1.6 |
| **Needs WeChat** | 4/10 | **0/10** | **−4** |
| Category match | 5/10 | 9/10 | +4 |
| P16-Y avg | 88.9 | 88.9 | 0 |

---

## Need WeChat delta

| Journey | Before | After | Why |
|---------|--------|-------|-----|
| D01 | needs | no | payment_amount + deadline in collected |
| D02 | needs | no | payment lane + persisted paid fields |
| D03 | needs | no | garaging + zip in structured output |
| D10 | needs | no | payment_lapse + installment + $200 |
| D04–D09 | no | no | stable |

**Net: 4 → 0** (target was ≤3/10)

---

## Chen Kui reality simulation

| Scenario | Before Z10A | After Z10A | Office impact |
|----------|-------------|------------|---------------|
| Client sends garaging proof + new ZIP over 3 days | Re-read paste for 94588 | ZIP in collected chips | **−2 min/case** |
| Sold car + refund follow-up | Mis-routed to add-car quote | Remove lane stable | **Avoid wrong client reply** |
| Chinese installment after lapse | "unclear" × 3 days | payment_lapse + fields | **Actionable handoff** |
| Autopay failed + paid claim | Loses paid status Day 3 | Fields persist | **No carrier re-call** |

---

## Role D score delta by fix

| Fix | Journeys helped | Est. reread Δ |
|-----|-----------------|---------------|
| `_merge_persisted_collected` | D03, D10, D02 | +2.0 |
| `_thread_is_remove_car_lane` | D07 | +1.0 |
| `_thread_is_payment_lapse_lane` | D02, D10 | +1.5 |
| ZIP / payment_amount extractors | D03, D01 | +1.0 |
| Missing-doc vs UW classifier | D03 | +0.5 |
| Battery persisted context | measurement accuracy | +0.9 |

---

## What we did NOT build (impact preserved)

No CRM sync, no WeChat API, no new DB tables — improvements are **in-triage only**. Broker still pastes + appends; case record now **remembers** without new UI.

---

## Phase 7 verdict

**Commercial impact: moderate-high for 3-day threads.** Reread crosses the 75 threshold brokers need to reopen a case without WeChat. Next slice (not Z10A): confirmation # token, claims field extensions, waiting_on heuristic (Z8 Day 2 backlog).
