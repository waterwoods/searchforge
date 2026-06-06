# Sellable Standard Scenario Package Report

**Sprint:** Sellable Standard Scenario Package Sprint  
**Date:** 2026-03-17  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Turn the product's strongest existing capabilities into a clearer, more sellable, more reusable standard scenario package for small insurance brokers.
- **Why now:** The product has backbone, scenario hardening, multi-turn continuity, workflow_state, case handoff, and workbench. It is strong but not yet packaged. To move from "strong evolving MVP" to "sellable standard package," packaging was the correct next move.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product Package Blueprint | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/01_PRODUCT_PACKAGE_BLUEPRINT.md` |
| Standard Scenario Package Definition Spec | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/02_STANDARD_SCENARIO_PACKAGE_DEFINITION_SPEC.md` |
| Included Scenario Matrix Spec | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/03_INCLUDED_SCENARIO_MATRIX_SPEC.md` |
| Office Workflow / Handoff Packaging Spec | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/04_OFFICE_WORKFLOW_HANDOFF_PACKAGING_SPEC.md` |
| Execution Outline | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/05_EXECUTION_OUTLINE.md` |
| Acceptance / Sellability Criteria | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/06_ACCEPTANCE_SELLABILITY_CRITERIA.md` |
| Founder Demo / Sales Inspection Notes | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/07_FOUNDER_DEMO_SALES_INSPECTION_NOTES.md` |
| Baseline Audit | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/08_BASELINE_AUDIT.md` |
| 10–20 Point Breakdown | `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/09_10_20_POINT_BREAKDOWN.md` |

**Canonical package definition:** `docs/STANDARD_SCENARIO_PACKAGE.md`

---

## 3. Baseline Audit

| Area | Status |
|------|--------|
| **Current package readiness** | Strong — inbox triage 63/63, multi-turn 40/40, adversarial 27/27, Simulation Assistant 27/27, state field 7/7, speed routing 9/9 |
| **Biggest weakness** | No single canonical package definition |
| **Biggest sellability gap** | Product explainable only to someone who has read multiple docs |
| **Biggest "still feels MVP" issue** | Workbench not explicitly sold as part of the package |

---

## 4. 10–20 Point Breakdown

1. **Package name:** Broker Standard Package
2. **Target broker/merchant profile:** Small CA auto broker; Chinese-speaking clients; 1–5 people
3. **Included scenarios:** Quote/add-car, policy change, material collection, renewal, billing, claim, talk to agent
4. **Excluded/deferred:** Email/WeChat/SMS, OCR, CRM, multi-tenant, Stripe
5. **Why these belong together:** High-frequency broker work; revenue + retention + operational + urgency
6. **Customer-side value:** Faster broker response; clearer what to send
7. **Broker-side value:** Less manual triage; fewer repetitive explanations; no lost follow-ups
8. **Office handoff value:** One next move; Collected/Still needed; client draft; follow-up memory
9. **Routing model:** FAST / LLM / Human
10. **Multi-turn expectations:** Add-car 2–3 turns; others 2 turns
11. **Case summary expectations:** conversation_summary + broker_next_step + collected/still_needed
12. **Workbench expectations:** Case focus, Your next move, Collected, Still needed, queue triage
13. **Strongest today:** Cancellation, missing doc, add-car, premium review, claim
14. **Still need another round:** Talk to agent (lightweight)
15. **Demo/prospect story:** "One paste → structured case. One next move. One draft. Workbench included."
16. **Pilot-ready enough:** Guardrail passes; 7 core scenarios; founder demo path
17. **Still not included:** Inbox sync, OCR, CRM, multi-tenant, Stripe
18. **Next packaging step:** Inbox integration; client pack customization

---

## 5. Iteration Loop 1

**What package problems were fixed:** No single canonical package definition; package story scattered across multiple docs.

**Why these fixes were chosen:** Highest sellability gain with smallest slice — create one canonical doc and wire it into entry points.

**What became more coherent:** Single `docs/STANDARD_SCENARIO_PACKAGE.md`; AGENTS.md, PROJECT_DOC_SYSTEM_MAP, CHEN_KUI_TRIAL_PACK now reference it.

**What became more sellable:** Founder can point to one file for "what we're selling."

**What did not improve:** Office-side framing; founder demo path.

**Whether it was worth it:** Yes.

---

## 6. Iteration Loop 2

**What package problems were fixed:** Workbench not explicitly framed as part of the package; "chat only" vs "chat + case + office" unclear.

**Why these fixes were chosen:** Office value is commercially critical; package must feel operational, not just conversational.

**What improved vs loop 1:** STANDARD_SCENARIO_PACKAGE.md now has "What it is: Chat + case + office follow-up"; expanded "What the Office Gets" with table; UNIFIED_INTAKE_MVP_RUNBOOK references package.

**What still remained weak:** Founder demo checklist; package-level guardrail.

**Whether it was worth it:** Yes.

---

## 7. Iteration Loop 3

**What package problems were fixed:** Founder demo path not explicit; no package-level guardrail.

**Why these fixes were chosen:** Founder needs a 5–10 min checklist; guardrail ensures package doc is not accidentally removed.

**What improved vs loop 2:** Founder Demo Checklist (5–10 min) in STANDARD_SCENARIO_PACKAGE.md; guardrail step 9 verifies package doc exists; 10–20 point breakdown doc for quick reference.

**What still remained weak:** None critical for this sprint.

**Whether it was worth it:** Yes.

---

## 8. Optional Loop 4

**Whether used:** No.

**Reason:** No clearly valuable, low-risk refinement remained. Package definition is complete; office framing is clear; founder demo path exists; guardrail is in place. Stopping is correct.

---

## 9. Validation Summary

| Test | Result |
|------|--------|
| `run_inbox_triage_scenarios.py` | 63/63 passed |
| `run_multi_turn_simulations.py` | 40/40 passed |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `verify_speed_routing.py` | 9/9 OK |
| `guardrail_inbox_triage.sh` | PASS (including new step 9) |
| `unified_intake_smoke_check.sh` | Guardrail passes; manual UI steps printed |
| `cd ui && npm run build` | Built successfully |

**Limitations:** API test skipped (no server on 8001). LLM-enabled runs not executed (would require API key).

---

## 10. Deployment / Release Judgment

| Area | Judgment |
|------|----------|
| **Backend** | No backend code changed. Redeploy not needed. |
| **Frontend** | No frontend code changed. Redeploy not needed. |
| **Docs** | New docs + edits to AGENTS.md, PROJECT_DOC_SYSTEM_MAP, CHEN_KUI_TRIAL_PACK, guardrail. No deployment required. |
| **Founder can inspect now** | Yes. Read `docs/STANDARD_SCENARIO_PACKAGE.md` and run demo path. |

---

## 11. Founder Showcase

### Scenario 1: Cancellation risk

- **What the customer experiences:** Pastes "这个英文 notice 说 payment failed，我现在怎么办？" → system asks for notice/screenshot → customer says "我发了截图在微信" → handoff.
- **What the office gets:** Case focus: Payment risk. Your next move: Confirm balance due. Same-day action. Client reply draft.
- **Why commercially useful:** Urgency; same-day broker action; reduces missed follow-ups.
- **Why in standard package:** Highest-frequency urgency scenario.

### Scenario 2: Missing document

- **What the customer experiences:** "UW follow up - need dec page + garaging proof. 上周发过了" → system clarifies → customer says "declaration page 他又发了一次，garaging proof 还没弄" → handoff.
- **What the office gets:** Case focus: Missing document. Your next move: Verify receipt; request garaging proof. Collected: dec page sent. Still needed: garaging proof.
- **Why commercially useful:** "Client says already sent" is common pain; structured follow-up reduces back-and-forth.
- **Why in standard package:** Operational; high-frequency.

### Scenario 3: Add-car quote

- **What the customer experiences:** "我买了台宝马X5，想问下保费多少钱" → system asks year, zip → "2024年的" → "90210，下周提车" → handoff.
- **What the office gets:** Case focus: Add car quote. Collected: year, model, zip, delivery. Still needed: driver (optional). Client reply draft: "报价资料已收集，办公室会尽快出价"
- **Why commercially useful:** Revenue; multi-turn collection; broker sees what's collected.
- **Why in standard package:** Revenue; strongest multi-turn proof.

---

## 12. Final Judgment

| Item | Assessment |
|------|------------|
| **Biggest gain** | Single canonical package definition; workbench explicitly part of package; founder demo checklist |
| **Biggest remaining weakness** | Talk to agent scenario is lightweight; some edge cases |
| **Whether this now feels like a sellable standard package** | Yes. Package is defined, coherent, and explainable. |
| **Best next step** | Inbox integration or client pack customization for next broker. |

---

## 13. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Recommended next step |
|------|--------------|-----------------|----------------------|-----------|------------------------|
| 1 | Created STANDARD_SCENARIO_PACKAGE.md; wired into AGENTS, PROJECT_DOC_SYSTEM_MAP, CHEN_KUI_TRIAL_PACK | Package has single source of truth | Office framing | Yes | Loop 2 |
| 2 | Expanded office section; "Chat + case + office"; runbook package reference | Workbench part of package | Founder demo path | Yes | Loop 3 |
| 3 | Founder Demo Checklist; guardrail step 9; 10–20 point breakdown | Demo path explicit; package guardrail | — | Yes | Stop |
| 4 | Not used | — | — | — | — |

---

## 14. 中文宏观总结

**为什么现在做这个标准场景包：** 产品已有很强的能力（多轮、工作台、handoff），但"强"不等于"好卖"。要从小型经纪人付费试用，必须把现有能力打包成清晰、可解释、可复用的标准包。

**我们用了什么主要方法/技术：** 文档先行：创建 7 份控制文档 + 1 份标准包定义；三轮迭代：定义包 → 强化办公室侧 → 强化创始人 demo 路径；最小改动：不新增功能，只做包装和引用。

**这轮最大的提升：** 有了单一 canonical 的 `STANDARD_SCENARIO_PACKAGE.md`；工作台明确作为包的一部分；创始人 5–10 分钟 demo 路径；guardrail 增加包定义检查。

**还差什么：** Talk to agent 场景较轻；部分 edge case；inbox 集成、client pack 定制是下一步。

**下一步最该做什么：** 对接下一个经纪人时做 client pack 定制；或做 inbox 集成（如 WeChat/email 粘贴入口）。

---

## 15. COPY/PASTE FOUNDER BLOCK

```
Biggest package improvement: Single canonical STANDARD_SCENARIO_PACKAGE.md; workbench explicitly part of package; founder demo checklist (5–10 min).

Biggest remaining weakness: Talk to agent scenario lightweight; some edge cases.

Makes product more sellable/reusable: Yes. Package is defined, coherent, explainable.

Redeploy needed: No. Docs + guardrail only.

What Andy should inspect next: Read docs/STANDARD_SCENARIO_PACKAGE.md; run demo path (Load founder demo queue → cancellation → missing doc → add-car); confirm one-sentence offer feels right.
```

---

## 16. REQUIRED CROSS-WINDOW BLOCK

```
Current package maturity: Package defined; 7 core scenarios; workbench part of package; founder demo path; guardrail includes package check.

Biggest improvements: (1) Single canonical STANDARD_SCENARIO_PACKAGE.md; (2) Office/workbench explicitly part of package; (3) Founder Demo Checklist; (4) Guardrail step 9.

Biggest remaining weaknesses: Talk to agent lightweight; inbox integration deferred.

Direction correct: Yes. Packaging over new features was the right move.

Best next recommendation: Client pack customization for next broker; or inbox integration.

Current IT technical backbone/stack: Python backend (fiqa_api); Vite/React frontend; inbox triage API; multi-turn simulations; Qdrant for RAG; Cloud Run + Vercel deploy.
```

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品已有强能力，但"强"不等于"好卖"。要从小型经纪人付费试用，必须把现有能力打包成清晰、可解释、可复用的标准包。

### 主要用了什么方法/技术

文档先行（7 份控制文档 + 1 份标准包定义）；三轮迭代（定义包 → 强化办公室侧 → 强化创始人 demo）；最小改动（不新增功能，只做包装）。

### 这轮最大的提升

单一 canonical 的 STANDARD_SCENARIO_PACKAGE.md；工作台明确作为包的一部分；创始人 5–10 分钟 demo 路径；guardrail 增加包定义检查。

### 现在还差什么

Talk to agent 场景较轻；inbox 集成、client pack 定制是下一步。

---

## 18. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

- Phase A: 创建 7 份控制文档
- Baseline audit: 分类场景，识别最大包装弱点
- Loop 1: 创建 STANDARD_SCENARIO_PACKAGE.md，接入 AGENTS/PROJECT_DOC_SYSTEM_MAP/CHEN_KUI_TRIAL_PACK
- Loop 2: 强化办公室侧，工作台作为包的一部分
- Loop 3: Founder Demo Checklist，guardrail 包检查，10–20 点 breakdown

### 哪些地方比原系统提高了

- 包装清晰度：单一 canonical 包定义
- 办公室价值：工作台明确作为包的一部分
- 创始人 demo：5–10 分钟路径明确
- 可维护性：guardrail 确保包定义存在

### 每一轮大概花了哪些时间 / 精力

- Phase A + Baseline: ~15 min（文档创建）
- Loop 1: ~10 min（包定义 + 引用）
- Loop 2: ~5 min（办公室强化）
- Loop 3: ~5 min（demo 路径 + guardrail）
- 报告: ~10 min

### 还有哪些值得下一轮继续做

- Client pack 定制（下一个经纪人）
- Inbox 集成（WeChat/email 粘贴入口）
- Talk to agent 场景强化

---

*End of Sellable Standard Scenario Package Report*
