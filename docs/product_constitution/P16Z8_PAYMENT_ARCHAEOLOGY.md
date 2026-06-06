# P16-Z8 Phase 1 — Payment Memory Archaeology

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Search terms:** `premium_review`, `renewal`, `bill_sent`, `policy_bill_sent`, `bill_sent_claimed`, `payment_issue`, `lapse`, `installment`, `renewal_structured_fields`  
**Sources:** `triage.py`, `case_store.py`, `configs/industries/insurance/markers.json`, Role D battery (D01, D02, D08, D10), P16-Z6 Y45, P16L payment docs

---

## Executive summary

Payment memory is **partially built** in the engine — strong on Turn 1 English cancel/lapse and premium renewal (post-Z6), **broken** on Chinese installment/lapse multi-turn and **hidden** in `collected_fields` for non-lane-matched threads. There is **no separate payment service**; everything lives in `triage.py` extractors and category classifiers.

| Verdict | Share of payment memory gap |
|---------|----------------------------|
| **Already built** | ~45% |
| **Partially built** | ~25% |
| **Hidden** | ~15% |
| **Broken** | ~10% |
| **Truly missing** | ~5% |

---

## What already exists?

### Categories & classifiers

| Asset | Location | Status |
|-------|----------|--------|
| `payment_lapse_expiration` | `triage.py` L182, L1092+, L1473+ | **Built** — high urgency, templates EN/ZH |
| `cancellation_warning` | Same | **Built** |
| `renewal_reminder` | L1658–1659 | **Built** — passive renewal only |
| `premium_review` markers | L239–240, `_is_premium_review_request()` L643 | **Built** |
| Payment risk markers | `configs/industries/insurance/markers.json` | **Built** |
| LLM category prompt | L1836–1853 | **Built** (env-gated path) |

### Structured field extractors

| Function | Returns | Lane |
|----------|---------|------|
| `_extract_cancellation_fields()` | notice, screenshot, already_paid, urgency | cancel/lapse |
| `_cancellation_structured_fields()` | `already_paid_claimed`, `verify_carrier_received` | cancel/lapse |
| `_extract_renewal_fields()` | premium_concern, renewal_context, bill_sent_claimed, policy_bill_sent | premium |
| `_renewal_structured_fields()` | Same → collected/still_needed | premium |
| `_thread_is_premium_review_lane()` | Cross-bubble premium thread (Y45) | premium |
| `_extract_deadline_hint()` | `deadline_mentioned` token | all lanes |
| `_extract_policy_number_hint()` | `policy_number` token | all lanes |

### Summary / continuity (P16-Z6 shipped)

| Capability | Status |
|------------|--------|
| Prior-turn prepend on premium continuation | **Shipped** — `_prepend_prior_customer_turn_on_correction()` |
| Premium lane blocks add-car misroute | **Shipped** — `_effective_add_car_lane_active()` L3097 |
| `bill_sent_claimed` in collected | **Shipped** — D08 validated (Role D reread 90) |
| Payment hints in `conversation_summary` | **Built** — collected_hint for already_paid / screenshot |

### UI & persistence

| Asset | Status |
|-------|--------|
| `collected_fields` / `still_needed_fields` on case | **Built** — `case_store.py` L704–707 |
| Glance chips for payment fields | **Partial** — inside collapsed 整理明细 |
| `human_confirmation_fields` for payment-risk | **Built** — `_derive_human_confirmation_fields()` |
| P16L payment evidence model | **Docs only** — not wired to engine |

---

## What is hidden?

1. **`policy_bill_sent` over-broad** — any 发/sent/bill in thread fires; not distinguished from garaging/doc sends (Y45 root cause pre-fix).
2. **`_renewal_structured_fields()` only runs when `_is_premium_review_request(lowered)`** — thread-level premium lane can miss if last bubble is refund/status ping.
3. **Cancellation fields not merged on append** — `_cancellation_structured_fields()` recomputes from merged text but **prior `collected_fields` cleared** on non-matching else branch (P16-Z6 #7).
4. **Installment / 分期 — no extractor** — D10 `$200`, `3 installments` never become field tokens.
5. **Payment amount regex** — `$420`, `confirmation #88291` hit `policy_number` or summary prose only, not `payment_amount` / `confirmation_number` fields.
6. **Chinese lapse wedge** — markers exist but classifier returns `customer_question` or `unclear` (D01, D10).
7. **v4/v5 payment risk scores** — computed in `case_draft_engine.py`, **not shown** in workbench.
8. **Category templates for payment** — `category_templates.json` has broker steps; `client_prep` product_only gated.
9. **Postgres payment mirror** — `service_record_repository.py` stores fields; broker sees tag only.
10. **P16L `payment_evidence` contract** — documented, zero code path.

---

## What is broken?

| Failure | Evidence | Root cause |
|---------|----------|------------|
| D10 Chinese installment → `unclear` ×3 | Role D battery | No 分期/installment classifier branch; no structured fields |
| D01 $420 not in collected | Role D | Amount not in `_extract_cancellation_fields()` |
| D02 Day 3 UW pivot loses #88291 | Role D | Boundary `new_issue` + category drift; collected cleared |
| D02 `policy_number` mislabeled as lapse | Role D | Generic policy hint without payment context |
| Premium thread → add-car (pre-Z6) | Y45 | **Fixed** by `_thread_is_premium_review_lane()` |
| Summary latest-bubble-only (pre-Z6) | Y44/Y45 | **Fixed** by prior-turn prepend |
| `else: collected_fields = []` | `triage.py` L6346–6348 | Wipes payment facts on lane mismatch |

---

## TOP 20 payment memory capabilities

| # | Capability | Class | Location |
|---|------------|-------|----------|
| 1 | `payment_lapse_expiration` category + urgency | **Built** | `triage.py` classify |
| 2 | `cancellation_warning` category + templates | **Built** | `triage.py`, reply templates |
| 3 | `_extract_cancellation_fields()` | **Built** | notice, paid, screenshot flags |
| 4 | `_cancellation_structured_fields()` | **Built** | collected/still for cancel |
| 5 | `_is_premium_review_request()` | **Built** | Marker-based premium detect |
| 6 | `_extract_renewal_fields()` | **Built** | premium, renewal, bill_sent |
| 7 | `_renewal_structured_fields()` | **Built** | renewal collected/still |
| 8 | `_thread_is_premium_review_lane()` | **Built** (Z6) | Multi-bubble premium thread |
| 9 | `bill_sent_claimed` field | **Built** (Z6) | Renewal handoff loop |
| 10 | `policy_bill_sent` field | **Partial** | Too broad |
| 11 | Prior-turn prepend on premium | **Built** (Z6) | `_prepend_prior_customer_turn_on_correction` |
| 12 | Premium blocks add-car lane | **Built** (Z6) | `_effective_add_car_lane_active` |
| 13 | `_extract_deadline_hint()` | **Built** | deadline_mentioned token |
| 14 | `_extract_policy_number_hint()` | **Partial** | No confirmation # distinction |
| 15 | Payment summary hints (already paid) | **Built** | `_build_conversation_summary` L2093+ |
| 16 | `human_confirmation_fields` payment-risk | **Built** | High-risk field surfacing |
| 17 | `renewal_reminder` low-urgency path | **Built** | Passive renewal |
| 18 | Handoff broker step for bill sent | **Built** | L6410–6416 premium handoff |
| 19 | Payment markers config | **Built** | `markers.json` |
| 20 | Case persistence of payment fields | **Built** | `case_store.py` merge on triage |

---

## TOP 10 payment memory gaps

| # | Gap | Class | Fix type |
|---|-----|-------|----------|
| 1 | Chinese installment / 分期 classification | **Broken** | Classifier + markers (D10) |
| 2 | Payment amount → structured field | **Missing** | `$420`, `200块` extractor |
| 3 | Confirmation number vs policy # | **Partial** | Separate `confirmation_number` token |
| 4 | Non–add-car collected merge on append | **Broken** | P16-Z6 deferred #7 |
| 5 | Installment plan fields | **Missing** | `installment_count`, `installment_amount` |
| 6 | Chinese cancel wedge → `cancellation_warning` | **Broken** | D01 category drift |
| 7 | Day 3 status ping preserves payment narrative | **Broken** | Boundary + summary refresh |
| 8 | `policy_bill_sent` precision | **Partial** | Narrow to bill-specific phrases |
| 9 | Payment fields in broker glance hero | **Hidden** | UI promote chips |
| 10 | P16L payment evidence model | **Missing** | Defer — docs only today |

---

## Phase 1 verdict

**Do not rebuild payment memory.** Extend `triage.py` classifiers and add `_merge_persisted_collected()` on append. Highest leverage: Chinese lapse/installment (1 day) + collected merge (1 day). D08 proves premium path is **commercial-ready** after Z6.
