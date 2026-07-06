# P19D-4B Deploy + Live WeCom Completion Card Smoke

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **DEPLOY PASS** · **Post-deploy cloud/API/UI smoke PASS** · **Live WeCom + phone End Card smoke HOLD (operator pending)**

---

## 1. Deployed commits (pushed)

| Commit | Message |
|--------|---------|
| `34a2642` | docs: add P19D WeCom start end card UX recon |
| `c57afbd` | feat: add WeCom completion card for H5 photo flow |

Pushed: `git push origin sprint/p16-trust-layer` (`f5b4d99..c57afbd`)

---

## 2. Pre-deploy tests

| Suite | Result |
|-------|--------|
| H5 token + single-slot + photo flow + end card | PASS |
| WeCom lane regression | PASS |
| P19A/B/D-1 regression | PASS |
| `npm run build` + H5 static test | PASS |
| QA gate (pre-deploy) | PASS |

---

## 3. Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00156-8mg`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `/health/live` | 200 OK |
| `/readyz` | 200 OK |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — **unchanged** |
| `H5_TASK_TOKEN_SECRET` | `fiqa-h5-task-token-secret:latest` — **unchanged** |
| `WECOM_SLICE_SEND_REPLY` | **`1`** — confirmed on revision |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — **unchanged** |
| Neon | Not used |
| WeCom callback | Unchanged |
| VPC/NAT | Unchanged |
| GIT_SHA on revision | `c57afbdf7` |

---

## 4. Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Production deployment | `https://ui-h3eor57zs-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/workbench/document-intake` | HTTP 200 |
| `/task/upload/:taskToken` | HTTP 200 (SPA route) |
| Build | PASS |

---

## 5. Post-deploy cloud H5 + End Card trigger smoke

Token minted with Cloud Run–matched `H5_TASK_TOKEN_SECRET` (value not recorded).

### Path A — full 3-step upload (`case_3fababa1fe6d`)

| Step | Result |
|------|--------|
| VIN upload | 200 → `next_slot=registration_photo` |
| Registration upload | 200 → `next_slot=insurance_card_photo` |
| Insurance upload | 200 → `flow_complete=true`, `end_card_sent=false` (no WeCom channel on API-only case) |
| GET refresh | `flow_complete=true` — **no duplicate upload/send** |
| Workbench attachments | 3 × `h5_task`: `vin_photo`, `registration_photo`, `insurance_card_photo` |
| Metadata | `ocr_status=not_started`, `broker_confirmed=false`, no `storage_uri` in API payload |
| Preview proxy | `GET .../attachments/att_920bbc930c07/preview` → **200** `image/jpeg` |

### End Card trigger (cloud logs)

```
h5_flow_complete_notify_skipped_v1 {"case_id": "case_3fababa1fe6d", "reason": "no_wecom_channel_binding"}
```

Expected for API-only smoke: case lacks `wecom_external_userid` + `wecom_open_kf_id`. **Live WeCom path binds channel on intake** — End Card send requires operator phone smoke.

---

## 6. H5 final page smoke (deployed alias, desktop browser)

Opened completed flow for `case_3fababa1fe6d` (token masked).

| Check | Result |
|-------|--------|
| Progress | 完成 3/3 |
| Headline | 照片已收到 ✅ |
| Checklist | ✓ VIN 照片 · ✓ 行驶证照片 · ✓ 保险卡照片 |
| Return WeChat | 请点「返回微信」；回到聊天后会收到确认消息 |
| Text fields | 提车日期 · 停放 ZIP · 联系电话 |
| Broker gate | 陈总会人工确认，不会自动修改您的保单 |
| Fallback | 若 10 秒内没有看到确认消息，请回复：已提交 |
| Buttons | 返回微信 · 稍后继续 |
| OCR language | None |

---

## 7. Live WeCom Start Card smoke (Andy phone)

**Status: PENDING operator**

Deployed copy (code truth on `c57afbd`):

**Greeting (unclear intent):**

- 您好，请选择您要办理的事项
- Buttons: 【加车资料补充】/【事故/理赔】/【保单检视】/【其他问题】
- 也可以直接回复：「我要加车」/「我要理赔」/「查保单」

**Add Vehicle Start Card (after 我要加车):**

- Head: 加车资料收集 · 3 张照片 · 大约 2 分钟
- Primary: **开始上传照片**
- Secondary: 稍后 · 联系经纪人

**Operator steps:**

1. WeCom/微信发送：**我要加车**
2. Confirm Start Card matches above (not legacy「开始补资料」)
3. Tap **开始上传照片** → H5 opens on `ui-smoky-beta.vercel.app/task/upload/h5t1.…`

---

## 8. Live phone H5 + End Card smoke (Andy phone)

**Status: PENDING operator**

Expected after 3 uploads or skip insurance:

1. H5 final page matches §6
2. Tap **返回微信**
3. Within ~10s receive End Card:

```
【加车资料】照片已收到 ✅
我们已收到： ✓ VIN 照片 · ✓ 行驶证照片 · ✓/○ 保险卡
还差 3 项：提车日期 · 停放 ZIP · 联系电话
陈总会人工查看并确认，不会自动修改您的保单。
```

4. Refresh H5 final page → **no second End Card**
5. Reply when done (e.g. `4B live done`) with path: 3 uploads vs skip insurance

**Cloud logs to watch:** `h5_flow_complete_notify_sent_v1` or `h5_flow_complete_notify_failed_v1`

---

## 9. Workbench verification

**Automated (API):** `case_3fababa1fe6d` — 3 H5 attachments, preview 200, no `storage_uri` in API JSON.

**Manual UI:** https://ui-smoky-beta.vercel.app/workbench/document-intake → case 赵先生 / `case_3fababa1fe6d`

- VIN / registration / insurance slots
- Source: H5 Task
- Preview via backend proxy
- No public GCS URL · no full external_userid

---

## 10. Logs / security check

| Check | Result |
|-------|--------|
| Token secret printed | No |
| Access token printed | No |
| DB secret printed | No |
| Full external_userid in logs | No |
| Image binary in logs | No |

---

## 11. QA gate (post-deploy)

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00156-8mg`)

---

## 12. Guardrails

| Constraint | Status |
|------------|--------|
| OCR / LLM | ❌ Not introduced |
| Schema migration | ❌ None |
| Cloud callback / VPC / NAT / Secret changes | ❌ None (deploy only) |
| Public GCS URL | ❌ None |
| Full external_userid in evidence | ❌ Omitted |
| Neon | ❌ Not QA truth |

---

## 13. Known limitations

- API-only cloud smoke cannot deliver WeCom End Card (needs `wecom_open_kf_id` from live WeCom intake)
- E1 full-material End Card — out of scope
- 「已提交」幂等重发 — V1.1

---

## 14. GO / HOLD

| Gate | Verdict |
|------|---------|
| Deploy + cloud/API/UI smoke | **GO** |
| Andy live WeCom Start + End Card | **HOLD** — operator phone smoke pending |
| Next loop (E1 / OCR / 小程序) | **HOLD** |

**Operator:** please run §7–8 on phone and reply `4B live done` with insurance uploaded vs skipped.
