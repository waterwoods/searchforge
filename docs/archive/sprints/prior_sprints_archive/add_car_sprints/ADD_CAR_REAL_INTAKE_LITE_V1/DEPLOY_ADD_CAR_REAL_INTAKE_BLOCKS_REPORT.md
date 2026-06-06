# Deploy Add-Car Real Intake Blocks to Production Report

**Sprint:** Deploy Add-Car Real Intake Blocks to Production  
**Date:** 2026-03-19  
**Execution mode:** Focused validate → deploy → verify → summarize

---

## 1. Sprint theme

- **What was deployed:** Add-Car Identity + Contact Lite, Add-Car Attachment-Ready Lite (frontend only; backend deploy failed)
- **Why now:** Founder wants to inspect add-car improvements on Vercel tonight — contact identity, quote-ready status, attachment support, workbench visibility

---

## 2. Pre-deploy validation

### Files inspected

| Area | File | Confirmed |
|------|------|-----------|
| Backend | `services/fiqa_api/inbox_triage/triage.py` | `quote_ready_status`, `extracted_contact_name/phone`, `_add_car_quote_ready_status`, `_add_car_structured_fields` |
| Backend | `services/fiqa_api/inbox_triage/case_store.py` | `customer_name`, `customer_phone`, `case_attachments`, `add_attachment_to_case`, `get_attachment_file_path` |
| Backend | `services/fiqa_api/routes/inbox_triage.py` | `POST /cases/{id}/attachments`, `GET /cases/{id}/attachments/{att_id}` |
| Frontend | `ui/src/pages/UnifiedIntakePage.tsx` | Contact block (Name/Phone), `quote_ready_status` tags, attachment list + upload UI |
| Frontend | `ui/src/api/inboxTriage.ts` | `quote_ready_status`, `customer_name`, `customer_phone`, `case_attachments`, `uploadCaseAttachment`, `getAttachmentDownloadUrl` |

### Test/build results

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (64/64 scenarios, 50 multi-turn, 27 adversarial, 24 complex, 27 sim assistant, 8 broker stress, 12 handoff timing) |
| `cd ui && npm run build` | **PASS** (built in 20.77s) |

### Blocker

**None.** All pre-deploy validation passed.

---

## 3. Backend deploy result

| Item | Value |
|------|-------|
| **Success/failure** | **FAILED** |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app (previous revision still serving) |
| **Revision** | New revision `fiqa-api-00034-rdf` failed to start |
| **Warnings/errors** | Container failed to start and listen on PORT=8080 within allocated timeout. Likely cause: startup time (embedding warming, Qdrant connection) exceeds Cloud Run startup timeout. |
| **Build** | Image built successfully (`gcr.io/optimal-disk-472305-e2/fiqa-api:latest`) |
| **Deploy** | `Creating Revision` step failed |

**Logs:** https://console.cloud.google.com/logs/viewer?project=optimal-disk-472305-e2&resource=cloud_run_revision/service_name/fiqa-api/revision_name/fiqa-api-00034-rdf

---

## 4. Frontend deploy result

| Item | Value |
|------|-------|
| **Success/failure** | **SUCCESS** |
| **Production URL** | https://ui-5ftct5lnd-andys-projects-1f411b73.vercel.app |
| **Alias** | https://ui-smoky-beta.vercel.app |
| **Warnings/errors** | Chunk size warning (>500 kB) — non-blocking |

---

## 5. Post-deploy verification

### Scenario A — Add-car + quote-ready + contact

| Item | Value |
|------|------|
| **What was checked** | API triage with full vehicle + contact info |
| **Expected** | `quote_ready_status`, contact block with name + phone |
| **Observed** | `quote_ready_status`: None, `extracted_contact_name/phone`: None, `customer_name/phone`: empty |
| **Pass/fail** | **FAIL** |
| **Notes** | Production backend is previous revision; new add-car blocks not deployed |

### Scenario B — Add-car quote-ready but contact missing

| Item | Value |
|------|------|
| **What was checked** | API triage with vehicle info, no contact |
| **Expected** | `quote_ready` or `almost_ready`, contact block shows Name needed / Phone needed |
| **Observed** | `quote_ready_status`: None |
| **Pass/fail** | **FAIL** |
| **Notes** | Same as A — backend has old code |

### Scenario C — Add-car + attachment upload

| Item | Value |
|------|------|
| **What was checked** | POST `/api/inbox/cases/{id}/attachments` |
| **Expected** | Upload works, case shows attachment list |
| **Observed** | 404 (case not found or route not in production) |
| **Pass/fail** | **Blocked / not verifiable** |
| **Notes** | Cannot distinguish route-missing vs case-missing; backend deploy failed so attachment routes may not be in production |

### Scenario D — Add-car + side question

| Item | Value |
|------|------|
| **What was checked** | Multi-turn: add-car + "garaging proof 是什么？" |
| **Expected** | Answer clarification, handoff reasonable, case structured |
| **Observed** | `handoff_ready`: True, reply includes garaging explanation + add-car handoff |
| **Pass/fail** | **PASS** (inferred from API) |
| **Notes** | Directly verified in production; mixed-intent handling works |

---

## 6. Final operational judgment

| Question | Answer |
|----------|--------|
| **Did backend deploy succeed?** | **No.** New revision failed to start. |
| **Did frontend deploy succeed?** | **Yes.** |
| **Are the latest add-car real-intake blocks now live?** | **Frontend: Yes.** Backend: **No** — production backend is previous revision. |
| **Which scenarios fully passed?** | Scenario D (add-car + side question). A, B, C failed or blocked due to backend not having new code. |
| **What remains the biggest add-car/productization weakness?** | Backend deploy reliability — Cloud Run startup timeout prevents new revision from going live. Add-car improvements (quote_ready_status, contact extraction, attachments) exist in code but are not in production backend. |
| **Can Andy now go to Vercel and inspect tonight?** | **Yes for frontend.** The new UI (contact block, quote-ready tags, attachment UI) is live at https://ui-smoky-beta.vercel.app. The backend will not populate these fields until a successful backend redeploy. |

---

## 7. 中文宏观总结

- **为什么现在要部署：** 创始人今晚要在 Vercel 上检查 add-car 真感增强（联系人、报价就绪、附件支持）。
- **哪些 add-car 真感增强已经上线：** 前端 UI 已上线（联系人区块、quote-ready 标签、附件上传/列表）。后端部署失败，quote_ready_status、contact 提取、attachment 路由未上线。
- **哪些验证通过了：** 本地 guardrail 全过；前端构建和 Vercel 部署成功；生产环境 Scenario D（加车+侧问题）通过；Scenario A/B/C 因后端未更新而失败。
- **现在我可不可以去 Vercel 看：** 可以。前端已部署，可查看新 UI。但后端未更新，联系人、报价就绪、附件数据不会显示。

---

## 8. COPY/PASTE FOUNDER BLOCK

```
Deploy Add-Car Real Intake Blocks — Sprint Summary

Backend deploy: FAILED
  - New Cloud Run revision failed to start (timeout).
  - Production backend is still previous revision.
  - quote_ready_status, contact extraction, attachment support: NOT in production.

Frontend deploy: SUCCESS
  - Production: https://ui-smoky-beta.vercel.app
  - New UI (contact block, quote-ready tags, attachment UI) is live.

Add-car verification:
  - Scenario D (add-car + side question): PASS.
  - Scenarios A/B/C: FAIL — backend lacks new code.

Biggest remaining weakness:
  - Backend startup timeout on Cloud Run blocks new revision.
  - Need to extend startup timeout or optimize cold start (embedding warming, Qdrant).

Can Andy inspect tonight?
  - Yes. Go to https://ui-smoky-beta.vercel.app — new UI is there.
  - Backend will not populate contact/quote-ready/attachments until backend redeploy succeeds.
  - For full add-car experience, run local: bash scripts/run_demo_local.sh
```

---

## 9. REQUIRED SHORT OVERVIEW

### 为什么做这件事
将 Add-Car Identity + Contact Lite 和 Add-Car Attachment-Ready Lite 部署到生产，让创始人能在 Vercel 上检查加车流程的商业化程度。

### 主要用了什么方法/技术
- 本地 guardrail 验证（scenario pack、multi-turn、adversarial、state backbone）
- Cloud Run 部署（gcloud builds submit + gcloud run deploy）
- Vercel 生产部署（vercel --prod）
- 生产 API 验证（curl 调用 triage 和 attachment 路由）

### 这轮最大的提升
- 前端成功部署，新 UI（联系人区块、quote-ready 标签、附件上传）已在 Vercel 生产环境可见。
- 本地验证全部通过，代码质量无问题。

### 现在还差什么
- 后端部署失败，需解决 Cloud Run 启动超时（延长 timeout 或优化冷启动）。
- 生产后端未包含 quote_ready_status、contact 提取、attachment 路由。
- 需成功 redeploy 后端后，再验证 Scenarios A/B/C。
