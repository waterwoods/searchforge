# P16-Z10B Phase 6 — Claims Retention Implementation

**Date:** 2026-06-02  
**File:** `services/fiqa_api/inbox_triage/triage.py` (+ battery script)

---

## Functions added / extended

| Function | Change |
|----------|--------|
| `_is_claim_intake_request` | +claim-status markers (total loss, adjuster, rear-ended, glass, etc.) |
| `_thread_has_claim_memory` | persisted token detection |
| `_thread_is_claim_lane` | claim thread guard |
| `_extract_plate_hint` | new |
| `_extract_claim_number_hint` | new |
| `_extract_claim_amount_hint` | new (VIN exclusion) |
| `_augment_claim_collected_from_merged` | new |
| `_extract_claim_fields` | +carrier/adjuster booleans |
| `_claim_structured_fields` | +carrier/adjuster collected |
| `_build_conversation_summary` | claim `collected_hint`; claim intent before coverage |
| Payment enrichments | `payment_amount_{$}`, `payment_confirmation_{#}`, `autopay_mentioned`, Chinese cancel tokens |

---

## Lane wiring

```python
elif _thread_is_claim_lane(merged_text, _persisted_collected):
    collected, still = _claim_structured_fields(...)
    collected, still = _augment_claim_collected_from_merged(...)
    collected, still = _merge_persisted_collected(...)
```

Missing-document branch: claim lane override when persisted claim memory exists.

---

## Battery fix

`run_claims_case()` now passes `reply_truth_context` with prior `collected_fields` / `still_needed_fields` on append — matches production `case_store` path (Z10A journey fix extended to claims).

---

## P16-Y regression

| Battery | Score |
|---------|-------|
| P16-Y | **88.6/100** (≥88 ✅) |
| Guardrails | **PASS** 13/13 |

---

## Per-case retention (Z10B)

| ID | % |
|----|---|
| CL03 | 100 |
| CL06 | 100 |
| CL04, CL05 | 80 |
| CL01, CL02, CL08, CL10 | 60 |
| CL07 | 50 |
| CL09 | 80 |
| **Avg** | **71%** |

---

## Phase 6 verdict

**PASS** — claims retention crosses 70% without new architecture.
