# P16-Z10A Phase 2 — Generic Merge Design

**Date:** 2026-06-02  
**Sprint:** P16-Z10A Memory Core Hardening  
**Pattern source:** `_augment_add_car_fields_from_persisted_collected`, `_reconcile_add_car_lists_with_persisted_record`

---

## Question

Can `_augment_add_car_fields_from_persisted_collected()` become generic?

**Answer: Yes.** The add-car stack already implements the contract:

1. Extract fresh fields from merged thread
2. Union with `persisted_collected_fields` from `reply_truth_context`
3. Drop `still_needed` entries satisfied by persisted collected
4. Preserve order via `dedupe_preserve_order`

Add-car adds **correction invalidation** (`_effective_persisted_for_add_car_merge`) — lane-specific, stays add-car only.

---

## Design: `_merge_persisted_collected()`

```python
def _merge_persisted_collected(
    new_collected: list[str],
    new_still: list[str],
    persisted: list[str] | None,
    *,
    persisted_still: list[str] | None = None,
) -> tuple[list[str], list[str]]:
```

### Behavior

| Step | Action |
|------|--------|
| 1 | Union `persisted` into `new_collected` (dedupe, preserve order) |
| 2 | Remove from `new_still` any item already in persisted collected |
| 3 | Optionally re-append prior `still_needed` not contradicted by new collected |
| 4 | Return merged lists |

### What stays add-car-only

| Function | Reason |
|----------|--------|
| `_augment_add_car_fields_from_persisted_collected` | Maps slot IDs → truth flags |
| `_effective_persisted_for_add_car_merge` | Correction invalidation per slot |
| `_reconcile_add_car_lists_with_persisted_record` | Thin wrapper — can delegate to generic merge |

---

## Wiring (implemented)

```
triage_conversation()
  └─ read reply_truth_context.persisted_collected_fields
  └─ lane branch (add_car | remove | premium | claim | missing_doc | payment | else)
  └─ _merge_persisted_collected(fresh, still, persisted, persisted_still=prior_still)
  └─ else branch: if persisted non-empty → merge, don't wipe
```

### Append path

```
triage_for_append(existing, new, reply_truth_context)
  └─ case_store passes prior collected_fields as persisted_collected_fields
  └─ battery now simulates same (Z10A)
```

---

## Lane matrix (post-Z10A)

| Lane | Fresh extract | Persisted merge | Correction invalidation |
|------|---------------|-----------------|-------------------------|
| add_car | `_compute_add_car_collected_still_lists` | ✅ (existing + generic) | ✅ add-car only |
| remove_car | `_remove_car_structured_fields` | ✅ generic | ❌ |
| premium | `_renewal_structured_fields` | ✅ generic | ❌ |
| claim | `_claim_structured_fields` | ✅ generic | ❌ |
| missing_doc | `_missing_document_structured_fields` | ✅ generic | ❌ |
| payment/cancel | `_cancellation_structured_fields` | ✅ generic | ❌ |
| else | `[]` | ✅ if prior non-empty | ❌ |

---

## Safety gates

- **No new storage** — reuses `reply_truth_context.persisted_collected_fields`
- **No new service** — single helper in `triage.py`
- **Add-car correction path untouched** — invalidation runs before generic merge on add-car spine only
- **P16-Y regression:** 88.9/100 unchanged after implementation

---

## Phase 2 verdict

Generic merge is a **~40-line helper** generalizing existing add-car reconcile logic. Safe to ship; D03/D10/D02 retention improved without CollectedFieldsService.
