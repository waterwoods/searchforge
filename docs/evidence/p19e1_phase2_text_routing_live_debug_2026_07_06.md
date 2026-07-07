# P19E-1 Phase 2 Text Routing — Live Debug

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Live revision (failure):** `fiqa-api-00160-44g` (`c252369`)  
**Fix commit:** `9cb7e5f` — not yet redeployed  
**Verdict:** **ROOT CAUSE CONFIRMED** · **FIX LOCAL PASS** · **DEPLOY HOLD**

---

## Andy Live Failure

| Step | Result |
|------|--------|
| `重新加车` → H5 三步 | ✅ |
| Stage Complete S1 | ✅ |
| Text: `7月10号提车，zip. 92705。电话2031234567` | ❌ greeting menu |
| Workbench fields | ❌ no delivery_date / zip / phone |

---

## Log Investigation (01:14 UTC ≈ PT 18:14)

**Case:** `case_e341aa97b8c8` (suffix only — no full external_userid)

```
01:14:01  h5_flow_complete_notify_sent_v1  (S1)
01:14:45  normalized text + phone=2031234567
01:14:46  stale_draft_binding_cleared_v1   case_e341aa97b8c8
01:14:46  intent_v1 unclear / guided_menu_required: true
01:14:46  reply greeting menu
```

**Not called:** `wecom_phase2_text_ingest_v1`

---

## Root Cause

| # | Finding |
|---|---------|
| 1 | `find_open_draft_case_by_external_userid` → Postgres `list_all_cases_for_read` → **found case** |
| 2 | `get_case_by_id` (pre-fix) → **JSON-only** → `None` on Cloud Run |
| 3 | `stale_draft_binding_cleared_v1` → open case cleared |
| 4 | Phase 2 block skipped (`open_bound_case is None`) |
| 5 | `unclear` intent → **greeting menu** |

**Not root cause:** extractors (all 3 fields parse), phone validation, phase hydration on Postgres row.

---

## Field Extraction (Andy exact text)

```text
7月10号提车，zip. 92705。电话2031234567
```

| Field | Extracted |
|-------|-----------|
| delivery_date | `7月10日` |
| zip | `92705` |
| phone | `2031234567` |

---

## Fix (`9cb7e5f`)

| File | Change |
|------|--------|
| `wecom/slice.py` | `get_case_for_read`; `resolve_add_car_case_for_phase2` |
| `wecom/add_vehicle_phase2.py` | Postgres read facade + `find_phase2_eligible_add_car_case` fallback |
| `wecom/reply.py` | Format hint when Phase 2 active but 0 fields parsed |

---

## State Machine / Pipeline Doc

`docs/p19e1_add_vehicle_case_state_machine_event_pipeline.md`

Includes Mermaid:
- Case state machine (NoCase → Phase1 → Phase2 → Phase3 → Done)
- Event pipeline with **BUG** annotation showing greeting-menu fallback

---

## Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19e1_*.py -q   # PASS
```

Covers: Andy message routing, stale-binding repro, extractors, S2, format hint, hello unchanged without case.

Postgres extra round-trip: `tests/test_service_record_wecom_extra.py` — `guided_workflow_state`, `add_vehicle_phase`.

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM | ❌ |
| Schema migration | ❌ |
| Cloud callback / VPC change | ❌ |
| Deploy this round | ❌ STOP |
| Neon | ❌ |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Root cause + fix | **GO** |
| Redeploy `9cb7e5f` | **HOLD** |
| Andy phone retest | **HOLD** until redeploy |

**After redeploy:** same text → Stage Complete S2 + `ready_for_broker_review`.
