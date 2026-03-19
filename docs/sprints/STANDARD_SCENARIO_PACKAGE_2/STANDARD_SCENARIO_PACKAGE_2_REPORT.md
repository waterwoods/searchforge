# Standard Scenario Package 2.0 Report

**Sprint:** Standard Scenario Package 2.0  
**Date:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Deepen the top 5 commercial flows (add-car, material/already sent, renewal premium, payment/cancellation, talk to agent) so the package becomes more convincing, more reusable, and more pilot-ready.
- **Why now:** The current package is sellable but handoff usefulness and broker guidance when "client says sent" or "client says paid" were implicit. Package 2.0 makes these explicit so the broker asks fewer manual follow-up questions.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product / Package 2.0 Blueprint | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/01_PRODUCT_PACKAGE_2_BLUEPRINT.md` |
| Scenario Selection Spec | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/02_SCENARIO_SELECTION_SPEC.md` |
| Package 2.0 Handling Matrix Spec | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/03_PACKAGE_2_HANDLING_MATRIX_SPEC.md` |
| Conversation / Handoff Deepening Spec | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/04_CONVERSATION_HANDOFF_DEEPENING_SPEC.md` |
| Execution Outline | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/05_EXECUTION_OUTLINE.md` |
| Acceptance / Sellability Criteria | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/06_ACCEPTANCE_SELLABILITY_CRITERIA.md` |
| Founder Demo / Sales Inspection Notes | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/07_FOUNDER_DEMO_SALES_INSPECTION_NOTES.md` |
| Baseline Audit | `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/08_BASELINE_AUDIT.md` |

---

## 3. Baseline Audit

| Area | Status |
|------|--------|
| **Current package quality** | Inbox triage 64/64 pass; multi-turn 41/41 pass |
| **Biggest weakness** | Summary and broker_next_step when "client says sent" or "client says paid" did not explicitly tell broker to verify with carrier |
| **Biggest broker rework source** | When client says "发过了" or "我付了" — broker received handoff but next move was implicit |
| **Biggest "still MVP-like" issue** | broker_next_step could be more actionable: "Verify dec page received with carrier" vs generic "Review and follow up" |

---

## 4. 10–20 Point Breakdown

1. **Scenarios in scope:** Add-car, Material/already sent, Renewal premium, Payment/cancellation, Talk to Agent
2. **Why selected:** Highest commercial value; reduce broker rework; pilot-ready
3. **Deferred:** Remove-car (strong), Claim (lower freq), Billing clarification standalone
4. **Biggest weakness each:** Add-car—summary clarity; Material—verify guidance; Renewal—handoff when bill sent; Payment—verify when paid; Talk to Agent—mid-flow (already strong)
5. **Recognition improvements:** Minor; already strong
6. **Later-turn improvements:** Clarification/urgency answer-first; already_sent warmer handoff (existed)
7. **Correction handling:** other_corrected + embedded question (existed)
8. **Already-sent / material:** broker_next_step "verify receipt"; summary "Client says sent" — **implemented**
9. **Handoff timing:** Per MATURE_INTAKE_SKELETON
10. **Summary improvements:** "Client says already paid"; "policy/bill sent" when client sends — **implemented**
11. **Workbench usefulness:** collected_fields, still_needed include verify_receipt (existed)
12. **Broker follow-up reduction:** Explicit verify guidance — **implemented**
13. **Simulation/test additions:** P2-M1, P2-C1 audit cases — **added**
14. **Guardrails:** broker_next_step includes verify when already_sent/paid — **implemented**
15. **"Package 2.0 stronger":** Broker asks fewer manual follow-ups
16. **Out of scope:** New scenarios, platform features, docs-only
17. **More reusable:** Same skeleton; clearer handoff contract
18. **Next step after:** Package 2.1 — remove-car deepening, claim deepening, or config extraction

---

## 5. Iteration Loop 1

**What package/scenario problems were fixed:**
- broker_next_step when "client says sent" (missing_document) or "client says paid" (payment) was generic
- conversation_summary did not distinguish "client says already paid" from "client says sent notice/screenshot"

**Why these fixes were chosen:**
- Highest broker rework source; explicit verify guidance reduces manual follow-up

**What became more natural:**
- Handoff phrase ("好的，收到了") unchanged; broker_next_step now says "Verify with carrier that resubmitted documents were received" or "Confirm with carrier that payment was received; if not, process payment today"

**What became more useful to the broker:**
- broker_next_step is one operational sentence; broker knows exactly what to do next

**What remained weak:**
- Add-car and renewal broker_next_step still generic at handoff

**Whether loop 1 was worth it:** Yes. Core "already sent/paid" flows are now explicitly actionable.

---

## 6. Iteration Loop 2

**What package/scenario problems were fixed:**
- Renewal summary said "policy/bill mentioned" even when client explicitly sent
- Add-car broker_next_step at handoff was "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day" — generic

**Why these fixes were chosen:**
- Renewal and add-car are high-frequency; clearer summary and broker_next_step improve office usability

**What improved vs loop 1:**
- Renewal: "Collected: policy/bill sent" when client sends; broker_next_step "Review renewal notice and quote options; confirm remove-vehicle intent if client asked"
- Add-car: broker_next_step "Run quote for collected vehicle details (year, model, zip). Confirm delivery date and driver with client before binding."

**What still remained weak:**
- Talk to Agent mid-flow already strong; no changes needed

**Whether loop 2 was worth it:** Yes. Renewal and add-car handoffs are more concrete.

---

## 7. Iteration Loop 3

**What package problems were fixed:**
- No new product changes; added Package 2.0 audit cases (P2-M1, P2-C1) to lock in broker_next_step verify/confirm behavior

**Why these fixes were chosen:**
- Guardrail ensures future changes don't regress Package 2.0 behavior

**What improved vs loop 2:**
- audit_state_field_accuracy.py now has 9 cases including 2 Package 2.0 cases

**What still remained weak:**
- None identified

**Whether loop 3 was worth it:** Yes. Package 2.0 behavior is now regression-tested.

---

## 8. Optional Loop 4

**Whether used:** No.

**Why stopping is correct:** All high-value improvements implemented; no clearly valuable, low-risk refinement remaining.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 64/64 passed |
| `run_multi_turn_simulations.py` | 41/41 passed |
| `audit_state_field_accuracy.py` | 9/9 passed (incl. P2-M1, P2-C1) |
| `guardrail_inbox_triage.sh` | PASS |
| `ui && npm run build` | Built successfully |

**Limitations:** LLM path not exercised; rule path only. Backend must be running for live smoke check.

---

## 10. Deployment / Release Judgment

- **Backend changed:** Yes (triage.py). Backend redeploy needed for Cloud Run if/when deploying.
- **Frontend changed:** No.
- **Whether founder can inspect now:** Yes, locally. Run `bash scripts/run_demo_local.sh` and test add-car, missing doc, renewal, payment flows.

---

## 11. Founder Showcase

### Add-car

| Dimension | Before | After |
|-----------|--------|-------|
| **Scenario** | Add-car handoff | Same |
| **Customer experience** | "报价资料已收集，办公室会尽快出价" | Same |
| **Broker gets** | broker_next_step: "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day." | broker_next_step: "Run quote for collected vehicle details (year, model, zip). Confirm delivery date and driver with client before binding." |
| **Why stronger** | More concrete; broker knows exactly what to run | |
| **Why helps selling** | "One paste → structured case" with clear next step | |

### Material / Already Sent

| Dimension | Before | After |
|-----------|--------|-------|
| **Scenario** | Client says "dec page 发你了，garaging 也发了" | Same |
| **Customer experience** | "好的，收到了。办公室会尽快核实" | Same |
| **Broker gets** | broker_next_step: "Verify whether customer-resubmitted items were received; request any still-missing items." | broker_next_step: "Verify with carrier that resubmitted documents were received; request any still-missing items." |
| **Why stronger** | Explicit "with carrier"; broker knows to verify receipt | |
| **Why helps selling** | Reduces "did we get it?" manual follow-up | |

### Payment / Already Paid

| Dimension | Before | After |
|-----------|--------|-------|
| **Scenario** | Client says "我昨天付了，截图发你" | Same |
| **Customer experience** | "好的，收到了。办公室会尽快处理" | Same |
| **Broker gets** | broker_next_step: "Confirm whether the payment actually failed..." | broker_next_step: "Confirm with carrier that payment was received; if not, process payment today to avoid lapse." |
| **Why stronger** | Explicit verify + same-day action | |
| **Why helps selling** | Urgent flows get clearer broker guidance | |

### Renewal Premium

| Dimension | Before | After |
|-----------|--------|-------|
| **Scenario** | Client says "续保通知和账单我发你微信了" | Same |
| **Customer experience** | Handoff | Same |
| **Broker gets** | Summary: "policy/bill mentioned"; broker_next_step generic | Summary: "Collected: policy/bill sent"; broker_next_step: "Review renewal notice and quote options; confirm remove-vehicle intent if client asked" |
| **Why stronger** | Summary distinguishes sent vs mentioned; broker_next_step actionable | |
| **Why helps selling** | Retention flow feels more complete | |

---

## 12. Final Judgment

- **Biggest gain:** broker_next_step when "client says sent" or "client says paid" now explicitly tells broker to verify with carrier. Reduces manual follow-up.
- **Biggest remaining weakness:** Add-car broker_next_step could include actual year/model/zip values (currently "collected vehicle details"); deferred as lower ROI.
- **Whether this now feels like a stronger commercial package:** Yes. Handoff is more useful; broker gets clearer verification guidance.
- **Best next step:** Package 2.1 — remove-car deepening, or config extraction for easier tuning.

---

## 13. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Recommended next |
|------|--------------|-----------------|----------------------|-----------|------------------|
| 1 | broker_next_step override for already_sent/paid; summary "client says already paid" | Missing doc + payment handoffs more actionable | Add-car, renewal | Yes | Loop 2 |
| 2 | Renewal summary "policy/bill sent"; add-car broker_next_step; renewal broker_next_step | Renewal + add-car handoffs more concrete | Talk to Agent (already strong) | Yes | Loop 3 |
| 3 | P2-M1, P2-C1 audit cases | Regression guardrail for Package 2.0 | — | Yes | Stop |

---

## 14. 中文宏观总结

- **为什么现在做这个 Package 2.0：** 现有套餐可卖，但客户说「发过了」「付了」时，经纪人收到的 handoff 不够明确，不知道下一步要「核实」。Package 2.0 把「核实」写进 broker_next_step，减少经纪人重复追问。
- **主要用了什么方法/技术：** 在 triage_conversation 中，当 handoff 且 (already_sent 或 collected 含 already_paid_claimed / customer_says_sent) 时，覆盖 broker_next_step 为更具体的操作句；同时增强 conversation_summary 对「已付」「已发」的区分。
- **这轮最大的提升：** broker_next_step 在「客户说发了/付了」时，明确告诉经纪人「与 carrier 核实是否收到；若未收到，今日处理」。
- **还差什么：** add-car 的 broker_next_step 可进一步包含具体 year/model/zip 值；remove-car、claim 深化留待 2.1。
- **下一步最该做什么：** Package 2.1 深化 remove-car 或 claim；或做 config 提取便于调参。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest Package 2.0 improvement:** When the client says "I already sent it" or "I already paid," the broker now gets an explicit broker_next_step: "Verify with carrier that resubmitted documents were received" (missing doc) or "Confirm with carrier that payment was received; if not, process payment today" (payment). This reduces manual follow-up.

**Biggest remaining weakness:** Add-car broker_next_step could show actual year/model/zip; deferred.

**Whether this makes the product more sellable/reusable:** Yes. Handoff is more useful; broker asks fewer "did we get it?" questions.

**Whether redeploy is needed:** Backend yes (if deploying to Cloud Run); frontend no.

**What Andy should inspect next:** Run demo; paste "dec page 发你了" or "我付了" in a payment/missing-doc flow; confirm broker_next_step shows verify/confirm guidance.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Current package maturity:** Package 2.0. Top 5 flows (add-car, material/already sent, renewal, payment, talk to agent) deepened. broker_next_step and conversation_summary explicitly guide broker when client says "sent" or "paid."

**Biggest improvements:** (1) broker_next_step override for missing_document and payment when already_sent/paid — "Verify with carrier" / "Confirm with carrier"; (2) conversation_summary "Collected: client says already paid" and "policy/bill sent"; (3) add-car and renewal broker_next_step more concrete at handoff; (4) P2-M1, P2-C1 audit cases lock in behavior.

**Biggest remaining weaknesses:** Add-car broker_next_step could include actual values; remove-car and claim not deepened this sprint.

**Whether direction is correct:** Yes. Focus on reducing broker rework and making handoff more actionable.

**Best next recommendation:** Package 2.1 — deepen remove-car or claim; or config extraction for easier tuning.

**Current IT technical backbone / stack:** Python backend (FastAPI, fiqa_api), triage module (rule + optional LLM), configs (markers, handoff phrases), React/Vite frontend, Vercel + Cloud Run deploy.

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事
现有套餐可卖，但客户说「发过了」「付了」时，经纪人收到的 handoff 不够明确。Package 2.0 把「核实」写进 broker_next_step，减少经纪人重复追问。

### 主要用了什么方法/技术
在 triage_conversation 中，当 handoff 且 already_sent/paid 时，覆盖 broker_next_step 为更具体的操作句；增强 conversation_summary 对「已付」「已发」的区分；add-car 和 renewal 的 broker_next_step 更具体；新增 P2-M1、P2-C1 审计用例。

### 这轮最大的提升
broker_next_step 在「客户说发了/付了」时，明确告诉经纪人「与 carrier 核实是否收到；若未收到，今日处理」。

### 现在还差什么
add-car 的 broker_next_step 可进一步包含具体 year/model/zip；remove-car、claim 深化留待 2.1。

---

## 18. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作
- Phase A: 创建 7 份控制文档（Blueprint, Scenario Selection, Handling Matrix, Conversation/Handoff Spec, Execution Outline, Acceptance Criteria, Founder Inspection Notes）
- Baseline audit
- Loop 1: broker_next_step + summary 对 already_sent/paid 的增强
- Loop 2: renewal summary "policy/bill sent"；add-car 和 renewal broker_next_step 更具体
- Loop 3: P2-M1、P2-C1 审计用例

### 哪些地方比原系统提高了
- broker_next_step 在 missing_document、payment 的 already_sent/paid 场景下更明确
- conversation_summary 区分 "client says already paid" 与 "client says sent notice/screenshot"
- renewal summary "policy/bill sent" 当客户明确发送时
- add-car、renewal 的 broker_next_step 更具体

### 每一轮大概花了哪些时间 / 精力
- Loop 1: ~15 min（代码修改 + 测试）
- Loop 2: ~10 min（代码修改 + 测试）
- Loop 3: ~5 min（审计用例 + 验证）

### 还有哪些值得下一轮继续做
- Package 2.1: remove-car、claim 深化
- add-car broker_next_step 包含具体 year/model/zip
- config 提取便于调参

---

*End of Standard Scenario Package 2.0 Report*
