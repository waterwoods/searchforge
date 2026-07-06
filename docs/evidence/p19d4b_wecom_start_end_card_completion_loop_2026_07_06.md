# P19D-4B — WeCom Start / End Card Completion Loop

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Feature MVP (local PASS — no deploy)

---

## Recon doc commit

- `34a2642` — `docs: add P19D WeCom start end card UX recon`

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/reply.py` | Greeting menu + Start Card copy; `build_h5_photo_phase_complete_reply()` |
| `services/fiqa_api/wecom/h5_photo_end_card.py` | **New** — End Card send helper with dedup |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | Trigger End Card on `flow_complete` |
| `services/fiqa_api/inbox_triage/case_store.py` | `record_h5_photo_flow_end_card_status()` |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | H5 final page copy + checklist |
| `ui/src/pages/h5SingleSlotUpload.static.test.mjs` | Static contract tests |
| `tests/test_wecom_reply.py` | Greeting + End Card copy tests |
| `tests/test_wecom_h5_vin_start_card.py` | Start Card copy assertions |
| `tests/test_h5_add_vehicle_photo_flow.py` | End Card trigger + failure tests |
| `tests/test_wecom_h5_photo_end_card.py` | **New** — send/dedup unit tests |
| `tests/test_wecom_slice.py` | Greeting assertion update |

---

## Copy — before / after

### Greeting menu (before)

```
Thanks. I can help you review your request...
Buttons: Add Vehicle / 加车 | Claim / Accident / 事故理赔 | ...
```

### Greeting menu (after)

```
您好，请选择您要办理的事项：

也可以直接回复：
「我要加车」/「我要理赔」/「查保单」

Buttons: 【加车资料补充】| 【事故/理赔】| 【保单检视】| 【其他问题】

经纪人会审核，我们不会自动修改您的保单。
```

### Start Card (before)

- Head: 「开始补加车资料」+ long step explanation
- Button: 「开始补资料 / Start guided upload」

### Start Card (after)

```
加车资料收集

请点下方按钮，按顺序上传 3 张照片：
1. VIN 照片
2. 行驶证 / registration
3. 保险卡，可选

大约 2 分钟，不用填长表格。

Button: 开始上传照片
Secondary: 稍后 | 联系经纪人
```

### H5 final page

- Title: 照片已收到 ✅
- Checklist: VIN / 行驶证 / 保险卡 (or ○ 保险卡 — 可稍后补)
- 请点「返回微信」；回到聊天后会收到确认消息
- Text fields: 提车日期、停放 ZIP、联系电话
- Fallback: 若 10 秒内没有看到确认消息，请回复：已提交
- Broker gate: 陈总会人工确认，不会自动修改您的保单

### End Card (E2-photo)

```
【加车资料】照片已收到 ✅

我们已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片  (or ○ 保险卡 — 可稍后补)

还差 3 项，请在本聊天打字：
1. 提车日期
2. 停放 ZIP
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。
资料齐全后我们会再通知您。
```

---

## End Card trigger

- **When:** `ingest_h5_slot_upload()` or `skip_h5_flow_slot()` transitions to `flow_complete=true`
- **Where:** `_complete_flow_response()` → `try_send_h5_photo_flow_end_card(case_id)`
- **Not on:** GET `/api/h5/tasks/{token}` refresh

---

## Dedup strategy

- Case JSON: `h5_photo_flow_state.end_card_sent_at` + `end_card_send_status`
- Skip send if `end_card_sent_at` already set
- No schema migration

---

## Send failure behavior

- Upload/skip still returns HTTP 200 with `flow_complete=true`
- Response may include `end_card_sent=false` and `end_card_send_warning=confirmation_message_pending`
- Logs: `h5_flow_complete_notify_failed_v1` (no tokens/secrets/full external_userid)

---

## Tests / build

| Suite | Result |
|-------|--------|
| `test_h5_task_token.py` + `test_h5_single_slot_upload.py` + `test_h5_add_vehicle_photo_flow.py` + `test_wecom_h5_photo_end_card.py` | PASS |
| WeCom lane/slice/reply/active_case/h5_start_card | PASS |
| `test_wecom_upload_guardrail.py` + `test_wecom_media_intake.py` + `test_workbench_attachment_api.py` | PASS |
| `ui npm run build` | PASS |
| `h5SingleSlotUpload.static.test.mjs` | PASS |

---

## QA gate

- `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` — **PASS**
- Cloud SQL private DB; secret `fiqa-service-record-database-url-cloudsql-private`
- Neon not QA truth

---

## Guardrails confirmed

| Constraint | Status |
|------------|--------|
| OCR / LLM / vision | ❌ Not introduced |
| Schema migration | ❌ None |
| Cloud callback / VPC / NAT / Secret changes | ❌ None |
| Public GCS URL | ❌ None |
| Full external_userid in logs/evidence | ❌ Masked / omitted |
| Neon as QA truth | ❌ No |
| Deploy | ❌ **Not deployed** |

---

## Known limitations

- E1 full-material End Card (all text fields collected) — not in P19D-4B scope
- 「已提交」幂等重发 handler — V1.1
- End Card requires `wecom_open_kf_id` + `wecom_external_userid` on case (bound at WeCom intake)
- `WECOM_SLICE_SEND_REPLY=1` required for live send (same as Done Card)

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local tests + build | **GO** |
| QA gate (pre-deploy cloud) | **PASS** |
| Live phone smoke (Andy) | **HOLD** — await explicit deploy approval |

**Deploy:** HOLD — code committed locally; no push, no Cloud Run deploy in this loop.
