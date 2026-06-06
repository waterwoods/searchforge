# P16-Z8 Phase 3 — Collected Fields Archaeology

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Search terms:** `collected_fields`, `still_needed_fields`, append, merge, case update  
**Sources:** `triage.py` L6329–6348, `case_store.py`, P16-Z6 merge analysis, Role D battery

---

## Executive summary

`collected_fields` / `still_needed_fields` are **production-grade on Turn 1** for lane-matched paths. **Append merge is add-car only** — all other lanes re-extract from merged text and **clear on else branch**, losing persisted office truth.

**Critical code path (`triage.py` L6329–6348):**

```python
if is_add_car:
    # full merge via _add_car_structured_fields + persisted_collected
elif _is_premium_review_request(lowered):
    collected, still_needed = _renewal_structured_fields(merged_text)
elif _is_claim_intake_request(lowered):
    collected, still_needed = _claim_structured_fields(merged_text)
elif issue_category == "missing_document":
    ...
elif issue_category in ("cancellation_warning", "payment_lapse_expiration"):
    ...
else:
    result["collected_fields"] = []
    result["still_needed_fields"] = []
```

---

## Lane-by-lane merge matrix

| Lane | Turn 1 extract | Append re-extract | Persisted merge | Summary merge | UI chips | Verdict |
|------|----------------|-------------------|-----------------|---------------|----------|---------|
| **add_car** | ✅ `_add_car_structured_fields` | ✅ | ✅ `_augment_add_car_fields_from_persisted_collected` | ✅ | ✅ | **MERGE OK** |
| **premium_review** | ✅ `_renewal_structured_fields` | ⚠️ Recompute only | ❌ | ✅ Z6 prior-turn | ✅ | **PARTIAL** |
| **claim_intake** | ✅ `_claim_structured_fields` | ⚠️ Recompute only | ❌ | ⚠️ | ✅ | **PARTIAL** |
| **missing_document** | ✅ `_missing_document_structured_fields` | ⚠️ Recompute | ❌ | ✅ | ✅ | **PARTIAL** |
| **cancellation / lapse** | ✅ `_cancellation_structured_fields` | ⚠️ Recompute | ❌ | ⚠️ | ✅ | **PARTIAL** |
| **remove_car** | ⚠️ Summary hint only | ❌ | ❌ | ⚠️ | ❌ | **LOSES** |
| **underwriting_followup** | ⚠️ Generic + deadline token | ❌ | ❌ | ✅ | ⚠️ | **LOSES** |
| **customer_question** | ❌ Cleared | ❌ | ❌ | ⚠️ | ❌ | **LOSES** |
| **unclear** | ❌ Cleared | ❌ | ❌ | ❌ | ❌ | **LOSES** |
| **payment (generic)** | ❌ No dedicated branch | ❌ | ❌ | ⚠️ prose | ❌ | **LOSES** |

### Append-specific behavior

| Operation | Merges collected? | Location |
|-----------|-------------------|----------|
| `append_follow_up_message()` | Overwrites from triage result | `case_store.py` L1160–1163 |
| `triage_for_append()` | Passes `reply_truth_context.persisted_collected_fields` | **add-car only** |
| Deadline / policy hints | Appended to whatever lane produced | L6357–6368 |
| Correction invalidation | Add-car persisted override | `_add_car_structured_fields` |

---

## Which lanes merge correctly?

1. **add_car** — Full persisted merge, still_needed union, truth guardrails. **Gold standard.**
2. **premium_review** — Re-extract from full merged text works when lane stable (D08). Fails when last turn drifts lane.
3. **missing_document** — Re-extract usually OK if category stable; D03 zip not captured in structured list.

---

## Which lanes lose memory?

| Lane | Role D evidence | Mechanism |
|------|-----------------|-----------|
| remove_car | D07 | No structured branch; add-car overwrites |
| payment / installment | D10 | `unclear` → else clears |
| cancel + amount | D01 | `$420` not in extractor |
| missing_doc zip | D03 | Zip in summary, not `collected_fields` |
| claim corrections | CL02, CL10 | Re-extract drops prior FNOL tokens |
| underwriting | D04 | **Mostly OK** — policy # via hint append |
| generic customer_question | D06 T1–2 | Cleared until lane resolves |

---

## Hidden merge capabilities

| # | Capability | Status |
|---|------------|--------|
| 1 | `persisted_collected_fields` in reply_truth_context | add-car only |
| 2 | `merge_still_needed_for_intent()` | add-car only |
| 3 | `_augment_add_car_fields_from_persisted_collected()` | add-car only |
| 4 | `deadline_mentioned` post-append append | All lanes (if not cleared first) |
| 5 | `policy_number` post-append append | All lanes (if not cleared first) |
| 6 | `human_confirmation_fields` | Reads collected after lane branch |
| 7 | Postgres `service_record` mirror | Stores whatever triage emits |
| 8 | Session store collected | Mid-flow restore; not append path |

---

## TOP 10 merge fixes (reuse-first)

| # | Fix | Reuses | Effort |
|---|-----|--------|--------|
| 1 | Generic `_merge_persisted_collected(prior, new)` | add-car augment pattern | 4 hr |
| 2 | `_remove_car_structured_fields()` | `_extract_remove_car_fields` | 2 hr |
| 3 | Payment amount / installment extractors | cancellation pattern | 4 hr |
| 4 | Claim plate/$ in collected | regex on merged thread | 4 hr |
| 5 | Lane-stable append: infer domain from prior case | `_infer_prior_case_domain` | 2 hr |
| 6 | Don't clear else when prior collected non-empty | 5-line guard | 1 hr |
| 7 | Zip → `collected_fields` for missing_doc | extend extractor | 2 hr |
| 8 | Test: append preserves D03/D10 fields | Role D battery | 2 hr |
| 9 | UI turn-delta for collected changes | `buildAddCarRailTurnModel` | 0.5 day |
| 10 | Document merge contract in CAPABILITY_04 | existing contract | 1 hr |

---

## Phase 3 verdict

**One merge pattern exists (add-car).** Extend it — do not build CollectedFieldsService. **~1 engineer-day** for generic persisted merge + lane-specific extractors.
