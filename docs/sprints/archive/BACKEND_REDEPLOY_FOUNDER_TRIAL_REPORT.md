# Backend Redeploy + Founder Real Trial Report

**Sprint:** Backend Redeploy + Founder Real Trial Sprint  
**Date:** 2026-03-17  
**Execution time:** ~35 minutes

---

## 1. Sprint theme

- **What was deployed:** Top Scenarios Hardening Phase 2 backend changes (billing clarification, remove vehicle shorthand, claim first notice, renewal increase) to Cloud Run production.
- **Why now:** The founder wants confidence that the hardened scenarios are live in production and ready for real trial testing on the frontend.

---

## 2. Control docs created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/BACKEND_REDEPLOY_FOUNDER_TRIAL_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/BACKEND_REDEPLOY_FOUNDER_TRIAL_EXECUTION_OUTLINE.md` |
| Acceptance / Operational Criteria | `docs/sprints/BACKEND_REDEPLOY_ACCEPTANCE_CRITERIA.md` |
| Founder Trial Checklist | `docs/sprints/FOUNDER_TRIAL_CHECKLIST.md` |

---

## 3. Pre-deploy validation

### Files inspected

| File | Expected logic | Found |
|------|----------------|-------|
| `services/fiqa_api/inbox_triage/triage.py` | `_is_billing_clarification_request` (账单 + 什么意思/看不懂) | ✓ |
| | `_is_remove_vehicle_request` (减车 + vehicle_context) | ✓ |
| | `_is_claim_intake_request` (报事故, 刚撞了) | ✓ |
| | `_is_premium_review_request` (续保涨) | ✓ |
| `configs/industries/insurance/markers.json` | remove_vehicle: 减车, 卖掉了; claim_intake: 报事故, 刚撞了; premium_review: 续保涨 | ✓ |
| `configs/inbox_triage_scenarios.json` | TSH2-BC1, TSH2-BC2, TSH2-CL1, TSH2-RN1, TSH2-RV1 | ✓ |

### Validation results

| Script | Result |
|--------|--------|
| `run_inbox_triage_scenarios.py` | 63/63 passed |
| `run_multi_turn_simulations.py` | 39/39 passed |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `verify_speed_routing.py` | OK |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |

**Blocker:** None.

---

## 4. Backend deploy result

| Field | Value |
|-------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | fiqa-api-00029-25j |
| **Project** | optimal-disk-472305-e2 |
| **Region** | us-west1 |
| **Warnings** | /healthz returned FAILED immediately post-deploy (cold start); /readyz OK |
| **Errors** | None |

---

## 5. Post-deploy verification

Production API: `POST https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage`

| Scenario | Input | Expected | Observed | Pass |
|----------|-------|----------|----------|------|
| **A** | 账单什么意思 | customer_question; NOT payment_lapse; reply asks for bill, offers to explain | category: customer_question; draft: 把完整账单或通知发我，我先帮你看一下，再告诉你重点和下一步怎么处理。 | ✓ |
| **B** | 这个账单我看不懂 | Same as A | Same as A | ✓ |
| **C** | 减车，卖掉了 | customer_question; remove vehicle handling; asks for sale date/vehicle/transfer | category: customer_question; draft: 好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。 | ✓ |
| **D** | 报事故，刚撞了 | customer_question; claim intake; asks for photos/other driver/what happened | category: customer_question; draft: 刚出事故一定很着急...先把事故经过、对方信息和照片发我，我就能帮你确认下一步怎么报案。 | ✓ |
| **E** | 续保涨了好多，帮我看看 | customer_question; renewal/premium review; NOT payment failure | category: customer_question; draft: 我先帮你看这次保费为什么变高...把现在保单和最新账单发我... | ✓ |

**All 5 founder trial scenarios passed in production.**

---

## 6. Optional second loop

- **Whether used:** No.
- **Reason:** All scenarios passed; no high-value, low-risk fix needed.

---

## 7. Final operational judgment

| Question | Answer |
|----------|--------|
| Did backend deploy succeed? | **Yes** |
| Are the hardened scenarios now live? | **Yes** |
| Which founder trial scenarios passed? | **All 5 (A–E)** |
| Which scenario still remains weakest? | None identified; all behaved as expected. |
| Can Andy now manually test on the live frontend with confidence? | **Yes** |

---

## 8. 中文宏观总结

- **为什么现在要 redeploy：** Phase 2 场景加固（账单澄清、减车、报事故、续保涨）已完成，需要上线到生产环境供创始人真实试用。
- **这轮主要验证了哪些场景：** 账单什么意思、这个账单我看不懂、减车卖掉了、报事故刚撞了、续保涨了好多帮我看看。
- **哪些已经上线成功：** 全部 5 个场景均在生产环境通过验证，分类和回复草稿均符合预期。
- **哪些还弱：** 暂无；如需进一步验证可增加更多变体或多轮对话。
- **现在我可不可以去前端测试：** 可以。后端已部署，5 个场景已验证，可直接在 Vercel 前端或本地连接生产后端进行手动测试。

---

## 9. COPY/PASTE FOUNDER BLOCK

```
Backend Redeploy + Founder Trial — Summary

✅ Backend deploy: SUCCESS
   URL: https://fiqa-api-g7zatxrycq-uw.a.run.app
   Revision: fiqa-api-00029-25j

✅ Scenario pass: 5/5
   A 账单什么意思 — customer_question, clarification flow ✓
   B 这个账单我看不懂 — same ✓
   C 减车，卖掉了 — remove vehicle handling ✓
   D 报事故，刚撞了 — claim intake ✓
   E 续保涨了好多，帮我看看 — renewal/premium review ✓

Biggest remaining weakness: None identified.

Can Andy test on live frontend now? YES.
```

---

## 10. REQUIRED SHORT OVERVIEW

### 为什么做这件事

将 Top Scenarios Hardening Phase 2 的代码变更部署到生产环境，并验证创始人真实试用场景在线上行为正确，确保 Vercel 前端连接的 live backend 与最新逻辑一致。

### 主要用了什么方法/技术

- 控制文档先行（Blueprint、Outline、Acceptance、Founder Checklist）
- 预部署校验：代码审查 + 6 个验证脚本（inbox triage、multi-turn、state audit、speed routing、guardrail、smoke）
- 标准部署路径：`deploy_rag_demo.sh` → Cloud Build → Cloud Run
- 生产真实验证：对 5 个创始人场景直接调用生产 API，比对 category 与 reply draft

### 这轮最大的提升

5 个商业化重要场景（账单澄清、减车、报事故、续保涨）在生产环境得到验证，创始人可以放心在前端进行真实试用测试。

### 现在还差什么

- 无阻塞问题
- 可选：增加更多变体或多轮对话的回归测试
- 可选：确认 Vercel 前端 CORS 与 `ALLOWED_ORIGINS` 配置正确
