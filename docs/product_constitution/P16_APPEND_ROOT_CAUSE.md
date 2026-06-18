# P16 Append Integrity — Root Cause

**Date:** 2026-06-06  
**Sprint:** P16-APPEND-INTEGRITY-SPRINT — Phase 2

---

## Primary root cause (one)

**`append_follow_up_message()` replaces `collected_fields` / `still_needed_fields` wholesale from fresh triage output instead of merging additively with the persisted case record.**

Evidence:

1. **Store overwrite** — `case_store.py` (pre-fix) assigned triage lists directly:

```python
normalized_case["collected_fields"] = [str(x) for x in collected]  # from triage only
normalized_case["still_needed_fields"] = [str(x) for x in still_needed]
```

2. **Controlled reproduction** — Saved case with `delivery_date` in `collected_fields`. Crafted triage result (simulating missing `persisted_collected_fields` in `reply_truth_context`) dropped `delivery_date` from collected and reintroduced it in `still_needed`. `append_follow_up_message()` persisted the regression. See `P16_APPEND_REPRODUCTION.md`.

3. **Triage drop mechanism** — When `reply_truth_context` lacks `persisted_collected_fields`, `triage_for_append()` re-extracts from full thread but strict truth guardrails reject relative `next Wednesday` on the append turn (last bubble is name/phone only). Fresh `collected_fields` omits `delivery_date`; `still_needed_fields` adds it back. This is correct *extraction* but must not erase durable case memory at persist time.

---

## Investigation answers

| Question | Answer | Evidence |
|----------|--------|----------|
| 1. Where is `delivery_date` lost? | At **persist** in `append_follow_up_message()` | Overwrite test: before collected had `delivery_date`, after did not |
| 2. Is append replacing fields? | **Yes** — full replace, not union | `case_store.py` lines 1164–1167 (pre-fix) |
| 3. Is append rebuilding from partial data? | Triage rebuilds from thread; can drop relative slots without persisted merge | `triage_for_append` with `ctx={"formal_submitted_at": ...}` only → `delivery_date` in `still_needed` |
| 4. Is append overwriting structured memory? | **Yes** | Case JSON/Postgres `structured_payload.collected_fields` overwritten |
| 5. Is `still_needed` recomputed incorrectly? | Triage recomputation is locally consistent; **store** makes it durable and wrong | Merged still regressed because collected was wiped |

---

## Why triage merge was insufficient alone

`triage.py` has `_merge_persisted_collected()` and `_reconcile_add_car_lists_with_persisted_record()`, but:

- They only run when `persisted_collected_fields` is present in `reply_truth_context`.
- `append_follow_up_message()` had **no second-line defense** if triage output regressed.
- Commercial rule: **persisted case record is authoritative memory**; append must be additive at the store boundary.

---

## Fix location

| File | Function | Change |
|------|----------|--------|
| `services/fiqa_api/inbox_triage/case_store.py` | `_merge_append_field_lists()` | Union prior + new collected; block still_needed reintroduction |
| `services/fiqa_api/inbox_triage/case_store.py` | `append_follow_up_message()` | Use merge; recompute `office_broker_next_step` when merged still ≠ triage still |
| `services/fiqa_api/inbox_triage/triage.py` | `_extract_contact_fields()` | Recognize `Name: Li Hua` English labeled pattern |

---

*Phase 2 complete.*
