# P19D-3 — WeCom Start Card → H5 VIN Task Link Integration

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Add Vehicle WeCom entry → H5 single-slot VIN upload link only. STOP before registration / insurance card / OCR / multi-step chain.

---

## 1. Commits

| Hash | Message |
|------|---------|
| `f7531cb` | feat: link WeCom add vehicle start card to H5 VIN task |
| *(this doc)* | docs: add WeCom to H5 VIN task smoke evidence |

Prior P19D-2 evidence: `4a1b93e`

---

## 2. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/h5_task_link.py` | `mint_h5_task_link`, `h5_task_frontend_base`, URL masking |
| `services/fiqa_api/wecom/reply.py` | `build_h5_vin_start_card_payload` (view button + copy) |
| `services/fiqa_api/wecom/slice.py` | add_car + start click → draft case + H5 Start Card |
| `scripts/generate_h5_task_link.py` | Reuse `mint_h5_task_link` |
| `tests/test_h5_task_link.py` | Link helper tests |
| `tests/test_wecom_h5_vin_start_card.py` | WeCom → H5 integration tests |
| `tests/test_wecom_active_case.py` | Updated B0 expectations (draft on add_car text) |
| `tests/test_wecom_minimal_lanes.py` | Updated add_car start card expectation |

**No frontend changes.** H5 page from P19D-2 unchanged.

---

## 3. Deploy

| Item | Value |
|------|-------|
| Backend service | `fiqa-api` @ `us-west1` |
| Backend revision | `fiqa-api-00153-h4p` |
| Frontend alias | `https://ui-smoky-beta.vercel.app` (no redeploy) |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` (unchanged) |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC (unchanged) |
| `H5_TASK_TOKEN_SECRET` | Secret Manager `fiqa-h5-task-token-secret` (unchanged) |
| H5 link base URL | Code default `https://ui-smoky-beta.vercel.app` via `h5_task_frontend_base()`; Cloud Run may also set `UNIFIED_INTAKE_FRONTEND_ORIGIN` |

---

## 4. Product behavior (doctrine)

| Surface | Role |
|---------|------|
| WeCom chat | Entry, notification, human comms |
| H5 `/task/upload/:token` | Current step · one evidence · preview confirm |
| Workbench | Broker review |

**This sprint:** Add Vehicle text → H5 VIN link only. No multi-image upload. No OCR. No registration step.

---

## 5. Customer copy (WeCom Start Card)

- **Title:** 开始补加车资料
- **Body:** 为了避免资料放错，我们会一步一步收集。第一步只需要拍 1 张 VIN 照片。
- **Button:** 开始上传 VIN 照片 (WeCom `msgmenu` `view` → H5 URL)
- **Fallback:** tail text with copy-paste link if button fails

Prohibited wording not used: upload all documents, multi-image, OCR, VIN recognized, policy changed.

---

## 6. Local / simulated smoke (pre-deploy)

Input: `我要加车`

| Check | Result |
|-------|--------|
| add_car draft case created | PASS (`case_id` set) |
| Start Card / H5 link in menu | PASS (`/task/upload/h5t1.…`) |
| `GET /api/h5/tasks/{token}` | PASS 200 |
| `task_label` | 请拍 VIN 照片 |
| `slot` | `vin_photo` |
| `lane` | `add_car` |
| No OCR / bulk wording | PASS |

Other lanes (no H5 VIN link):

| Input | Lane | H5 link |
|-------|------|---------|
| 你好 | unclear / menu | No |
| 陈总，我保险又涨了… | policy_review | No |
| 我撞车了 | claim_lite | No |
| DMV说我没保险 | coverage_risk | No |

---

## 7. Tests

```
PYTHONPATH=. python3 -m pytest tests/test_h5_task_token.py tests/test_h5_task_link.py tests/test_h5_single_slot_upload.py -q  → PASS
PYTHONPATH=. python3 -m pytest tests/test_wecom_upload_guardrail.py tests/test_wecom_media_intake.py tests/test_workbench_attachment_api.py -q  → PASS
PYTHONPATH=. python3 -m pytest tests/test_wecom_minimal_lanes.py tests/test_wecom_intent.py tests/test_wecom_slice.py tests/test_wecom_active_case.py tests/test_wecom_reply.py tests/test_wecom_identity_b0_extractors.py tests/test_wecom_h5_vin_start_card.py -q  → PASS
```

QA gate: `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00153-h4p`)

---

## 8. Live WeCom phone smoke — **PENDING Andy**

**Action for Andy:** From WeCom/微信 send:

```
我要加车
```

**Expected customer reply:**

- Start Card or equivalent message
- Copy includes “开始上传 VIN 照片” or equivalent
- H5 task link/button present
- States first step is one VIN photo only

**Then on phone:** tap link → H5 loads → upload **one** non-sensitive test image (not a real VIN) → submit.

**Workbench verify:**

- Selected/new `add_car` case shows H5 Task / VIN photo
- `source=h5_task`, `slot_assignment=vin_photo`
- Preview works

| Field | Value |
|-------|-------|
| Live message time | _pending_ |
| Generated case id | _pending_ |
| H5 link (masked) | _pending_ `https://ui-smoky-beta.vercel.app/task/upload/h5t1.…` |
| Phone upload result | _pending_ |
| Workbench preview | _pending_ |

---

## 9. Safety checklist

| Item | Status |
|------|--------|
| OCR / LLM vision | **No** |
| Schema migration | **No** |
| Public GCS URL | **No** |
| Full `external_userid` in token/logs | **No** (8-char `user_ref` only) |
| Full token in logs | **No** (masked `h5t1.…`) |
| Token secret printed | **No** |
| Neon as QA truth | **No** |
| Cloud SQL / VPC / NAT / callback changed | **No** |
| P19A media intake broken | **No** (tests pass) |
| P19B Workbench preview broken | **No** (tests pass) |
| P19D-1 guardrail broken | **No** (tests pass) |
| P19D-2 standalone H5 page broken | **No** (no frontend change) |

---

## 10. Known limitations

- WeCom `msgmenu` `view` button depends on WeChat/WeCom client supporting external H5 links; tail text provides copy-paste fallback.
- Draft case is created on first high-confidence `add_car` text (needed to bind token to case). Legacy B0.1 “no case until Start click” superseded for H5 binding.
- Repeat `add_car` messages while draft open merge into draft (no second Start Card).
- `H5_TASK_FRONTEND_BASE_URL` optional; defaults to `https://ui-smoky-beta.vercel.app` when unset.

---

## 11. GO / HOLD — next step

| Step | Verdict |
|------|---------|
| P19D-3 WeCom → H5 VIN link (code + deploy + unit tests) | **GO** |
| P19D-3 live WeCom phone smoke | **HOLD** until Andy completes §8 |
| P19D-2.5 registration step | **HOLD** — out of scope |

**STOP** before registration / insurance card / full H5 chain / OCR / 小程序.
