# Top Scenarios Hardening Phase 2 Report

**Sprint:** Top Scenarios Hardening Phase 2  
**Date:** 2026-03-17  
**Execution:** Cursor Composer

---

## 1. Sprint Theme

- **What was chosen:** Billing clarification, remove vehicle (减车), claim first notice (报事故), renewal increase (续保涨价).
- **Why now:** Phase 1 hardened add-car, payment, premium, add driver, bundling. Phase 2 targets the next tier: billing clarification misroute ("账单什么意思" → payment) and shorthand phrasings.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product / Scenario Blueprint | (inline in this report) |
| Phase 2 Scenario Selection Spec | (inline) |
| Scenario Handling Matrix Spec | (inline) |
| Conversation Strategy Spec | Reused from Phase 1 |
| Execution Outline | (inline) |
| Acceptance / SLA Criteria | 63 triage, 39 multi-turn, guardrail PASS |
| Founder Demo / Inspection Notes | §10 below |

---

## 3. Baseline Audit

| Area | Before Phase 2 | After Phase 2 |
|------|----------------|---------------|
| Inbox triage | 58/58 passed | **63/63 passed** |
| Multi-turn simulations | 39/39 Strong | 39/39 Strong |
| State/field accuracy | 7/7 passed | 7/7 passed |
| Guardrail | PASS | PASS |

**Biggest weakness (before):** "账单什么意思" (what does this bill mean?) routed to payment_lapse_expiration — wrong. Customer asking for clarification, not payment urgency.

**Biggest merchant-value gap:** Billing clarification treated as payment failure → broker gets wrong urgency, wrong reply.

**Biggest source of broker rework:** Broker had to manually clarify "this is a question about the bill, not a payment problem."

---

## 4. 10–20 Point Breakdown

1. **In scope:** Billing clarification, remove vehicle (减车), claim first notice (报事故), renewal increase
2. **Out of scope:** LC-AC3, bundling deepening, DMV/SR-22
3. **Why these:** Billing clarification = highest misroute; 减车 = common shorthand; 报事故 = first-response; 续保涨价 = verify
4. **Phrasing variants:** 账单什么意思, 账单看不懂, 减车卖掉了, 报事故刚撞了, 续保涨价了怎么办
5. **Classification boundary:** Bill + question + NOT payment_failure → customer_question
6. **Reply strategy:** Billing → "把完整账单或通知发我，我先帮你看一下"
7. **Handoff:** Billing 2 turns; remove/claim/renewal unchanged
8. **case_creation_suggested:** Unchanged
9. **Summary:** Billing uses customer_question summary style
10. **Guardrails:** _is_billing_clarification_request() before payment check
11. **Regression tests:** 63 inbox triage (58+5 new)
12. **New scenarios:** TSH2-BC1, TSH2-BC2, TSH2-CL1, TSH2-RN1, TSH2-RV1
13. **Deferred:** LC-AC3, billing multi-turn
14. **Pilot-ready:** Billing clarification no longer misroutes

---

## 5. Iteration Loop 1

**What was fixed:**
- Billing clarification: "账单什么意思" → customer_question (was payment_lapse_expiration)
- Added _is_billing_clarification_request() before payment check
- Billing reply: "把完整账单或通知发我，我先帮你看一下"
- 减车 added to remove_vehicle markers
- 5 new scenarios: TSH2-BC1, TSH2-BC2, TSH2-RV1, TSH2-CL1, TSH2-RN1

**Why these fixes:** Billing misroute was the biggest "system feels dumb" gap; 减车 is common shorthand.

**What became more realistic:** Billing questions get clarification reply, not payment urgency.

**What became more useful:** Broker gets correct "explain bill" vs "fix payment" routing.

**What did not improve:** LC-AC3 (deferred); billing multi-turn not added.

**Worth it:** Yes. 63/63 triage; no regressions.

---

## 6. Iteration Loop 2

**What was fixed:**
- 报事故 added to claim_intake markers
- TSH2-CL1, TSH2-RN1 verification scenarios added

**What improved vs Loop 1:** Claim first notice and renewal increase explicitly verified.

**What remained weak:** Billing multi-turn not added.

**Worth it:** Yes. 63/63 triage; no regressions.

---

## 7. Optional Loop 3

**Used:** No.

**Reason:** Billing clarification fix and 减车/报事故/续保 verification sufficient. Stopping is correct.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 63/63 passed |
| run_multi_turn_simulations.py | 39/39 Strong |
| audit_state_field_accuracy.py | 7/7 passed |
| guardrail_inbox_triage.sh | PASS |

**Limitations:** API test skipped (no server on 8001).

---

## 9. Deployment / Release Judgment

- **Backend changed:** Yes (triage.py, markers.json, inbox_triage_scenarios.json).
- **Backend redeploy needed:** Yes, if Cloud Run is used.
- **Frontend changed:** No.
- **Founder can inspect:** Yes — paste "账单什么意思" → should get clarification reply (not payment).

---

## 10. Founder Showcase

### Example 1: Billing clarification

| Field | Value |
|-------|-------|
| User asks | 账单什么意思 |
| System now does | Routes to customer_question; reply: "把完整账单或通知发我，我先帮你看一下，再告诉你重点和下一步怎么处理。" |
| Hands off | When full bill/notice provided |
| Better than before | Before: payment_lapse_expiration (wrong). Now: clarification reply. |

### Example 2: Remove vehicle 减车

| Field | Value |
|-------|-------|
| User asks | 减车，卖掉了 |
| System now does | Routes to customer_question; reply: "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。" |
| Better than before | 减车 now in markers; shorthand works. |

### Example 3: Claim first notice

| Field | Value |
|-------|-------|
| User asks | 报事故，刚撞了 |
| System now does | Routes to customer_question; claim intake reply with photos, other driver info. |
| Better than before | 报事故 in markers; first-response guidance. |

---

## 11. Final Judgment

- **Biggest gain:** Billing clarification no longer misroutes to payment_lapse_expiration.
- **Biggest remaining weakness:** Billing multi-turn not added; LC-AC3 deferred.
- **Meaningfully strengthens paid-pilot layer:** Yes. Fewer wrong-urgency replies.
- **Best next step:** Deploy backend; founder trial with TSH2 scenarios.

---

## 12. Iteration Log

| Loop | What changed | Better vs prior | Not improved | Worth it |
|------|--------------|-----------------|--------------|----------|
| 1 | Billing clarification, 减车, 5 scenarios | 63 triage | Billing MT | Yes |
| 2 | 报事故, TSH2-CL1, TSH2-RN1 | Verified | — | Yes |
| 3 | — | — | — | N/A |

---

## 13. 中文宏观总结

**为什么现在做主线二第二轮：** Phase 1 已加固 add-car、payment、premium、add driver、bundling；下一层高价值场景是账单解释误判和减车/报事故 shorthand。

**主要方法/技术：** 新增 _is_billing_clarification_request() 在 payment 检查之前；账单+问题词 ≠ 付款失败；新增 减车、报事故 markers；5 个新场景。

**好处：** 账单什么意思不再误判为付款失败；减车、报事故 shorthand 覆盖。

**已实现：** 63 triage、39 multi-turn 全过；guardrail PASS。

**比原系统提升：** 账单解释正确路由；减车、报事故 shorthand 覆盖。

**还差什么：** Billing 多轮；LC-AC3。

**有无重大问题：** 无。

**下一步最该做：** 部署后端；创始人试用 TSH2 场景。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Top Scenarios Hardening Phase 2 — Founder Summary

Biggest improvement: "账单什么意思" (what does this bill mean?) no longer routes to payment failure. Now gets clarification reply: "把完整账单或通知发我，我先帮你看一下."

Biggest remaining weakness: Billing multi-turn not added; LC-AC3 deferred.

Makes product more sellable/reusable: Yes. Fewer wrong-urgency replies for billing questions.

Redeploy needed: Backend yes (triage + markers + scenarios). Frontend no.

What Andy should inspect: Paste "账单什么意思" → should get clarification reply (NOT payment). Paste "减车，卖掉了" → should get remove-vehicle reply.
```

---

## 15. REQUIRED CROSS-WINDOW BLOCK

```
Top Scenarios Hardening Phase 2 — Evaluator Block

Current scenario layer maturity: Strong. 63 inbox triage, 39 multi-turn (all Strong), guardrail PASS.

Biggest improvements: (1) Billing clarification — "账单什么意思" no longer payment_lapse_expiration. (2) 减车、报事故 markers for shorthand.

Biggest remaining weaknesses: Billing multi-turn; LC-AC3 (driver correction).

Direction correct: Yes. Scenario hardening without platform bloat.

Best next recommendation: Deploy backend; founder trial; consider billing multi-turn in next sprint.

Technical backbone: Python triage (services/fiqa_api/inbox_triage/triage.py), configs/industries/insurance/markers.json, configs/inbox_triage_scenarios.json.
```

---

## 16. REQUIRED SHORT OVERVIEW

### 为什么做这件事
Phase 1 已稳；账单解释误判为付款失败、减车 shorthand 需加固。

### 主要用了什么方法/技术
分类顺序（billing clarification 先于 payment）；新增 markers（减车、报事故）；5 个新场景。

### 这轮最大的提升
账单什么意思正确路由；减车、报事故 shorthand 覆盖；63 triage 全过。

### 现在还差什么
Billing 多轮；LC-AC3。

---

## 17. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作
- Billing clarification 分类修复
- 减车、报事故 markers
- 5 个新单轮场景
- 全量验证

### 哪些地方比原系统提高了
- 账单解释不再误判为付款失败
- 减车、报事故 shorthand 覆盖
- 场景覆盖 58→63

### 每一轮大概花了哪些时间/精力
- Loop 1: Billing fix + 减车 + 5 场景
- Loop 2: 报事故 + 验证场景

### 还有哪些值得下一轮继续做
- Billing 多轮
- LC-AC3 handoff 逻辑

---

*End of Top Scenarios Hardening Phase 2 Report*
