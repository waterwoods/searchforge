# P16-Z10A Phase 4 — Remove Vehicle Audit

**Date:** 2026-06-02  
**Sprint:** P16-Z10A Memory Core Hardening  
**Oracle:** Role D D07  
**Sources:** `triage.py`, P16-Z8_REMOVE_VEHICLE.md, battery trace

---

## Executive summary

Remove-vehicle was **~60% built** — detection, summary hints, handoff copy existed. **D07 failed** because add-car vehicle extraction ate "2018 Toyota Camry" on Day 2–3 when the last bubble was materials/refund language. **No thread-level remove lane guard** existed (unlike Y45 premium fix).

---

## Why add-car wins (D07 trace)

```
Day 1: 我把2018 Toyota Camry卖掉了，要从保单拿掉  → remove_car ✅
Day 2: bill of sale和新车主的transfer都发你了     → add_car ❌ (vehicle + 发你了)
Day 3: refund大概多少？什么时候生效？              → add_car ❌ (Camry in thread)
```

### Root cause chain

1. Day 3 last bubble has **no remove_vehicle markers** → `_last_customer_turn_blocks_add_car_context_carryover()` returns False
2. Merged thread contains **year + make/model** → add-car extractors fire
3. Day 2 `发你了` → `follow_up_type: already_sent` + add-car materials path
4. **No `_thread_is_remove_car_lane()`** equivalent to premium lane guard
5. **No `_remove_car_structured_fields()`** — remove facts in summary prose only
6. Boundary classifier: `prior=remove_car; last=add_car` → `new_issue`
7. `_build_customer_question_broker_next_step`: add-car checked **before** remove on merged text

---

## What already existed

| Asset | Status |
|-------|--------|
| `remove_vehicle` markers | Built |
| `_is_remove_vehicle_request()` | Built |
| `_extract_remove_car_fields()` | Built |
| Summary collected_hint for remove | Built (prose only) |
| `_infer_prior_case_domain()` → remove_car | Built |
| Handoff phrase + broker_next_step on remove | Built (when `is_remove_car`) |
| `_last_customer_turn_blocks_add_car` includes remove | Built — **last turn only** |

---

## TOP 10 routing conflicts

| # | Conflict | Winner (pre-Z10A) | Should win | Fix (Z10A) |
|---|----------|-------------------|------------|------------|
| 1 | remove_car + year/make/model → add_car | add_car | remove_car | `_thread_is_remove_car_lane` + block add-car |
| 2 | remove + premium ("去掉会便宜") | premium | context | unchanged |
| 3 | remove + materials already_sent | add_car materials | remove_car docs | remove lane + structured fields |
| 4 | remove + refund/billing ping | add_car / new_issue | remove_car | boundary exception billing+remove |
| 5 | remove + claim (sold after accident) | claim | broker confirm | unchanged |
| 6 | remove markers need vehicle_context | unclear | remove_car | unchanged |
| 7 | `_prior_thread_signals_add_car` vs sold vehicle | add_car | remove_car | remove lane guard |
| 8 | Boundary new_issue on billing follow-up | splits narrative | same_case | `prior=remove_car + billing` pass |
| 9 | Mixed remove + coverage adjust | premium | premium | unchanged |
| 10 | Chinese 删车 without 车 token | unclear | remove_car | unchanged |

---

## Phase 5 guard (implemented)

### `_thread_is_remove_car_lane(merged_text)`

Mirrors `_thread_is_premium_review_lane()`:

- Any bubble has remove markers + vehicle context → lane active
- Multi-bubble: first bubble sold/remove + last bubble refund/materials/transfer → lane active

### Integration points

| Location | Change |
|----------|--------|
| `_effective_add_car_lane_active` | Return False when remove lane |
| `triage_conversation` | `is_add_car = False` when remove lane |
| `_build_conversation_summary` | Remove intent before add-car |
| `_build_customer_question_broker_next_step` | Remove lane before add-car |
| `_classify_append_case_boundary` | remove + billing/add_car materials → same_case |
| Collected branch | `_remove_car_structured_fields` + merge |

---

## D07 post-Z10A

| Metric | Before | After |
|--------|--------|-------|
| Summary headline | "New quote / new vehicle" | "Remove vehicle from policy" |
| collected_fields | add-car slots | vehicle, year, make_model, transfer_completed |
| Reread | 70 | **80** |
| Lane stable Day 3 | ❌ | ✅ |

---

## Phase 4 verdict

Remove vehicle fix = **lane guard + structured fields + boundary exception**. No new service. Mirrors Y45 premium pattern. D07 passes.
