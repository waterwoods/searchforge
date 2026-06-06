# P16-Z8 Phase 2 — Remove Vehicle Archaeology

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Search terms:** remove vehicle, remove car, vehicle removal, delete vehicle, lane routing, triage, intent classification  
**Sources:** `triage.py`, Role D D07 battery trace, `configs/industries/insurance/markers.json`, P16-Z7 founder summary

---

## Executive summary

Remove-vehicle is **partially built** — detection, summary hints, handoff copy, and broker_next_step exist. **No structured collected_fields path.** D07 fails because **add-car vehicle extraction eats "2018 Toyota Camry"** on Day 2–3 when the last bubble is materials/refund language, not remove markers.

**Why D07 failed:**

```
Day 1: 我把2018 Toyota Camry卖掉了，要从保单拿掉  → remove_car ✅
Day 2: bill of sale和新车主的transfer都发你了     → still remove-ish ✅
Day 3: refund大概多少？什么时候生效？              → add_car ❌
```

**Engine output Day 3 (Role D):**
- Summary: `New quote / new vehicle. Collected: 2018 Toyota Camry`
- `collected_fields`: `year`, `make_model`, `vin`, `zip`, `delivery_date`, `primary_driver` (add-car slots)
- `broker_next_step`: `Confirm any missing driver, ZIP, or VIN… then quote`

**Root cause chain:**

1. Day 3 last bubble has **no remove_vehicle markers** → `_last_customer_turn_blocks_add_car_context_carryover()` returns False.
2. Merged thread contains **year + make/model** → add-car extractors fire.
3. Day 2 `发你了` → `follow_up_type: already_sent` + `customer_says_materials_sent` (add-car materials path).
4. **No `_thread_is_remove_car_lane()`** equivalent to premium lane guard (Y45 pattern).
5. **No `_remove_car_structured_fields()`** — remove facts live in summary prose only; easily overwritten.
6. Boundary classifier may tag `billing` cross-domain on refund → `Boundary: new_issue` without preserving remove domain.

---

## What already exists?

| Asset | Location | Status |
|-------|----------|--------|
| `remove_vehicle` markers | `markers.json`, L252–253 | **Built** |
| `_is_remove_vehicle_request()` | L866–867 | **Built** — requires vehicle_context marker |
| `_extract_remove_car_fields()` | L4077–4101 | **Built** — vehicle, sale_date, transfer booleans |
| Summary collected_hint for remove | L2067–2077 | **Built** — prose only |
| `remove_car` in flow labels | L1996 | **Built** |
| `_infer_prior_case_domain()` → remove_car | L3115–3116 | **Built** |
| Cross-domain boundary sets | L3182–3183 | **Built** |
| Handoff phrase key `remove_car` | `triage_handoff_reply_policy.py` | **Built** |
| Remove handoff reply composer | `triage_handoff_reply_composer.py` L333+ | **Built** |
| broker_next_step on remove handoff | L6419–6422 | **Built** |
| `_last_customer_turn_blocks_add_car` includes remove | L3013–3014 | **Built** — **last turn only** |
| Reply templates `remove_vehicle` | category + client templates | **Built** |
| Scenario configs | `inbox_triage_scenarios.json`, Role D D07 | **Built** |

---

## What is hidden / broken?

| Issue | Class | Detail |
|-------|-------|--------|
| No `_remove_car_structured_fields()` | **Hidden** | Falls into `else: collected_fields = []` or add-car branch |
| No thread-level remove lane guard | **Broken** | Unlike `_thread_is_premium_review_lane()` |
| Vehicle token → add-car | **Broken** | Camry/year triggers quote lane on follow-ups |
| `remove_vehicle_interest` inside renewal fields | **Partial** | Only when premium lane active |
| Refund follow-up → billing cross-domain | **Broken** | Boundary without remove persistence |
| Tests for remove multi-turn | **Missing** | No dedicated battery case in P16-Y |
| UI remove lane indicator | **Hidden** | No badge distinct from add-car |

---

## TOP 10 routing conflicts

| # | Conflict | Turns affected | Winner today | Should win |
|---|----------|----------------|--------------|------------|
| 1 | remove_car + year/make/model → add_car | D07 T2–3 | add_car | remove_car |
| 2 | remove + premium_review ("去掉会便宜") | Premium threads | premium | context-dependent |
| 3 | remove + materials already_sent | D07 T2 | add_car materials | remove_car docs |
| 4 | remove + refund/billing ping | D07 T3 | add_car / new_issue | remove_car |
| 5 | remove + claim (sold after accident) | Rare | claim | broker confirm |
| 6 | remove markers need vehicle_context | Edge cases | unclear | remove_car |
| 7 | `_prior_thread_signals_add_car` vs sold vehicle | D07 | add_car | remove_car |
| 8 | Boundary new_issue on billing follow-up | D07 T3 | splits narrative | same_case |
| 9 | Mixed remove + coverage adjust | Premium | premium_review | premium |
| 10 | Chinese 删车 without 车 token | Sparse msgs | unclear | remove_car |

---

## TOP 10 reuse opportunities

| # | Reuse | From | Effort |
|---|-------|------|--------|
| 1 | `_thread_is_remove_car_lane(merged_text)` | Copy `_thread_is_premium_review_lane()` pattern | 2 hr |
| 2 | `_remove_car_structured_fields()` | Mirror `_renewal_structured_fields()` | 2 hr |
| 3 | Block add-car when remove lane active | `_effective_add_car_lane_active()` L3095 | 1 hr |
| 4 | Prior-turn prepend for remove thread | Z6 `_prepend_prior_customer_turn_on_correction` | 1 hr |
| 5 | Persist remove domain in `reply_truth_context` | Add-car `persisted_collected_fields` pattern | 4 hr |
| 6 | Refund follow-up broker step | Existing remove handoff L6419 | 30 min |
| 7 | Handoff templates already written | `remove_vehicle` in reply templates | 0 |
| 8 | Boundary exception: remove + billing | Extend L3206 premium exception | 2 hr |
| 9 | Role D D07 as regression oracle | `configs/role_d_journeys.json` | 0 |
| 10 | `buildAddCarRailTurnModel` generalization | Show remove delta in glance | 0.5 day UI |

---

## Phase 2 verdict

Remove vehicle is **~60% built, ~40% broken on multi-turn.** Fix is **lane guard + structured fields**, not a new service. Estimated **0.5 engineer-day** for engine; mirrors Y45 premium fix.
