# P19D-4B.1 Fix — Restart Add Vehicle Creates New H5 Flow

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **FIX PASS (local)** · **Deploy HOLD** — await approval

---

## Andy reported issue (Scenario B FAIL)

After P19D-4B deploy (`fiqa-api-00157-zvt` / commit `54933ca`):

| Scenario | Result |
|----------|--------|
| A — completed photo flow + `我要加车` / 【加车资料补充】 | **PASS** — follow-up checklist, no new H5 Start Card |
| B — `重新加车` on completed case | **FAIL** — still returned old case「照片已收到」follow-up; no new flow |

---

## Root cause

1. **Draft merge ran before the H5 Start / follow-up path.** In `slice.py`, open add_car draft merge (lines ~537–586) intercepted high-confidence `add_car` text **before** `create_or_attach_draft_case_for_start_click()` + `_build_add_car_h5_start_menu()`. Customer got generic `build_slice_reply("add_car")` or merged into old case — never hit restart / completed-flow routing.

2. **Restart detector existed but was unreachable.** `wants_restart_add_car_photo_flow()` and `create_or_attach` restart branch in `54933ca` only ran on the Start Card / add_car H5 path — blocked by draft merge.

3. **Restart required `h5_photo_flow_is_complete`.** `create_or_attach_draft_case_for_start_click()` only forced a new case when flow was complete **and** restart — incomplete restart still attached to old draft.

---

## Fix summary

| Area | Change |
|------|--------|
| `h5_task_upload.py` | Expanded `is_explicit_add_car_restart()` phrases; kept `wants_restart_add_car_photo_flow` alias |
| `slice.py` | `_should_route_add_car_h5_start_instead_of_draft_merge()` — bypass draft merge for explicit restart OR completed photo flow + ordinary add_car |
| `active_case_bridge.py` | Any explicit restart → force new draft case (not only when flow complete) |
| `reply.py` | Optional `restart_intro` on Start Card head: 「好的，我们重新开始一组加车资料收集。」 |

---

## Restart phrases supported

**中文:** 重新加车 · 重新开始加车 · 重新上传加车资料 · 新加一辆车 · 再加一辆车 · 换一辆车 · 另加一辆车  

**English:** add another car · new vehicle · start over add vehicle · restart add vehicle · restart add car · new add car

---

## Case selection — before / after

| Customer message | Open completed add_car case | Before | After |
|------------------|----------------------------|--------|-------|
| `我要加车` | Yes | Draft merge → generic reply (local); follow-up only if H5 path reached | H5 path → attach existing → **follow-up checklist** |
| `重新加车` | Yes | Draft merge → attach old case → no new flow | **New draft case** → new v2 token → **Start Card Step 1 VIN** |
| `新加一辆车` / `再加一辆车` / `换一辆车` | Yes | Same as 重新加车 fail | New case + Start Card |
| VIN/ZIP/phone text on open draft | Yes | Draft merge (unchanged) | Draft merge (unchanged) |
| Incomplete draft + `我要加车` | No (incomplete) | Draft merge | Draft merge (unchanged) |

---

## Changed files

- `services/fiqa_api/inbox_triage/h5_task_upload.py`
- `services/fiqa_api/wecom/slice.py`
- `services/fiqa_api/wecom/active_case_bridge.py`
- `services/fiqa_api/wecom/reply.py`
- `tests/test_p19d4b1_restart_add_vehicle_flow.py` (new)
- `tests/test_p19d4b_completion_ux_fix.py`
- `tests/test_wecom_active_case.py`

---

## Tests / build

```text
PYTHONPATH=. python3 -m pytest tests/test_h5_task_token.py tests/test_h5_single_slot_upload.py tests/test_h5_add_vehicle_photo_flow.py tests/test_p19d4b_completion_ux_fix.py tests/test_p19d4b1_restart_add_vehicle_flow.py -q  → PASS
PYTHONPATH=. python3 -m pytest tests/test_wecom_minimal_lanes.py tests/test_wecom_intent.py tests/test_wecom_slice.py tests/test_wecom_active_case.py tests/test_wecom_reply.py tests/test_wecom_identity_b0_extractors.py -q  → PASS
PYTHONPATH=. python3 -m pytest tests/test_wecom_upload_guardrail.py tests/test_wecom_media_intake.py tests/test_workbench_attachment_api.py -q  → PASS
cd ui && npm run build  → PASS
```

---

## QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00157-zvt` — pre-deploy)

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM / vision extraction | ❌ Not introduced |
| Schema migration | ❌ |
| Cloud SQL / VPC / NAT / Secret / callback change | ❌ |
| Public GCS / public URL | ❌ Start Card tail still hides URL |
| Neon as QA truth | ❌ |
| Full external_userid in logs/docs | ❌ |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local fix + tests + build | **GO** |
| Deploy + Andy phone Scenario B smoke | **HOLD** — await approval |

**STOP** — no deploy in this sprint slice unless separately approved.
