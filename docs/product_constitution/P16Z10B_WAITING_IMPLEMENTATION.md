# P16-Z10B Phase 3 — Waiting-On Implementation

**Date:** 2026-06-02  
**File:** `services/fiqa_api/inbox_triage/triage.py`

---

## Shipped

### `_suggest_waiting_on(merged_text, still_needed_fields, issue_category)`

- Rule-based scan of full merged thread + still_needed + category  
- Returns one of: `client`, `broker`, `carrier`, `underwriting`, or `""`  
- ~90 lines; no new imports beyond existing `re`

### Triage wiring

After collected/still merge and payment hints:

```python
suggested_wo = _suggest_waiting_on(...)
if suggested_wo:
    result["suggested_waiting_on"] = suggested_wo
```

Applies to both `triage_conversation` and `triage_for_append` (shared spine).

### Battery

`scripts/run_role_d_memory_battery.py`:

- `WAITING_ON_SCENARIOS` — 9 Role D Day-3 phrases  
- `_score_waiting_on()` — direct heuristic unit test  
- Reread blob includes `suggested_waiting_on` for oracle scoring  

---

## No new API / storage

| Item | Status |
|------|--------|
| New table | ❌ |
| New endpoint | ❌ |
| Auto PATCH | ❌ |
| `case_store` change | ❌ |

Broker flow: read triage card → PATCH `waiting_on` if agree.

---

## Validation

| Metric | Before Z10B | After Z10B |
|--------|-------------|------------|
| waiting_on auto | 0/9 | **9/9** |

---

## Phase 3 verdict

**PASS** — highest-ROI Z8 backlog item shipped in ~0.5 day scope with zero architecture drift.
