# Configuration Layer / Reusable Template Foundation Report

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Date:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

**What was chosen:** Establish the first real reusable template/configuration layer by clearly separating common base, insurance industry config, and client-specific config.

**Why now:** The product has reached trial readiness. To sell to multiple brokers or SMB clients, the system must feel like a configurable vertical product rather than a Chen Kui custom project. The next most valuable move is a practical configuration foundation—not a no-code platform, but a clear layering that makes reuse credible.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Configuration Foundation Blueprint | `docs/sprints/CONFIGURATION_LAYER_SPRINT/01_CONFIGURATION_FOUNDATION_BLUEPRINT.md` |
| Base vs Industry vs Client Boundary Spec | `docs/sprints/CONFIGURATION_LAYER_SPRINT/02_BASE_VS_INDUSTRY_VS_CLIENT_BOUNDARY_SPEC.md` |
| Reusable Configuration Inventory Spec | `docs/sprints/CONFIGURATION_LAYER_SPRINT/03_REUSABLE_CONFIGURATION_INVENTORY_SPEC.md` |
| Configuration Migration / Extraction Spec | `docs/sprints/CONFIGURATION_LAYER_SPRINT/04_CONFIGURATION_MIGRATION_EXTRACTION_SPEC.md` |
| Execution Outline | `docs/sprints/CONFIGURATION_LAYER_SPRINT/05_EXECUTION_OUTLINE.md` |
| Acceptance / Reusability Criteria | `docs/sprints/CONFIGURATION_LAYER_SPRINT/06_ACCEPTANCE_REUSABILITY_CRITERIA.md` |
| Founder Inspection Notes | `docs/sprints/CONFIGURATION_LAYER_SPRINT/07_FOUNDER_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

### Current Reusability State (Before Sprint)

| Layer | Status |
|-------|--------|
| **Common** | Empty (README only); workflow fallbacks hardcoded in triage.py |
| **Industry** | Partial: markers.json, reply_templates.json, add_car_rules.json; broker_next_step/client_prep hardcoded |
| **Client** | Partial: handoff_phrases.json, reply_overrides.json; UI copy hardcoded |

### Biggest Weakness

broker_next_step and client_prep were fully hardcoded in `_get_category_templates` (12+ categories). This is the highest-value extraction target because it directly affects broker-facing guidance and is reused across all triage flows.

### Biggest Custom-Project Signal

"陈奎办公室" and "办公室会尽快处理" scattered in triage and UI. Handoff phrases are configurable, but fallbacks and UI copy remain Chen Kui–specific.

### Biggest Barrier to Future Client Reuse

No common layer; industry guidance mixed with code; no documented client UI copy structure. Adding a second broker required guessing what to change.

---

## 4. 10–20 Point Breakdown

1. **Current common/base layer elements:** Intake skeleton, case store, workflow conventions, shared test framework. No config files before sprint.
2. **Current industry-specific elements:** markers.json, reply_templates.json, add_car_rules.json; now + category_templates.json.
3. **Current client-specific elements:** handoff_phrases.json, reply_overrides.json; now + ui_copy.json (structure).
4. **What is wrongly mixed today:** broker_next_step fallbacks (now in common); some UI copy still hardcoded.
5. **Top hardcoded items extracted:** broker_next_step, client_prep → category_templates.json; generic fallbacks → workflow_defaults.json.
6. **Copy/phrases now configurable:** Per-category broker guidance; generic fallbacks.
7. **Scenario definitions:** Remain in STANDARD_SCENARIO_PACKAGE.md; config structure supports future scenario package config.
8. **Handoff/workbench labels:** handoff_phrases already config; ui_copy.json documents UI labels for future loading.
9. **What remains hardcoded:** customer_question broker_next_step/client_prep (dynamic); missing_document client_prep (dynamic); classification logic; UI copy (structure in config, loading deferred).
10. **Too risky to extract now:** Classification logic; handoff thresholds; VALID_CATEGORIES.
11. **Helps future A/B/C client reuse:** New broker = configs/clients/new_broker/ with handoff_phrases, reply_overrides, ui_copy.
12. **Sales credibility:** "We have a template; Chen Kui is one configuration" is now defensible.
13. **Internal maintainability:** Config changes do not require code deploy for broker_next_step, client_prep, fallbacks.
14. **Tests/guardrails needed:** guardrail_inbox_triage.sh; run_inbox_triage_scenarios; run_multi_turn_simulations. All pass.
15. **Deployment impact:** Backend redeploy needed for production to use new config; frontend unchanged.
16. **Intentionally deferred:** Runtime client/industry switch; full UI config loading; handoff thresholds in config.
17. **What makes this a real template foundation:** Clear common/industry/client layout; category_templates and workflow_defaults in config; documented extraction path.
18. **Next platformization step:** Wire UI to load ui_copy.json; add runtime client selection (env or API param).

---

## 5. Iteration Loop 1

**What config problems were fixed:** broker_next_step and client_prep were fully hardcoded in triage.py for 10+ categories.

**Why these fixes were chosen:** Highest-value extraction; directly improves broker-facing guidance; tunable without code change.

**What became more reusable:** Per-category broker guidance is now in `configs/industries/insurance/category_templates.json`. customer_question and missing_document (dynamic) remain in code by design.

**What did not improve:** UI copy; common fallbacks (addressed in Loop 2).

**Whether it was worth it:** Yes. 64/64 scenarios pass; guardrail PASS. Clear win.

---

## 6. Iteration Loop 2

**What config problems were fixed:** Generic fallbacks (broker_next_step, client_prep, client_reply_draft) were hardcoded in _rule_based_triage.

**Why these fixes were chosen:** Establishes the common layer; completes the base/industry/client stack.

**What improved vs loop 1:** Common layer now has real config (workflow_defaults.json). Fallbacks load from config.

**What still remained weak:** UI copy; client ui_copy structure (addressed in Loop 3).

**Whether it was worth it:** Yes. Common layer is no longer a placeholder.

---

## 7. Iteration Loop 3

**What template-foundation problems were fixed:** No documented client UI copy structure; config READMEs incomplete.

**Why these fixes were chosen:** ui_copy.json documents what belongs in client config; READMEs and CONFIG_EXTRACTION_GUIDE updated for discoverability.

**What improved vs loop 2:** Stronger config inventory; clearer documentation; ui_copy.json as target for future UI loading.

**What still remained weak:** UI does not yet load ui_copy.json; that would require API + React changes.

**Whether it was worth it:** Yes. Config structure is now complete; next step is clear.

---

## 8. Optional Loop 4

**Whether used:** No.

**Reason:** No clearly valuable, low-risk refinement remained. Wiring UI to ui_copy would be a larger change; better as a follow-up sprint.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios | 64/64 passed |
| run_multi_turn_simulations | 41/41 strong |
| guardrail_inbox_triage.sh | PASS |
| ui npm run build | Success |

**Limitations:** API test skipped (no server on 8001). Production behavior not verified live.

---

## 10. Deployment / Release Judgment

| Component | Redeploy needed? | Notes |
|-----------|------------------|-------|
| **Backend** | Yes | config_loader + triage changes; new config files. Cloud Run redeploy for production. |
| **Frontend** | No | No UI code changes. |

**Founder can inspect:** Yes. Run `bash scripts/guardrail_inbox_triage.sh`; inspect `configs/common/`, `configs/industries/insurance/category_templates.json`, `configs/clients/chen_kui/ui_copy.json`.

---

## 11. Founder Showcase

### Example 1: broker_next_step and client_prep

**What is now configurable:** Per-category broker guidance (cancellation_warning, payment_lapse_expiration, missing_document, etc.) in `configs/industries/insurance/category_templates.json`.

**Why this is better:** Broker can tune guidance without code change. Another insurance broker can use the same industry pack or override.

**Why this helps future client reuse:** New broker = same industry config; optional client overrides in reply_overrides.

**Why this helps sales:** "We have configurable broker guidance; you can adjust the wording" is a credible claim.

### Example 2: Common workflow fallbacks

**What is now configurable:** Generic broker_next_step, client_prep, client_reply_draft when category-specific config is missing.

**Why this is better:** Platform-level defaults live in config, not code.

**Why this helps future client reuse:** Common layer is real; industry and client layers override as needed.

**Why this helps sales:** "We have a three-layer config: common, industry, client" is explainable.

### Example 3: Client UI copy structure

**What is now configurable:** ui_copy.json documents app title, office label, quick-start buttons. (UI loading deferred.)

**Why this is better:** Clear target for future UI config; another broker knows what to customize.

**Why this helps future client reuse:** New broker = new ui_copy.json with their wording.

**Why this helps sales:** "Your branding and labels go in your config folder" is a clear story.

---

## 12. Final Judgment

**Biggest gain:** broker_next_step and client_prep extracted to config; common layer established; config structure complete.

**Biggest remaining weakness:** UI still hardcoded; ui_copy.json not yet loaded by frontend.

**Whether this meaningfully improves reusability:** Yes. The product is now clearly layered; adding another broker is adding a config folder, not editing code.

**Best next step:** Wire UI to load ui_copy.json (API + React); or add runtime client selection for multi-client demos.

---

## 13. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Recommended next |
|------|--------------|-----------------|----------------------|-----------|------------------|
| 1 | category_templates.json; config_loader; triage reads config | broker_next_step/client_prep configurable | UI; common layer | Yes | Loop 2 |
| 2 | workflow_defaults.json; config_loader; triage uses fallbacks | Common layer real | UI copy | Yes | Loop 3 |
| 3 | ui_copy.json; README updates; CONFIG_EXTRACTION_GUIDE | Config inventory complete; docs accurate | UI loading | Yes | Wire UI to ui_copy |
| 4 | Not used | — | — | — | Stop; no low-risk refinement |

---

## 14. 中文宏观总结

**为什么现在做配置化第一步：** 产品已到试用就绪，但要卖给更多经纪人，必须从「陈奎定制项目」变成「可配置的垂直产品」。配置层是下一步最有价值的动作。

**我们用了什么主要方法/技术：** 三层配置（common / industry / client）、从 triage.py 提取 broker_next_step 和 client_prep 到 category_templates.json、建立 common workflow_defaults、用 ui_copy.json 定义客户端 UI 文案结构。

**这轮最大提升：** broker_next_step 和 client_prep 从代码迁移到配置；common 层从空壳变为有实际文件；配置结构完整、文档清晰。

**还差什么：** UI 尚未从配置加载文案；ui_copy.json 目前仅作文档用途。下一步可做 UI 配置加载或运行时客户切换。

**下一步最该做什么：** 让 UI 加载 ui_copy.json，或增加运行时客户选择，以支持多客户演示。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest template/config improvement:** broker_next_step and client_prep are now in config (category_templates.json); common layer has workflow_defaults.json; client ui_copy.json documents UI strings for future loading.

**Biggest remaining weakness:** UI copy still hardcoded; ui_copy.json not yet wired to frontend.

**Whether this makes the product more sellable/reusable:** Yes. "We have a configurable template; Chen Kui is one configuration" is now defensible.

**Whether redeploy is needed:** Backend yes (Cloud Run) for production. Frontend no.

**What Andy should inspect next:** configs/common/workflow_defaults.json, configs/industries/insurance/category_templates.json, configs/clients/chen_kui/ui_copy.json; run `bash scripts/guardrail_inbox_triage.sh`.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Current reusability maturity:** Medium. Three-layer config (common, industry, client) is implemented. broker_next_step, client_prep, and workflow fallbacks are config-driven. UI copy structure documented but not loaded.

**Biggest improvements:** (1) category_templates.json — per-category broker guidance in config. (2) workflow_defaults.json — common fallbacks. (3) ui_copy.json — client UI copy structure for future loading.

**Biggest remaining weaknesses:** UI does not load ui_copy.json; runtime client selection not implemented.

**Whether direction is correct:** Yes. Practical, incremental extraction; no overbuild.

**Best next recommendation:** Wire UI to load ui_copy.json via API or static import; or add env/param for client selection to support multi-client demos.

**Current IT technical backbone / stack:** Python backend (FastAPI, fiqa_api), triage module (rule + optional LLM), config_loader (common, industry, client), configs/ layout, React/Vite frontend, Vercel + Cloud Run deploy.

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品已到试用就绪，但要卖给更多经纪人，必须从「陈奎定制项目」变成「可配置的垂直产品」。配置层是下一步最有价值的动作。

### 主要用了什么方法/技术

三层配置（common / industry / client）、从 triage.py 提取 broker_next_step 和 client_prep 到 category_templates.json、建立 common workflow_defaults、用 ui_copy.json 定义客户端 UI 文案结构。

### 这轮最大的提升

broker_next_step 和 client_prep 从代码迁移到配置；common 层从空壳变为有实际文件；配置结构完整、文档清晰。

### 现在还差什么

UI 尚未从配置加载文案；ui_copy.json 目前仅作文档用途。下一步可做 UI 配置加载或运行时客户切换。
