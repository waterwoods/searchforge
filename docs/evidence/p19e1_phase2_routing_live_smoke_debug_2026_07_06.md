# P19E-1 Live Smoke Debug — Phase 2 Routing Fix

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Live revision (failure):** `fiqa-api-00160-44g`  
**Verdict:** **ROOT CAUSE FOUND** · **FIX READY** · **NOT DEPLOYED**

---

## Symptom

After Stage Complete S1, Andy sent:

```text
7月10号提车，zip. 92705。电话2031234567
```

**Expected:** Phase 2 handler → extract 3 fields → Stage Complete S2  
**Actual:** Greeting menu —「您好，请选择您要办理的事项……」

---

## Log Evidence (2026-07-07 01:14 UTC ≈ PT 18:14)

| Time | Event |
|------|-------|
| 01:13:08 | `重新加车` → new case `case_e341aa97b8c8` |
| 01:14:01 | H5 3/3 uploads + `h5_flow_complete_notify_sent_v1` (S1) |
| 01:14:45 | Text normalized: `7月10号提车，zip. 92705。电话2031234567`, phone=`2031234567` |
| 01:14:46 | **`stale_draft_binding_cleared_v1`** `case_e341aa97b8c8` |
| 01:14:46 | `intent_v1` → `unclear` / `guided_menu_required: true` |
| 01:14:46 | Greeting menu sent |

**Phase 2 handler never invoked** — no `wecom_phase2_text_ingest_v1` log.

---

## Root Cause

**A. Routing / case load mismatch (PRIMARY)**

| Step | Function | Read path |
|------|----------|-----------|
| Binding lookup | `find_open_draft_case_by_external_userid` | `list_all_cases_for_read()` → **Postgres** ✅ found `case_e341aa97b8c8` |
| Case load | `get_case_by_id` (pre-fix) | **JSON file only** ❌ returns `None` on Cloud Run |
| Result | `stale_draft_binding_cleared_v1` | `open_bound_case = None` |
| Fallback | Generic `unclear` intent | **Greeting menu** |

This is the same class of bug as P19D-4B End Card (`get_case_for_read` vs JSON-only read).

**B. Extractor — NOT the issue**

Local test on Andy's exact string:

| Field | Extracted |
|-------|-----------|
| delivery_date | `7月10日` |
| zip | `92705` |
| phone | `2031234567` |

**C. Phone rejection — NOT the issue**  
`2031234567` passes `is_valid_customer_phone`.

**D. Phase state hydration — NOT the issue**  
S1 sent successfully; case had attachments + channel binding on Postgres row.

---

## Fix (local, not deployed)

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/slice.py` | `get_case_for_read` instead of `get_case_by_id`; `resolve_add_car_case_for_phase2` |
| `services/fiqa_api/wecom/add_vehicle_phase2.py` | `get_case_for_read`; `find_phase2_eligible_add_car_case` fallback; zero-field format hint |
| `services/fiqa_api/wecom/reply.py` | `build_phase2_unrecognized_fields_reply()` |
| `tests/test_p19e1_phase2_routing_fix.py` | Regression for Postgres-only case + Andy message |
| `docs/p19e1_add_vehicle_case_state_machine_event_pipeline.md` | Mermaid state machine + event pipeline |

---

## Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19e1_phase2_routing_fix.py \
  tests/test_p19e1_add_vehicle_text_field_collection.py tests/test_wecom_slice.py -q
# PASS
```

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM | ❌ |
| Schema migration | ❌ |
| Cloud SQL / VPC / callback change | ❌ |
| Deploy | ❌ **STOP per sprint** |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Root cause identified | **GO** |
| Fix + tests local | **GO** |
| Redeploy + Andy retest | **HOLD** — deploy `c252369` + this fix next |

**Andy retest after deploy:**

1. `重新加车` → H5 三步 → S1  
2. `7月10号提车，zip. 92705。电话2031234567`  
3. Expect S2 + Workbench `ready_for_broker_review`
