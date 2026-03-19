# Top Scenarios Hardening Master Report

**Sprint:** Top Scenarios Hardening Master Sprint  
**Date:** 2026-03-17  
**Execution:** Cursor Composer

---

## 1. Sprint Theme

- **What was chosen:** Hardening add-car, payment, missing document, premium, add driver, and bundling scenarios.
- **Why now:** Backbone is solid (53/53 triage, 38/38 multi-turn pass); founder observes system can feel "too simple" or "too wrong" for real-world phrasings outside demo.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product / Scenario Blueprint | `docs/sprints/TOP_SCENARIOS_HARDENING_SPRINT/01_PRODUCT_SCENARIO_BLUEPRINT.md` |
| Top Scenarios Selection Spec | `02_TOP_SCENARIOS_SELECTION_SPEC.md` |
| Scenario Handling Matrix Spec | `03_SCENARIO_HANDLING_MATRIX_SPEC.md` |
| Conversation Strategy Spec | `04_CONVERSATION_STRATEGY_SPEC.md` |
| Execution Outline | `05_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `06_ACCEPTANCE_SLA_CRITERIA.md` |
| Founder Demo / Inspection Notes | `07_FOUNDER_DEMO_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

| Area | Status |
|------|--------|
| Inbox triage | 53/53 passed |
| Multi-turn simulations | 38/38 Strong |
| State/field accuracy | 7/7 passed |
| Speed routing | OK |
| Guardrail | PASS |

**Biggest weakness:** Add driver ("加个司机") and bundling ("一起买能打折") routed to unclear. Premium + "我发你账单了" misrouted to payment_lapse_expiration.

**Biggest merchant-value gap:** Real phrasings for add driver and bundling got generic fallback.

**Biggest "system feels dumb" source:** Premium + bill-sent treated as payment failure.

---

## 4. 10–20 Point Breakdown

1. **In scope:** Add-car, payment, missing doc, remove vehicle, premium, claim, add driver, bundling
2. **Out of scope:** DMV/SR-22, full add-driver multi-turn collection, full bundling workflow
3. **Priority:** Loop 1 = premium fix, add-driver, bundling; Loop 2 = verification + MT39
4. **Phrasing variants:** Add driver (加个司机, 加人开车), bundling (一起买能打折, bundling discount)
5. **Routing:** Premium before payment when premium_review markers present
6. **Next-best-question:** Add driver → vehicle, driver info, license; bundling → policies
7. **Reassure/answer-first:** Unchanged; already strong
8. **Handoff:** Add driver 2 turns; bundling 2 turns
9. **case_creation_suggested:** Unchanged
10. **Summary:** Add driver/bundling use customer_question summary style
11. **User error patterns:** Premium + bill sent misclassified — fixed
12. **Mixed-intent:** Unchanged; complex adversarial passes
13. **Business wording:** Office-natural; no formal letter tone
14. **Regression tests:** 58 inbox triage (53+5 new); 39 multi-turn (38+1 new)
15. **Simulation scenarios:** TSH-AD1, TSH-AD2, TSH-B1, TSH-B2, TSH-PR1, MT39
16. **Workbench:** Unchanged
17. **Deferred:** LC-AC3 handoff timing; full add-driver multi-turn
18. **Pilot-ready:** Fewer unclear fallbacks; premium-vs-payment fixed

---

## 5. Iteration Loop 1

**What was fixed:**
- Premium + "我发你账单了" routing (check premium_review before payment)
- Add driver intent (markers + reply)
- Bundling intent (markers + reply)

**Why these fixes:** Highest merchant-value gaps; clear routing errors.

**What became more realistic:** Add driver and bundling get tailored replies.

**What became more useful:** Premium + bill-sent no longer triggers payment urgency.

**What did not improve:** LC-AC3 (1 Friction); remove vehicle, claim already strong.

**Worth it:** Yes. 5 new scenarios pass; no regressions.

---

## 6. Iteration Loop 2

**What was fixed:**
- Add-driver multi-turn (MT39)
- Category mapping for add_driver in run_multi_turn_simulations.py

**What improved vs Loop 1:** Add-driver now has multi-turn coverage.

**What remained weak:** LC-AC3 (driver correction handoff) — acceptable to defer.

**Worth it:** Yes. 39/39 Strong.

---

## 7. Optional Loop 3

**Used:** No.

**Reason:** LC-AC3 fix would require handoff logic changes; low-risk refinement not clearly valuable enough. Stopping is correct.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 58/58 passed |
| run_multi_turn_simulations.py | 39/39 Strong |
| audit_state_field_accuracy.py | 7/7 passed |
| verify_speed_routing.py | OK |
| guardrail_inbox_triage.sh | PASS |
| unified_intake_smoke_check.sh | (requires server) |

**Limitations:** API test skipped (no server on 8001). LC-AC3 remains 1 Friction.

---

## 9. Deployment / Release Judgment

- **Backend changed:** Yes (triage.py, configs).
- **Backend redeploy needed:** Yes, if Cloud Run is used.
- **Frontend changed:** No.
- **Frontend redeploy needed:** No.
- **Founder can inspect:** Yes — run demo, paste TSH scenarios.

---

## 10. Founder Showcase

### Example 1: Add driver

| Field | Value |
|-------|-------|
| User asks | 加个司机，我儿子刚拿驾照 |
| System now does | Routes to customer_question; reply: "好的，可以加司机。把要加的是哪辆车、驾驶人信息和驾照发我，我先帮你确认下一步。" |
| Collects | Vehicle, driver info, license |
| Hands off | After 2 turns when vehicle + driver info provided |
| Better than before | Before: "这段内容还不够完整" (unclear). Now: tailored add-driver reply. |

### Example 2: Bundling

| Field | Value |
|-------|-------|
| User asks | home insurance 一起买能打折吗 |
| System now does | Routes to customer_question; reply: "房屋险和车险一起买一般有折扣。把您现在的车险和房屋险（如果有）情况发我，我先帮你看有没有合适的方案。" |
| Collects | Current policies |
| Hands off | After 2 turns |
| Better than before | Before: unclear. Now: bundling-specific reply. |

### Example 3: Premium + bill sent

| Field | Value |
|-------|-------|
| User asks | 帮我看看能不能便宜，我发你账单了 |
| System now does | Routes to customer_question (premium_review); reply: "我先帮你看这次保费为什么变高..." |
| Collects | Policy, bill |
| Hands off | When policy/bill mentioned |
| Better than before | Before: payment_lapse_expiration (wrong). Now: premium review. |

---

## 11. Final Judgment

- **Biggest gain:** Premium-vs-payment disambiguation + add driver + bundling coverage.
- **Biggest remaining weakness:** LC-AC3 (driver correction handoff timing).
- **Meaningfully strengthens paid-pilot layer:** Yes. Fewer "system feels dumb" moments.
- **Best next step:** Deploy backend; founder trial with TSH scenarios; consider LC-AC3 in next sprint.

---

## 12. Iteration Log

| Loop | What changed | Better vs prior | Not improved | Worth it | Next step |
|------|--------------|-----------------|--------------|----------|-----------|
| 1 | Premium order, add_driver, bundling markers+replies, 5 new scenarios | 58 triage, tailored replies | LC-AC3 | Yes | Loop 2 |
| 2 | MT39, add_driver cat_map | 39 multi-turn | LC-AC3 | Yes | Final report |
| 3 | — | — | — | N/A | Stopped |

---

## 13. 中文宏观总结

**为什么现在做主线二：** 骨干已稳（53 triage、38 multi-turn全过），创始人反馈真实场景下系统仍会显得“太简单”或“答错”。

**主要方法/技术：** 分类顺序调整（premium先于payment）、新增add_driver和bundling的markers与回复模板、新增场景测试。

**好处：** 加司机、捆绑折扣不再落入“不够完整”；保费+账单已发不再误判为付款失败。

**已实现：** 5个新单轮场景、1个新多轮场景；58 triage、39 multi-turn全过；guardrail PASS。

**比原系统提升：** 减少generic fallback；premium与payment区分正确；add driver和bundling有专门回复。

**还差什么：** LC-AC3（司机纠正后的handoff时机）仍为1个Friction；可下一轮处理。

**有无重大问题：** 无。

**下一步最该做：** 部署后端；创始人试用TSH场景；视情况安排LC-AC3。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Top Scenarios Hardening Sprint — Founder Summary

Biggest improvement: Premium + "我发你账单了" no longer routes to payment failure. Add driver and bundling now get tailored replies instead of "这段内容还不够完整."

Biggest remaining weakness: LC-AC3 (driver correction handoff timing) — 1 Friction, acceptable to defer.

Makes product more sellable/reusable: Yes. Fewer "system feels dumb" moments for real phrasings.

Redeploy needed: Backend yes (triage + configs). Frontend no.

What Andy should inspect: Paste "加个司机，我儿子刚拿驾照" → should get add-driver reply. Paste "帮我看看能不能便宜，我发你账单了" → should get premium reply (not payment). Paste "home insurance 一起买能打折吗" → should get bundling reply.
```

---

## 15. REQUIRED CROSS-WINDOW BLOCK

```
Top Scenarios Hardening — Evaluator Block

Current scenario layer maturity: Strong. 58 inbox triage, 39 multi-turn (all Strong), guardrail PASS.

Biggest improvements: (1) Premium before payment in classification — "我发你账单了" in premium context no longer payment_lapse_expiration. (2) Add driver and bundling — new markers and replies; no longer unclear.

Biggest remaining weaknesses: LC-AC3 (driver correction) handoff at turn 2 vs expected 3. One Friction in complex adversarial pack.

Direction correct: Yes. Scenario hardening without platform bloat.

Best next recommendation: Deploy backend; founder trial; consider LC-AC3 in next sprint.

Technical backbone: Python triage (services/fiqa_api/inbox_triage/triage.py), configs/industries/insurance/markers.json, configs/inbox_triage_scenarios.json, configs/customer_entry_multi_turn_simulations.json. Rule-based + optional LLM. Fast path for high-confidence turns.
```

---

## 16. REQUIRED SHORT OVERVIEW

### 为什么做这件事
骨干已稳，但真实用户提问（加司机、捆绑、保费+账单已发）仍会落入generic或误分类，需加固高价值场景。

### 主要用了什么方法/技术
分类顺序调整、新增intent markers、回复模板、场景测试。

### 这轮最大的提升
Premium与payment正确区分；add driver和bundling有专门回复；58 triage、39 multi-turn全过。

### 现在还差什么
LC-AC3 handoff时机；可下一轮处理。

---

## 17. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作
- 7份控制文档
- 分类顺序调整（premium先于payment）
- add_driver、bundling markers与回复
- 5个新单轮场景、1个新多轮场景
- 全量验证

### 哪些地方比原系统提高了
- 加司机、捆绑不再unclear
- 保费+账单已发不再误判为付款失败
- 场景覆盖从53→58、38→39

### 每一轮大概花了哪些时间/精力
- Phase A + Baseline: 文档+审计
- Loop 1: 实现+测试
- Loop 2: MT39+验证
- Loop 3: 跳过

### 还有哪些值得下一轮继续做
- LC-AC3 handoff逻辑
- 更多add-driver多轮变体
- 更多bundling变体

---

*End of Top Scenarios Hardening Master Report*
