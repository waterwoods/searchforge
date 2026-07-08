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

**Result:** PASS (no deploy performed)

---

## 11. Constraints honored

| Constraint | Status |
|------------|--------|
| No deploy | ✅ |
| No schema | ✅ |
| No OCR | ✅ |
| No Workbench checklist | ✅ |
| No skip persistence | ✅ |
| No WeCom direct image binding | ✅ |
| Add Vehicle H5 / Workbench unchanged | ✅ |

---

## 12. Known limitations

- Workbench evidence checklist not implemented
- Explicit `claim_attachment_slots` mutation / skip reason persistence deferred
- Direct WeCom image binding deferred
- No deploy yet — C1 H5 button is local/test only until next deploy sprint

---

## 13. Next recommended step

**P19H-3c-3** — Claim H5 upload slot status + Workbench Evidence Checklist  

**Alternative:** Deploy + phone/H5 smoke on production WeCom first to validate C1 button in live channel.

---

## 14. GO / HOLD

| Gate | Verdict |
|------|---------|
| Local tests + QA gate | **GO** for merge |
| Production deploy + phone/H5 smoke | **HOLD** until deploy sprint |

**STOP**
