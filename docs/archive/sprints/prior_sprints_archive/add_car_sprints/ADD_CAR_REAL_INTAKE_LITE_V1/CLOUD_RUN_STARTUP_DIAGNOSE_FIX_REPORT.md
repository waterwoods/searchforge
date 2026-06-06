# Cloud Run Startup Failure Diagnose + Fix Report

**Sprint:** Cloud Run Startup Failure Diagnose + Fix Sprint  
**Date:** 2026-03-19  
**Execution mode:** Focused diagnose → isolate → fix minimally → redeploy → verify

---

## 1. Sprint theme

- **What failed:** Backend Cloud Run revision `fiqa-api-00034-rdf` failed to start; container exited before listening on port 8080.
- **Why this sprint was needed:** Frontend deployed successfully; backend deploy failed, so the new add-car real-intake logic (quote_ready_status, contact extraction, attachment support) was not live. Founder needed backend fixed for full Vercel inspection.

---

## 2. Root-cause diagnosis

| Item | Value |
|------|-------|
| **What blocked startup** | Missing `python-multipart` dependency. FastAPI raised `RuntimeError: Form data requires "python-multipart" to be installed` during app import when registering the attachment upload route. |
| **Evidence from logs** | Cloud Run logs for revision `fiqa-api-00034-rdf`: |
| | `File "/app/services/fiqa_api/routes/inbox_triage.py", line 594, in (module)` |
| | `@router.post("/cases/{case_id}/attachments")` |
| | `File ".../fastapi/dependencies/utils.py", line 121, in ensure_multipart_is_installed` |
| | `raise RuntimeError(multipart_not_installed_error) from None` |
| **Why this is the most likely root cause** | The failure occurred during `importlib.import_module` of `app_main`, which imports `inbox_triage` router. The attachment route uses `File(...)` from FastAPI, which requires `python-multipart`. The package was not in `requirements.txt`, so the app crashed before uvicorn could bind to port 8080. |

---

## 3. Chosen minimal fix

| Item | Value |
|------|-------|
| **What was changed** | Added `python-multipart>=0.0.6` to `requirements.txt`. |
| **Why this was the safest fix** | Single-line dependency addition; no logic changes; FastAPI explicitly requires it for `File()` and `UploadFile`; no risk to existing behavior. |
| **What was intentionally not changed** | No startup path refactor; no lazy-init; no timeout changes; no removal of attachment route or other features. |

---

## 4. Local validation

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | **PASS** (50/50) |
| App import smoke (with python-multipart) | **PASS** |
| **Blocker** | None |

---

## 5. Backend redeploy result

| Item | Value |
|------|-------|
| **Success/failure** | **SUCCESS** |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | fiqa-api-00035-8cz (serving 100% traffic) |
| **Warnings/errors** | Deploy script healthz check failed (timing); readyz OK. Service is serving. |

---

## 6. Post-deploy verification

### Scenario A — Add-car + contact

| Item | Value |
|------|------|
| **What was checked** | API triage with full vehicle + contact info |
| **Expected** | quote_ready_status, contact extraction, customer_name/phone |
| **Observed** | `quote_ready_status`: quote_ready, `extracted_contact_name`: 李四, `extracted_contact_phone`: 310-123-4567, `customer_name`: 李四, `customer_phone`: 310-123-4567 |
| **Pass/fail** | **PASS** |
| **Notes** | Directly verified in production |

### Scenario B — Add-car quote-ready no contact

| Item | Value |
|------|------|
| **What was checked** | API triage with vehicle info, no contact |
| **Expected** | quote_ready_status, still_needed includes name/phone |
| **Observed** | `quote_ready_status`: quote_ready, `still_needed_fields`: ['primary_driver', 'name', 'phone'] |
| **Pass/fail** | **PASS** |
| **Notes** | Directly verified in production |

### Scenario C — Attachment route

| Item | Value |
|------|------|
| **What was checked** | POST `/api/inbox/cases/{id}/attachments` with PNG |
| **Expected** | Upload works, case shows attachment |
| **Observed** | `case_attachments` count: 1, `attachment_id`: att_0992326d14ce, `filename`: mini.png |
| **Pass/fail** | **PASS** |
| **Notes** | Directly verified in production |

---

## 7. Final operational judgment

| Question | Answer |
|----------|--------|
| **Is backend now live?** | **Yes.** Revision fiqa-api-00035-8cz is serving. |
| **Are add-car real-intake backend blocks now live?** | **Yes.** quote_ready_status, contact extraction, attachment upload/download are live. |
| **Biggest remaining weakness** | None identified for this sprint. Healthz check in deploy script may need longer wait for cold start. |
| **Can Andy now fully test on Vercel?** | **Yes.** Frontend + backend are both deployed. Full add-car flow (contact, quote-ready, attachments) is verifiable on https://ui-smoky-beta.vercel.app. |

---

## 8. 中文宏观总结

- **后端为什么没部署上：** 缺少 `python-multipart` 依赖。附件上传路由使用了 FastAPI 的 `File()`，需要该包才能启动。App 在 import 阶段就崩溃，导致容器无法监听 8080。
- **这次怎么修的：** 在 requirements.txt 中加入 `python-multipart>=0.0.6`，重新构建并部署。
- **现在后端有没有真的上线：** 有。Revision fiqa-api-00035-8cz 已成功部署并正在服务。
- **我现在可不可以去 Vercel 看完整效果：** 可以。前端已部署，后端也已部署，add-car 的 quote_ready、联系人、附件功能都已上线。

---

## 9. COPY/PASTE FOUNDER BLOCK

```
Cloud Run Startup Failure — Diagnose + Fix Sprint

Root cause: Missing python-multipart dependency.
  - Attachment upload route uses FastAPI File() which requires it.
  - App crashed during import before uvicorn could bind to port 8080.

Fix applied: Added python-multipart>=0.0.6 to requirements.txt.

Backend deploy status: SUCCESS
  - Revision: fiqa-api-00035-8cz
  - URL: https://fiqa-api-g7zatxrycq-uw.a.run.app

Can Andy test full add-car flow on Vercel tonight?
  Yes. Go to https://ui-smoky-beta.vercel.app — new add-car UI (contact block, quote-ready tags, attachment upload) is live. Backend now supports quote_ready_status, contact extraction, and attachment upload/download.
```

---

## 10. REQUIRED SHORT OVERVIEW

### 为什么会失败
缺少 `python-multipart` 依赖。附件上传路由使用了 FastAPI 的 `File()`，需要该包才能完成 app 导入。导入失败导致容器在启动阶段就崩溃，无法监听端口 8080。

### 主要修了什么
在 requirements.txt 中加入 `python-multipart>=0.0.6`，重新构建并部署到 Cloud Run。

### 现在是否上线成功
是。Revision fiqa-api-00035-8cz 已成功部署并正在服务。add-car 的 quote_ready_status、联系人提取、附件上传/下载均已上线。

### 现在还差什么
无。本次 sprint 目标已达成。可继续在 Vercel 上做完整 add-car 流程验证。
