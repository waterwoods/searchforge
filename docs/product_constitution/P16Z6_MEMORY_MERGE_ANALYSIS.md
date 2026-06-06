# P16-Z6 Phase 3 — Memory Merge Investigation (Y44 / Y45)

**Date:** 2026-06-02  
**Focus:** `conversation_summary`, `collected_fields`, `still_needed_fields`, correction + premium append

---

## Y44 — Correction (cancel → address/UW)

**Thread:** T1 `保单要cancel了` → T2 `不是payment问题，是地址不对被UW退回了`

| Field | Before Z6 | After Z6 |
|-------|-----------|----------|
| `issue_category` | `customer_question` ✅ | ✅ |
| `conversation_summary` | Address only; **no “cancel”** | `Prior turn: 保单要cancel了. Address / garaging change…` |
| `collected_fields` | `[]` | `[]` (acceptable for battery) |
| P16-Y score | **79** | **86** |

**Root cause:** `_build_conversation_summary` used merged text for intent but **latest bubble only** for headline; correction tag existed without prior bubble injection.

**Fix shipped:** `_prepend_prior_customer_turn_on_correction()` — prepends prior customer bubble on correction or premium continuation.

---

## Y45 — Premium thread (renewal → bill sent)

**Thread:** T1 `续保费太高` → T2 `我发你账单了，你看能不能换便宜点的coverage`

| Field | Before Z6 | After Z6 |
|-------|-----------|----------|
| `conversation_summary` | `New quote / new vehicle` ❌ | `Prior turn: 续保费太高. Premium review / too high.` |
| `collected_fields` | `[]` (add-car still_needed leaked) | `premium_concern`, `renewal_context`, `bill_sent_claimed`, … |
| `still_needed_fields` | add-car slots ❌ | `target_coverage_preference` |
| P16-Y score | **79** | **86** |

**Root cause:** `_is_add_vehicle_request` matched Turn 2 “便宜 + coverage” re-shop heuristic; add-car lane overrode premium thread.

**Fix shipped:**
- `_thread_is_premium_review_lane()` — detects renewal + bill-sent continuation  
- `_effective_add_car_lane_active` returns False when premium lane  
- `is_add_car` forced False when premium lane on merged thread  
- `_extract_renewal_fields` + `bill_sent_claimed` in collected  
- Summary intent checks premium lane before add-car  

---

## TOP 10 memory-loss causes

| # | Cause | Cases affected |
|---|-------|----------------|
| 1 | Summary built from latest bubble only | Y44, claims corrections |
| 2 | Add-car re-shop heuristic eats premium “coverage” wording | Y45 |
| 3 | `collected_fields` cleared for non-add-car `else` branch | Multi-turn general |
| 4 | No merge of `persisted_collected_fields` on non-add-car append | Office truth gap |
| 5 | Category classified on merged text but lane picked on last turn | Y45 |
| 6 | `conversation_summary` overwrite on append (no prepend) | All multi-turn |
| 7 | Chinese keywords not scored in battery regex (`\w{4,}`) | Scoring blind spot |
| 8 | `policy_bill_sent` too broad / `bill_sent_claimed` missing | Y45 |
| 9 | Correction `follow_up_type` not driving summary merge | Y44 |
| 10 | Broker UI not showing thread → perceived “memory loss” | All Turn 2+ |

---

## TOP 10 merge fixes

| # | Fix | Status |
|---|-----|--------|
| 1 | `_prepend_prior_customer_turn_on_correction` | **Shipped** |
| 2 | `_thread_is_premium_review_lane` | **Shipped** |
| 3 | Premium before add-car in summary intent order | **Shipped** |
| 4 | `bill_sent_claimed` in renewal collected | **Shipped** |
| 5 | Disable add-car lane when premium thread | **Shipped** |
| 6 | Render thread so merge visible to broker | **Shipped** (UI) |
| 7 | Merge persisted collected on all append paths | Deferred |
| 8 | Plate/police# in claim summary across turns | Deferred |
| 9 | Default-open activity after append | Deferred |
| 10 | Turn-delta block (add-car rail generalization) | Deferred |
