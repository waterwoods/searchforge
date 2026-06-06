# Top Commercial Scenarios Deepening Report

**Sprint:** Top Commercial Scenarios Deepening Sprint  
**Date:** 2026-03-17  
**Execution:** Cursor Composer  
**Target budget:** 60–150 minutes

---

## 1. Sprint theme

- **What was chosen:** Add-car driver correction (LC-AC3), billing T2 "我发你了", driver extraction, summary correction capture.
- **Why now:** Founder identified turn 3/4 still feels shallow; LC-AC3 was the only friction in long-context pack; billing multi-turn was deferred in Phase 2.

---

## 2. Document set created

| Doc | Path |
|-----|------|
| Product / Scenario Blueprint | `docs/sprints/TOP_COMMERCIAL_SCENARIOS_DEEPENING_SPRINT/01_PRODUCT_SCENARIO_BLUEPRINT.md` |
| Deepening Scenario Selection Spec | (inline in this report) |
| Turn 3–4 Conversation Strategy Spec | Reused from LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT |
| Scenario Handling Matrix Spec | (inline) |
| Execution Outline | (inline) |
| Acceptance / SLA Criteria | 63 triage, 40 multi-turn, guardrail PASS |
| Founder Demo / Inspection Notes | §10 below |

---

## 3. Baseline audit

| Area | Before | After |
|------|--------|-------|
| Inbox triage | 63/63 passed | 63/63 passed |
| Multi-turn simulations | 39/39 Strong | **40/40 Strong** |
| Long-context pack | 1 friction (LC-AC3) | **10/10 Strong** |
| Simulation Assistant | 24 normal, 3 off-flow | **27/27 normal** |
| Guardrail | PASS | PASS |

**Biggest later-turn weakness (before):** LC-AC3 — "我刚才说错了，是我老婆开那辆" handed off at T2; driver correction arrived after handoff.

**Biggest "feels simulated" issue:** Add-car with zip+delivery at T2 handed off without asking driver; corrections like "是我老婆开" lost.

**Biggest broker rework source:** Broker had to infer driver from append; summary did not always capture "说错了" corrections.

---

## 4. 10–20 point breakdown

1. **In scope:** Add-car driver correction, billing T2 "我发你了", driver extraction, summary correction.
2. **Out of scope:** Remove-vehicle deepening, claim deepening, renewal 4-turn (already strong).
3. **Why these:** LC-AC3 was the only friction; billing multi-turn was Phase 2 deferred; driver affects premium.
4. **Later-turn weakness fixed:** Add-car at T2 with delivery but not driver → ask for driver.
5. **Confirmation wording:** "主要驾驶人发我一下，我好安排报价。" at T2 when delivery present.
6. **Correction handling:** "说错了" added to summary context_hint; driver markers expanded.
7. **Main driver / yourself / family member:** "我老婆开", "老公开", "我开", "就我" → driver=True.
8. **Billing T2 "我发你了":** MT40 added; already_sent handoff works (customer_question + follow_up_type).
9. **Add-car after year+zip+driver clue:** At T2 only, when delivery present, ask driver; T3 correction captured.
10. **Handoff threshold:** Add-car asks driver at T2 when delivery present; handoff at T3.
11. **Summary:** "说错了" → "Customer corrected/clarified."; driver in collected_hint.
12. **Guardrails:** No new guardrails; existing tests updated.
13. **Simulations/tests:** MT16, SIM4, SIM11, R3 updated to 3-turn; MT40 added.
14. **Intentionally deferred:** Remove-vehicle 4-turn, claim 4-turn deepening.
15. **Broker follow-up reduced:** Driver captured in same case; correction in summary.
16. **Pilot-ready:** LC-AC3 Strong; billing multi-turn verified.

---

## 5. Iteration loop 1

**What deeper-turn problems were fixed:**
- LC-AC3: Add-car at T2 with zip+delivery now asks for driver; T3 "是我老婆开那辆" captured.
- Driver extraction: "我老婆开", "老公开", "我开" → has_driver=True.
- Summary: "说错了" → context_hint "Customer corrected/clarified."

**Why these fixes were chosen:** LC-AC3 was the only friction; driver affects premium; correction capture improves broker handoff.

**What became more natural:** Add-car asks one more useful question (driver) before handoff when delivery present at T2.

**What became more useful:** Broker receives driver in collected_fields; summary shows correction.

**What did not improve:** Remove-vehicle, claim 4-turn (deferred).

**Worth it:** Yes. LC-AC3 Strong; 40/40 multi-turn; 27/27 Simulation Assistant.

---

## 6. Iteration loop 2

**What deeper-turn problems were fixed:**
- Billing T2 "我发你了": MT40 added; already_sent handoff verified.
- Simulation scenarios: SIM4, SIM11, R3 updated to 3-turn with driver.

**Why these fixes were chosen:** Billing multi-turn was Phase 2 deferred; Simulation Assistant had 3 off-flow.

**What improved vs loop 1:** Billing multi-turn coverage; all Simulation Assistant scenarios pass.

**What still remained weak:** None in scope.

**Worth it:** Yes. 27/27 Simulation Assistant; MT40 Strong.

---

## 7. Optional loop 3

**Used:** No.

**Reason:** LC-AC3, billing multi-turn, and scenario updates sufficient. Stopping is correct.

---

## 8. Validation summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 63/63 passed |
| run_multi_turn_simulations.py | 40/40 Strong |
| run_complex_adversarial_simulation.py (long_context) | 10/10 Strong |
| guardrail_inbox_triage.sh | PASS |
| test_state_workflow_backbone.py | PASS |

**Limitations:** API test skipped (no server on 8001).

---

## 9. Deployment / release judgment

- **Backend changed:** Yes (triage.py, customer_entry_multi_turn_simulations.json, simulation_assistant_scenarios.json, test_state_workflow_backbone.py).
- **Backend redeploy needed:** Yes, if Cloud Run is used.
- **Frontend changed:** No.
- **Founder can inspect:** Yes — run LC-AC3, MT40, SIM4 in Simulation Assistant.

---

## 10. Founder showcase (REQUIRED)

### Example 1: Add-car driver correction (LC-AC3)

| Field | Value |
|-------|-------|
| User says (T1) | 加一台2024 Tesla Model Y |
| User says (T2) | 90210，下周拿车 |
| System now does (T2) | Asks "主要驾驶人发我一下，我好安排报价。" (does not hand off) |
| User says (T3) | 我刚才说错了，是我老婆开那辆 |
| System now does (T3) | Hands off with "好的，明白了。办公室会尽快处理，有结果会联系您。" |
| What it collects | year, model, zip, delivery, driver (老婆开) |
| When it hands off | After T3 when driver provided |
| Why better | Before: handed off at T2; driver correction lost. Now: driver captured in same case. |

### Example 2: Billing T2 "我发你了"

| Field | Value |
|-------|-------|
| User says (T1) | 账单什么意思 |
| System now does (T1) | "把完整账单或通知发我，我先帮你看一下" |
| User says (T2) | 账单我发你微信了 |
| System now does (T2) | Hands off with "好的，收到了。办公室会尽快处理，有结果会联系您。" |
| What it collects | Bill sent |
| When it hands off | After T2 |
| Why better | Billing multi-turn now has already_sent path; was deferred in Phase 2. |

### Example 3: Add-car 3-turn (SIM4, SIM11, R3)

| Field | Value |
|-------|-------|
| User says (T1) | I bought a new BMW X5, how much is insurance? |
| User says (T2) | 2024, 90210, picking up next week |
| System now does (T2) | Asks for main driver |
| User says (T3) | I drive it myself |
| System now does (T3) | Hands off |
| Why better | One more useful turn; driver captured. |

---

## 11. Final judgment

- **Biggest gain:** LC-AC3 driver correction now captured; billing multi-turn verified.
- **Biggest remaining weakness:** Remove-vehicle 4-turn, claim 4-turn not deepened (low priority).
- **Meaningfully strengthens paid-pilot layer:** Yes. Fewer lost corrections; more natural add-car flow.
- **Best next step:** Deploy backend; founder trial with LC-AC3, MT40, SIM4.

---

## 12. Iteration log (REQUIRED)

| Loop | What changed | Better vs prior | Not improved | Worth it |
|------|--------------|-----------------|--------------|----------|
| 1 | LC-AC3 fix, driver extraction, summary "说错了", MT16/SIM4/SIM11/R3 updates | LC-AC3 Strong; 40 MT | — | Yes |
| 2 | MT40 billing, SIM4/SIM11/R3 T3 driver | 27/27 Sim Asst; billing MT | — | Yes |
| 3 | — | — | — | N/A |

---

## 13. 中文宏观总结

**为什么现在先做这个：** 创始人指出第3/4轮仍显浅；LC-AC3 是唯一摩擦；账单多轮 Phase 2 未做。

**主要方法/技术：** 加车 T2 有 delivery 无 driver 时多问一轮驾驶人；扩展 driver 提取（我老婆开、我开）；账单 T2「发你了」走 already_sent 转交；summary 增加「说错了」修正提示。

**这轮最大提升：** LC-AC3 从 FRICTION 变 Strong；账单多轮 MT40 验证；40 个多轮、27 个 Sim Asst 全过。

**还差什么：** 减车、事故 4 轮深化（低优先级）。

**下一步最该做：** 部署后端；创始人试用 LC-AC3、MT40。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Top Commercial Scenarios Deepening — Founder Summary

Biggest improvement: LC-AC3 ("我刚才说错了，是我老婆开那辆") now Strong. Add-car at T2 with zip+delivery asks for driver; T3 correction captured. Billing T2 "我发你了" verified (MT40).

Biggest remaining weakness: Remove-vehicle, claim 4-turn not deepened (low priority).

Makes product more sellable/reusable: Yes. Fewer lost corrections; more natural add-car flow.

Redeploy needed: Backend yes. Frontend no.

What Andy should inspect: Run LC-AC3, MT40, SIM4 in Simulation Assistant. Paste "加一台2024 Tesla Model Y" → "90210，下周拿车" → should ask for driver, not hand off.
```

---

## 15. REQUIRED CROSS-WINDOW BLOCK

```
Top Commercial Scenarios Deepening — Evaluator Block

Current scenario layer maturity: Strong. 63 inbox triage, 40 multi-turn (all Strong), 10/10 long-context, 27/27 Simulation Assistant, guardrail PASS.

Biggest improvements: (1) LC-AC3 driver correction — ask driver at T2 when delivery present; capture "是我老婆开" at T3. (2) Billing multi-turn MT40 verified. (3) Driver extraction expanded (我老婆开, 我开). (4) Summary "说错了" → correction hint.

Biggest remaining weaknesses: Remove-vehicle, claim 4-turn not deepened.

Direction correct: Yes. Deepen highest-value scenarios; no bloat.

Best next recommendation: Deploy backend; founder trial; consider remove-vehicle/claim 4-turn in next sprint if needed.

Technical backbone: Python triage (services/fiqa_api/inbox_triage/triage.py), configs (customer_entry_multi_turn_simulations.json, simulation_assistant_scenarios.json).
```

---

## 16. REQUIRED SHORT OVERVIEW

### 为什么做这件事
第3/4轮仍显浅；LC-AC3 唯一摩擦；账单多轮未做。

### 主要用了什么方法/技术
加车 T2 多问驾驶人；driver 提取扩展；账单 T2 already_sent；summary 修正提示。

### 这轮最大的提升
LC-AC3 Strong；账单多轮 MT40；40 多轮、27 Sim Asst 全过。

### 现在还差什么
减车、事故 4 轮深化（低优先级）。

---

## 17. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作
- LC-AC3 修复（T2 问驾驶人）
- Driver 提取扩展
- Summary "说错了" 修正提示
- MT40 账单多轮
- MT16、SIM4、SIM11、R3 更新为 3 轮
- test_state_workflow_backbone 更新

### 哪些地方比原系统提高了
- LC-AC3 从 FRICTION 变 Strong
- 账单多轮验证
- 驾驶人修正捕获
- 27/27 Simulation Assistant

### 每一轮大概花了哪些时间/精力
- Loop 1: triage 逻辑、driver 提取、场景更新
- Loop 2: MT40、Sim Asst 场景更新

### 还有哪些值得下一轮继续做
- 减车 4 轮
- 事故 4 轮
- 其他修正路径

---

*End of Top Commercial Scenarios Deepening Report*
