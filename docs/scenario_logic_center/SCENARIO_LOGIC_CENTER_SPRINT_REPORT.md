# Scenario Logic Center Sprint Report

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Create a clear internal Scenario Logic Center so the founder, broker-side reviewers, and future client-config users can see the system's most important scenario logic in one place.
- **Why now:** The product has many layers (config, trial pack, fix-now queue, client wiring). The founder's pain: "We have many good parts now, but the logic is getting too spread out and harder to mentally hold." This sprint makes the system visible as a system.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| `01_SCENARIO_LOGIC_CENTER_BLUEPRINT.md` | Why a logic center; what we strengthen; what we defer |
| `02_SCENARIO_INVENTORY_SPEC.md` | Which scenarios; what each card shows; mapping to sources |
| `03_LOGIC_VISIBILITY_SPEC.md` | How to present route, ask-next, handoff, broker_next_step |
| `04_SCENARIO_STATUS_HEALTH_SPEC.md` | Strong/medium/weak; simulation coverage; fix-now/fix-next |
| `05_EXECUTION_OUTLINE.md` | Workstreams; loop plan |
| `06_ACCEPTANCE_REVIEWABILITY_CRITERIA.md` | Pass criteria for founder, broker, reuse |
| `07_FOUNDER_INSPECTION_NOTES.md` | What founder should inspect; how to use |
| `00_BASELINE_AUDIT.md` | Pre-sprint visibility state |
| `INDEX.md` | Doc index; quick links |

---

## 3. Baseline Audit

| Area | State |
|------|-------|
| **Current visibility** | Good docs (STANDARD_SCENARIO_PACKAGE, MATURE_INTAKE_SKELETON) but no single center |
| **Biggest weakness** | No single place answers: what scenarios exist, what is strong/weak, what broker does next, what varies by client |
| **Biggest "too much in Andy's head"** | Scenario-to-implementation mapping (add-car → markers + add_car_rules + handoff_phrases + triage.py) |
| **Biggest review/reuse barrier** | Broker audit: category_templates has broker_next_step by category, but customer_question is umbrella; real scenarios (add-car, premium review) are sub-intents, mapping implicit in code |

---

## 4. 10–20 Point Breakdown

1. **Which scenarios are shown** — 14: add-car, remove vehicle, add driver, missing document, payment/cancellation, billing clarification, premium review, claim intake, talk to agent, cancellation warning, english notice confusion, DMV/SR-22, bundling, unclear
2. **Why those scenarios** — Standard package 7 + trial top 5 + inbox triage categories + fix-now relevance
3. **What each scenario card shows** — Name, business goal, maturity, fix status, trial order, config layer; expandable: route, ask-next, handoff, broker_next_step, config sources
4. **Route / ask-next / handoff display** — In expandable Collapse; Descriptions with labels
5. **broker_next_step display** — Bold in expandable section
6. **Maturity/health display** — Tag: Strong (green), Medium (blue), Weak (gray)
7. **Fix-now / fix-next / defer** — Red/orange/gray Tag when applicable
8. **Common / industry / client** — Tag on each card; Alert explains industry = configs/industries/insurance, client = configs/clients/chen_kui
9. **Client-specific variation** — Config layer tag; config_sources list
10. **Simulation/trial coverage** — Trial #N badge; sim_ids in JSON (not shown in UI to avoid clutter)
11. **Still too detailed to show** — Full marker lists; LLM prompt text; per-template variants (zh_with_item, etc.)
12. **Still hardcoded** — Handoff thresholds in triage.py; VALID_CATEGORIES
13. **Directly helps founder** — One place to see all scenarios; strong/weak at a glance; config layer for planning
14. **Directly helps broker review** — broker_next_step visible; handoff timing clear
15. **Directly helps A → B reuse** — Config layer + config_sources; Alert explains new client = new folder
16. **Above the fold** — Summary (total, strong/medium/weak, trial IDs); grouped scenarios
17. **Expandable** — Route, ask-next, handoff, broker_next_step, config sources
18. **Next future version** — Editable maturity; last-changed timestamps; simulation coverage counts; link to run guardrail from UI

---

## 5. Iteration Loop 1

**What visibility problems were fixed:** No single scenario inventory; founder had to assemble from 6+ docs.

**Why these fixes were chosen:** Highest value = centralize top scenarios first; make each understandable at a glance.

**What became easier to understand:** 14 scenarios in one JSON + UI; grouped by standard_package / extended / fallback.

**What did not improve:** Route/ask-next/handoff were in expandable from start (Loop 2 scope).

**Whether it was worth it:** Yes. Founder can now list scenarios without opening code.

---

## 6. Iteration Loop 2

**What visibility problems were fixed:** Route, ask-next, handoff, broker_next_step not visible in one place; strong/medium/weak not shown; common/industry/client not distinguished.

**Why these fixes were chosen:** Operational and config visibility are core to broker audit and client reuse.

**What improved vs loop 1:** Each scenario card has expandable section with full logic; maturity and config layer badges.

**What still remained weak:** Client variation explanation was brief; added in Loop 3.

**Whether it was worth it:** Yes. Broker can now see "what do I do next?" per scenario.

---

## 7. Iteration Loop 3

**What review/clarity problems were fixed:** Config layer meaning (industry vs client) not obvious; founder inspection path unclear.

**Why these fixes were chosen:** Founder and future client reviewers need to understand what to swap for new client.

**What improved vs loop 2:** Config layers Alert; Doc index link; stronger grouping.

**What still remained weak:** Simulation coverage counts not in UI (deferred); last-changed not implemented.

**Whether it was worth it:** Yes. Founder can explain reuse more clearly.

---

## 8. Optional Loop 4

**Whether used:** No.

**Reason:** Loop 3 achieved founder clarity and broker audit value. Adding simulation counts or last-changed would be incremental; risk of overbuilding. Stopping is correct.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `cd ui && npm run build` | PASS |
| API `/api/inbox/scenario-logic-center` | Returns configs/scenario_logic_center.json |

**Limitations:** API test skipped when server not on 8001; manual verification when server running.

---

## 10. Deployment / Release Judgment

| Component | Changed | Redeploy needed |
|-----------|---------|------------------|
| Backend | New route GET /api/inbox/scenario-logic-center | Yes, if backend redeployed |
| Frontend | New page ScenarioLogicCenterPage; route; sider | Yes, if frontend redeployed |
| Config | New configs/scenario_logic_center.json | No (static; no env) |
| Docs | New docs/scenario_logic_center/* | No |

**Founder can inspect now:** Yes — open `/workbench/scenario-logic-center` (local) or deploy frontend.

---

## 11. Founder Showcase

| Example | What is now visible | Why better | Helps review/reuse | Helps planning |
|---------|---------------------|------------|--------------------|-----------------|
| Add-car / Quote | Name, goal, Strong, Trial #3, industry; expand: route, ask-next, handoff, broker step | One card vs 4 files | Broker sees "Verify vehicle details and zip; run quote" | Clear it's strong, trial-ready |
| Missing document | Name, goal, Strong, Trial #2; expand: broker_next_step "Verify whether customer-resubmitted items were received" | Operational clarity | Broker knows what to do | Trial order visible |
| Billing clarification | Fix next badge; Medium | Known gap visible | Prioritize fix-next | Plan sprint |
| Talk to Agent | Config layer: client | Client-specific handoff | New client = new handoff_phrases | Hot-swap clear |

---

## 12. Final Judgment

- **Biggest gain:** Single Scenario Logic Center — founder and broker can see what scenarios exist, what is strong/weak, what broker does next, what varies by client.
- **Biggest remaining weakness:** Handoff thresholds still in triage.py; simulation coverage counts not in UI; last-changed not implemented.
- **Whether this meaningfully improves project visibility and leadership:** Yes. The product now has a clear review/audit center. Founder mental load is lighter.
- **Best next step:** Use the center for pre-trial review and broker meetings. Consider extracting handoff thresholds to config in a future sprint if client variation needs it.

---

## 13. Iteration Log

| Loop | What changed | Better vs prior | Did not improve | Worth it? | Next step |
|------|--------------|-----------------|-----------------|----------|-----------|
| 1 | Doc set + scenario_logic_center.json + API + UI page | Single inventory; 14 scenarios | Route/handoff in expandable only | Yes | Loop 2 |
| 2 | Full logic in expandable; maturity; fix status; config layer | Operational + config visibility | Client variation brief | Yes | Loop 3 |
| 3 | Config layers Alert; Doc index | Reuse explanation | Simulation counts; last-changed | Yes | Stop |

---

## 14. 中文宏观总结

**为什么现在做 Scenario Logic Center：** 产品已有配置层、trial pack、fix-now 队列等，但逻辑分散在 6+ 文档和 5+ 配置中，创始人难以整体把握。需要有一个清晰的 Scenario Logic Center，让系统作为系统可见。

**主要用了什么方法/技术：** 文档先行（Blueprint、Inventory、Visibility、Health、Acceptance、Founder Notes）；聚合 JSON（configs/scenario_logic_center.json）；API（GET /api/inbox/scenario-logic-center）；UI 页面（ScenarioLogicCenterPage），按组展示，可展开查看 route/ask-next/handoff/broker_next_step。

**这轮最大提升：** 单一入口 — 创始人、broker 审核、未来客户迁移都能在一个地方看到：有哪些场景、每个场景做什么、强弱如何、broker 下一步做什么、common/industry/client 如何区分。

**还差什么：** handoff 阈值仍在 triage.py；simulation 覆盖数量未在 UI 展示；last-changed 未实现。可后续迭代。

**下一步最该做什么：** 用 Scenario Logic Center 做 pre-trial 审核和 broker 会议；若客户迁移需要，再考虑把 handoff 阈值提取到 config。

---

## 15. COPY/PASTE FOUNDER BLOCK

```
Scenario Logic Center Sprint — Founder Summary

Biggest improvement: Single Scenario Logic Center at /workbench/scenario-logic-center.
Shows 14 scenarios, maturity (strong/medium/weak), fix-now/fix-next/defer, route/ask-next/handoff/broker_next_step.
Config layer (industry/client) visible for reuse explanation.

Biggest remaining weakness: Handoff thresholds still in triage.py; simulation coverage counts not in UI.

Makes product more reviewable/reusable: Yes. Founder and broker can understand the system at a glance.

Redeploy needed: Backend (new API route) and frontend (new page) if deploying.

What Andy should inspect next: Open /workbench/scenario-logic-center; confirm scenarios, maturity, broker_next_step; use for pre-trial review and broker meetings.
```

---

## 16. REQUIRED CROSS-WINDOW BLOCK

```
Scenario Logic Center Sprint — Cross-Window Evaluator Block

Current project visibility maturity: Good docs (STANDARD_SCENARIO_PACKAGE, MATURE_INTAKE_SKELETON) but logic was scattered. Now: single Scenario Logic Center (doc set + JSON + API + UI) aggregates 14 scenarios with route, ask-next, handoff, broker_next_step, maturity, config layer.

Biggest improvements: (1) Single entry point for scenario logic. (2) Founder/broker can see what scenarios exist, what is strong/weak, what broker does next. (3) Common/industry/client visible for A→B client reuse.

Biggest remaining weaknesses: Handoff thresholds in code; simulation coverage counts not in UI; last-changed not implemented.

Direction correct: Yes. Clearer, not heavier. No no-code platform. Read-only review center.

Best next recommendation: Use center for pre-trial review and broker meetings. Consider extracting handoff thresholds to config if client migration needs it.

Current IT technical backbone: FastAPI backend (port 8001 default); React + Ant Design frontend; Vite build; configs in configs/ (common, industries/insurance, clients/chen_kui); triage.py 2500+ lines; Qdrant for RAG.
```

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事
产品逻辑分散在 6+ 文档和 5+ 配置中，创始人难以整体把握。需要 Scenario Logic Center 让系统作为系统可见。

### 主要用了什么方法/技术
文档先行（Blueprint、Inventory、Visibility、Health 等）；聚合 JSON；API；UI 页面按组展示，可展开查看完整逻辑。

### 这轮最大的提升
单一入口 — 14 个场景、强弱、broker 下一步、common/industry/client 在一处可见。

### 现在还差什么
手off 阈值仍在代码；simulation 覆盖数量未在 UI；last-changed 未实现。

---

## 18. REQUIRED MACRO PRINT BLOCK

```
MACRO PROJECT SUMMARY — SearchForge Chen Kui Insurance Unified Entry

1. What the product now is commercially
   Broker Standard Package: Chat + case + office follow-up. One paste → structured case. One next move. One draft to edit. 7 core scenarios (add-car, remove vehicle, missing doc, premium review, billing, claim, talk to agent). Trial-ready for Chen Kui.

2. What the IT architecture now is
   FastAPI backend (8001); React + Ant Design frontend; Vite; configs (common, industries/insurance, clients/chen_kui); triage.py (inbox_triage); case_store; Qdrant for RAG.

3. What the AI/workflow structure now is
   Detect → ask → enough? → hand off. Markers + LLM when available. Reply templates, category_templates, handoff_phrases from config. Add-car rules editable in Add-Car Rules Center.

4. What is strong now
   Standard scenario package; trial pack (SIM1–SIM5); config layer (common/industry/client); client-aware handoff; Scenario Logic Center (new); guardrail passes.

5. What is still weak
   Handoff thresholds in code; simulation coverage counts not in UI; some categories (customer_question) are umbrella, sub-intent mapping implicit.

6. What the next best step is
   Use Scenario Logic Center for pre-trial review and broker meetings. Consider extracting handoff thresholds to config if client migration needs it.
```

---

*End of Scenario Logic Center Sprint Report*
