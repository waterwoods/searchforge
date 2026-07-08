# P19H-3c-2 — Claim C1 WeCom H5 Upload Button

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Prerequisite:** P19H-3c-1 Claim H5 evidence foundation (`80170e0`)

---

## 1. Goal

When Claim accident basics complete and the system sends C1, give the customer a working WeCom H5 upload button (`上传事故照片`) that opens the Claim evidence pack at slot `customer_damage_photo`.

---

## 2. What was implemented

| Area | Change |
|------|--------|
| `reply.py` | C1 copy update; `build_claim_c1_h5_evidence_card_payload()` msgmenu view button |
| `claim_basics.py` | `_build_claim_c1_h5_response()` mints link via `mint_h5_claim_evidence_pack_link()`; returns `menu_payload` + masked URL |
| `slice.py` | Claim C1 dispatches msgmenu (same pathway as Add Vehicle H5 Start Card) |
| `workflow_scenario_simulator.py` | `expected_menu_button` validation; scenario steps assert upload button |
| `tests/test_p19h3c2_claim_c1_h5_button.py` | New acceptance tests |

---

## 3. C1 customer copy

```
【理赔资料 · 第 1 步完成 ✅】

事故基本信息已收到。

已记录：
时间：{accident_datetime}
地点：{accident_location}
描述：{accident_description}

请点击下面按钮上传事故照片。
请准备：
1. 您的车损伤照片
2. 对方车辆 / 车牌照片
3. 现场照片（可选）
```

**Tail (safety):**

```
这只是资料收集，不代表 claim 已正式提交。
陈总会人工确认。
```

Removed prior placeholder: “照片上传入口下一步会接入”.

---

## 4. H5 button / link behavior

| Field | Value |
|-------|-------|
| Button label | `上传事故照片` |
| Format | WeCom `msgmenu` view button (mirrors Add Vehicle H5 Start Card) |
| Mint helper | `mint_h5_claim_evidence_pack_link(case_id=...)` |
| Secondary click | `联系陈总` |
| Fallback | Plain text C1 when `case_id` missing or mint fails (no raw URL in head) |

---

## 5. Token validation

From C1 menu URL:

| Claim | Value |
|-------|-------|
| `lane` | `claim` |
| `flow` | `claim_evidence_pack` |
| `case_id` | active Claim case |
| First slot | `customer_damage_photo` |

---

## 6. H5 first-slot metadata

`GET /api/h5/tasks/{token}` after opening C1 link:

| Field | Expected |
|-------|----------|
| `lane` | `claim` |
| `flow` | `claim_evidence_pack` |
| `slot_key` | `customer_damage_photo` |
| `title` | `理赔资料 · 车损照片` |
| `safety_copy` | contains `不代表 claim 已正式提交` |
| `eligible_for_ocr` | `false` |

---

## 7. Scenario simulator extension

`ScenarioStep.expected_menu_button` validates msgmenu view button content.

Updated scenarios:

- `add_vehicle_to_claim_interrupt` — step `claim_basics_c1` expects `上传事故照片`
- `no_active_claim_basics` — step `claim_c1` expects `上传事故照片`

---

## 8. Add Vehicle regression

- Add Vehicle H5 Start Card unchanged (`add_car` lane, `开始上传资料` button)
- `tests/test_p19h3c1_claim_h5_evidence_foundation.py` Add Vehicle token regression PASS
- `tests/test_wecom_h5_vin_start_card.py` pattern preserved

---

## 9. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3c2_claim_c1_h5_button.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3c1_claim_h5_evidence_foundation.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3a_claim_workbench_visibility.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19j1c_workflow_scenario_simulator.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19j1a_routing_decision_log.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h21_claim_interrupt_lane_switch.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h2_simplified_claim_wecom_basics.py -q
PYTHONPATH=. python3 -m pytest tests -q -k "h5"
```

All PASS locally.

---

## 10. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Pre-deploy (2026-07-08):** PASS — production still on `29b57fe`  
**Post-deploy (2026-07-08):** PASS — `fiqa-api-00171-hbx` + `ui-smoky-beta`

---

## 11. Constraints honored

| Constraint | Status |
|------------|--------|
| No schema | ✅ |
| No OCR | ✅ |
| No Workbench checklist | ✅ |
| No skip persistence | ✅ |
| No WeCom direct image binding | ✅ |
| Add Vehicle H5 / Workbench unchanged | ✅ |
| Cloud SQL / VPC / NAT / secrets / callback unchanged | ✅ |

---

## 12. Known limitations

- Workbench evidence checklist not implemented
- Explicit `claim_attachment_slots` mutation / skip reason persistence deferred
- Direct WeCom image binding deferred
- Phone/H5 smoke on live WeCom pending Andy

---

## 13. Next recommended step

**P19H-3c-3** — Claim H5 upload slot status + Workbench Evidence Checklist

---

## Deploy Evidence

| Field | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Deployed commit | `c4c8b1e` (`c4c8b1e75`) |
| Prior production commit | `29b57fe` (backend + frontend both behind) |
| Backend revision | **`fiqa-api-00171-hbx`** |
| Backend URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Backend GIT_SHA | `c4c8b1e75` (`GET /version`) |
| Deploy script | `bash scripts/deploy_paid_pilot.sh` |
| Deploy time (UTC) | 2026-07-08 ~17:35 UTC (backend) |
| Frontend deploy | **Yes** — P19H-3c-1 H5 Claim UI (`80170e0`) not yet on stable alias |
| Frontend command | `vercel deploy --prod --yes` (from `ui/`) |
| Frontend deployment | `https://ui-c1527vah2-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Frontend deploy time (UTC) | 2026-07-08 ~17:42 UTC |
| `/health/live` | **200** |
| `/readyz` | **200** |
| Frontend build (local) | PASS (~21s) |
| Frontend build (Vercel) | PASS (~34s) |
| Backend targeted tests | PASS (P19H-3c-2 + regressions) |
| H5 tests | PASS |
| Scenario CLI | PASS (6/6) |
| Pre-deploy QA gate | PASS |
| Post-deploy QA gate | PASS |
| Workbench URL check | HTTP 200 — `https://ui-smoky-beta.vercel.app/workbench/document-intake` |
| Schema changed? | **No** |
| OCR? | **No** |
| Workbench checklist? | **No** |
| Skip persistence? | **No** |
| WeCom direct image binding? | **No** |
| WeCom callback / VPC / NAT / secrets | unchanged |

### Log check (post-deploy)

Revision `fiqa-api-00171-hbx` (~200 lines):

- **No** `claim_c1` / `h5_task_link` / `h5_task_token` / `h5_task_upload` / msgmenu import errors
- **No** Postgres read facade errors
- Expected optional warnings only: Qdrant unreachable, Redis optional, embedding warmup deferred, langgraph steward disabled

---

## Andy Phone/H5 Smoke Checklist

**Status:** Phone/H5 smoke **PENDING** (deploy complete; awaiting Andy on live WeCom)

### Smoke A — Claim path to C1 button

Prefer active Add Vehicle case, or start with no active case.

| Step | Input | Expected |
|------|-------|----------|
| 1 | `我要理赔` | Lane-switch prompt if Add Vehicle active; else Claim start |
| 2 | `开始理赔` | 【理赔资料收集】 + asks time/location/description |
| 3 | `今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门` | 【理赔资料 · 第 1 步完成 ✅】 + time/location/description + `请点击下面按钮上传事故照片` + button **上传事故照片**; no forbidden filing/fault/coverage language |

| Check | Result |
|-------|--------|
| C1 button visible | **PENDING** |
| Forbidden copy absent | **PENDING** |

### Smoke B — Click H5 button

Click **上传事故照片**.

| Check | Expected | Result |
|-------|----------|--------|
| H5 opens | No 401/403/404 | **PENDING** |
| Title | 理赔资料 · 车损照片 | **PENDING** |
| Instruction | Vehicle damage photo guidance | **PENDING** |
| Safety copy | 不代表 claim 已正式提交 | **PENDING** |
| First slot | `customer_damage_photo` | **PENDING** |
| Not Add Vehicle page | Not 开始上传资料 / add_car flow | **PENDING** |

### Smoke C — Optional upload test

Upload a test car damage photo if safe.

| Check | Expected | Result |
|-------|----------|--------|
| Upload succeeds | 200, no OCR promise | **PENDING** |
| Next slot | 对方车辆 / 车牌照片 | **PENDING** |

### Smoke D — Add Vehicle regression

| Step | Input | Expected | Result |
|------|-------|----------|--------|
| 1 | `重新加车` | Add Vehicle flow works; H5 button **开始上传资料** (`add_car` lane) | **PENDING** |

### Post-phone log check (optional)

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="fiqa-api" AND resource.labels.location="us-west1" AND textPayload:"wecom_routing_decision_v1"' \
  --project optimal-disk-472305-e2 \
  --limit 50 \
  --format='value(timestamp,textPayload)'
```

Look for: `active_claim_basics_collection` / `send_claim_c1` / `claim_c1`

---

## 14. GO / HOLD

| Gate | Verdict |
|------|---------|
| Deploy (backend + frontend) | **GO** |
| Post-deploy QA gate | **GO** |
| Phone/H5 smoke on live WeCom | **PENDING** — awaiting Andy |

**STOP**
