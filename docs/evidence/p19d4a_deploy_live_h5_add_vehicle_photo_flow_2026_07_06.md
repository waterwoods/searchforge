# P19D-4A Deploy + Live H5 Add Vehicle Photo Flow Smoke

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **DEPLOY PASS** · **Post-deploy cloud/API/UI smoke PASS** · **Live WeCom + phone smoke HOLD (operator pending)**

---

## 1. Deployed commits (pushed)

| Commit | Message |
|--------|---------|
| `66c6500` | docs: add P19D guided workflow best practice recon |
| `43108bf` | feat: add H5 add vehicle photo flow |

Pushed: `git push origin sprint/p16-trust-layer` (58f4b4a..43108bf)

---

## 2. Pre-deploy tests

| Suite | Result |
|-------|--------|
| H5 token + single-slot + photo flow | PASS |
| P19A/B/D-1 regression | PASS |
| WeCom lane regression | PASS |
| `npm run build` | PASS |
| H5 + attachment static tests | PASS |
| QA gate (pre-deploy) | PASS |

---

## 3. Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00155-fwc`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `/health/live` | 200 OK |
| `/readyz` | 200 OK |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — **unchanged** |
| `H5_TASK_TOKEN_SECRET` | `fiqa-h5-task-token-secret:latest` — **unchanged** |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — **unchanged** |
| Neon | Not used |
| WeCom callback | Unchanged |
| VPC/NAT | Unchanged |

---

## 4. Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Production deployment | `https://ui-4f6ao7h1k-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/workbench/document-intake` | HTTP 200 |
| `/task/upload/:taskToken` | HTTP 200 (SPA route) |
| Build | PASS |

---

## 5. Post-deploy H5 flow API smoke (cloud)

Token minted with Cloud Run–matched `H5_TASK_TOKEN_SECRET` (value not recorded).

### Path A — full 3-step upload (`case_65e8f926cb90`)

| Step | Result |
|------|--------|
| GET task | `flow=add_vehicle_photo_flow`, `current_step=vin_photo`, `step_total=3` |
| VIN upload | 200 → `next_slot=registration_photo` |
| Registration upload | 200 → `next_slot=insurance_card_photo` |
| Insurance upload | 200 → `flow_complete=true`, message asks return WeCom for date/ZIP/phone |
| Workbench attachments | 3 × `h5_task`: `vin_photo`, `registration_photo`, `insurance_card_photo` |
| Metadata | `promoted`, `guardrail_status=accepted`, `eligible_for_ocr=true`, `ocr_status=not_started`, `broker_confirmed=false` |
| Preview proxy | `GET .../attachments/att_9432e31ac6dd/preview` → **200** |

### Path B — skip insurance (`case_01dc1ba44b91`)

| Step | Result |
|------|--------|
| VIN + registration upload | 200 |
| Skip `insurance_card_photo` | 200 → `flow_complete=true`, `status=skipped` |
| Case `h5_photo_flow_state.skipped_slots` | includes `insurance_card_photo` |

### Negative (cloud)

| Check | Result |
|-------|--------|
| Wrong slot order | 400 `wrong_slot_order` |
| Tampered token | 403 |
| Local pytest regression | PASS (unchanged) |

---

## 6. H5 UI smoke (desktop browser, deployed alias)

Opened flow link for `case_3fababa1fe6d` (token masked in logs).

| Check | Result |
|-------|--------|
| Title | 加车资料补充 |
| Progress | 第 1 步 / 共 3 步 |
| Instruction | VIN 标签说明 |
| Upload button | 选择 / 拍摄照片 |
| OCR language | None observed |

---

## 7. Live WeCom Start Card smoke (Andy phone)

**Status: PENDING operator**

Expected operator steps:

1. From WeCom/微信 send: **我要加车**
2. Receive Start Card with button **开始补资料**
3. Copy should mention VIN / 行驶证 / 保险卡，每步 1 张
4. H5 link pattern: `https://ui-smoky-beta.vercel.app/task/upload/h5t1.…`
5. Token should be v2 `add_vehicle_photo_flow`

**Cloud Run logs at deploy time:** no `start_card_sent` / WeCom add_car callback observed yet (only automated API smoke).

**Operator:** please reply in chat when complete (e.g. `4A live done`) with path taken (3 uploads vs skip insurance).

---

## 8. Live phone H5 flow smoke (Andy phone)

**Status: PENDING operator**

Suggested non-sensitive test images: white paper labeled VIN TEST / REGISTRATION TEST / INSURANCE TEST.

Automated cloud API path above validates backend step transitions; phone UX confirmation still required from operator.

---

## 9. Workbench verification

**Automated (API):** `case_65e8f926cb90` shows 3 H5 attachments with correct slots and `preview_available=true`.

**Manual UI:** open https://ui-smoky-beta.vercel.app/workbench/document-intake → case `P19D1 Guardrail Smoke` / `case_65e8f926cb90` to confirm labels:

- VIN photo
- Registration photo
- Insurance card photo
- Source: H5 Task / Guided Upload

---

## 10. Logs / security check

Scanned recent Cloud Run logs (`limit 500`):

| Check | Result |
|-------|--------|
| Token secret printed | No |
| Access token printed | No |
| DB secret printed | No |
| Image binary printed | No |
| Public GCS URL | No |
| Full external_userid | No |
| Unexpected 500 on H5 smoke | No |

**Known risk:** request access logs include full H5 task token in URL path (pre-existing pattern). Evidence uses masked tokens only.

---

## 11. QA gate (post-deploy)

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: PASS** — revision `fiqa-api-00155-fwc`, Cloud SQL aligned, demo cases present.

---

## 12. Explicit non-goals

| Item | Status |
|------|--------|
| OCR / LLM | ❌ Not introduced |
| Schema migration | ❌ |
| Public GCS URL | ❌ |
| Neon | ❌ |
| Cloud SQL / VPC / NAT / Secret / callback changes | ❌ |

---

## 13. Known limitations

- Skip state has no dedicated Workbench UI
- Full H5 tokens appear in Cloud Run request logs (mask in operator comms)
- Live WeCom + phone confirmation pending Andy

---

## 14. GO / HOLD

| Gate | Verdict |
|------|---------|
| Deploy + cloud/API/UI smoke | **GO** |
| Live WeCom + phone E2E | **HOLD** — awaiting operator `我要加车` → H5 → Workbench confirm |
| Next loop (text fields in WeCom / OCR) | **HOLD** — out of P19D-4A scope |

---

*No token secrets, full tokens, external_userid, or image content in this document.*
