# Unified Intake System Scouting + Completion Review Report

**Sprint:** Unified Intake System Scouting + Completion Review Sprint  
**Date:** 2026-03-11  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry (mainline only)

---

## 1. Core file map

### Backend / logic

| Path | Purpose |
|------|---------|
| `services/fiqa_api/inbox_triage/triage.py` | **Core triage engine** — 1726 lines. Rule-based classification (LLM optional), intent detection, reply templates, progressive multi-turn logic, structured field extraction (add-car, renewal, claim, missing-document), handoff threshold, conversation summary. |
| `services/fiqa_api/inbox_triage/case_store.py` | **Lightweight case persistence** — JSON file under `data/unified_intake_cases.json`. Save, list, update status, follow-up, notes. Max 200 cases, 20 notes, 40 activity entries per case. |
| `services/fiqa_api/inbox_triage/config_loader.py` | **Config loader** — Loads markers, reply_templates, handoff_phrases, reply_overrides from `configs/`. Industry + client merge. Falls back to hardcoded defaults when missing. |
| `services/fiqa_api/inbox_triage/knowledge_paths.py` | **Knowledge layer paths** — Reference paths for common/industry/client `.md` files. Used for future ingestion; triage does not use RAG today. |
| `services/fiqa_api/inbox_triage/notice_retrieval.py` | **Retrieval-assisted explanation** — Notice confusion + document confusion. Uses Qdrant for DMV/SR-22, declaration page, garaging proof. Returns None when embedder/Qdrant not ready. |
| `services/fiqa_api/routes/inbox_triage.py` | **API routes** — POST `/api/inbox/triage`, GET `/api/inbox/cases`, PATCH status, POST notes, PATCH follow-up. |

### Frontend / workbench / queue

| Path | Purpose |
|------|---------|
| `ui/src/pages/UnifiedIntakePage.tsx` | **Single-page UI** — ~1300 lines. Tab A: Customer Entry (conversational intake). Tab B: Broker Workbench (paste, triage, case card, queue). |
| `ui/src/api/inboxTriage.ts` | **API client** — triageMessage, listRecentCases, updateSavedCaseStatus, addSavedCaseNote, updateSavedCaseFollowUp. |

### Config / templates / client pack

| Path | Purpose |
|------|---------|
| `configs/industries/insurance/markers.json` | Intent markers (question_help, strong_cancellation, add_vehicle, etc.) + document_items. |
| `configs/industries/insurance/reply_templates.json` | First-turn reply templates (zh/en) per category. |
| `configs/clients/chen_kui/handoff_phrases.json` | Handoff wording when case ready for broker (add_car, remove_car, other, etc.). |
| `configs/clients/chen_kui/reply_overrides.json` | Empty overrides; placeholder for client-specific reply tweaks. |

### Knowledge / retrieval

| Path | Purpose |
|------|---------|
| `knowledge/industries/insurance/` | DMV/SR-22, declaration page, garaging proof, notice interpretation. |
| `knowledge/common/`, `knowledge/clients/chen_kui/` | README placeholders. |
| `scripts/ingest_insurance_knowledge.py` | Ingestion into Qdrant. |
| `scripts/build_demo_core_collection.py` | Build demo collection. |

### Simulation / testing / regression

| Path | Purpose |
|------|---------|
| `configs/inbox_triage_scenarios.json` | Single-turn scenario pack (S1–S12+). |
| `configs/customer_entry_multi_turn_simulations.json` | Multi-turn simulations (add-car, remove-car, premium, etc.). |
| `configs/expression_robustness_cases.json` | Expression robustness. |
| `configs/adversarial_real_user_scenarios.json` | Messy user inputs. |
| `configs/mixed_intent_scenarios.json` | Mixed-intent (e.g. payment + document). |
| `configs/long_context_memory_shift_simulations.json` | Long-context / corrections. |
| `scripts/run_inbox_triage_scenarios.py` | Single-turn scenario runner. |
| `scripts/run_multi_turn_simulations.py` | Multi-turn runner. |
| `scripts/run_adversarial_simulation.py` | Adversarial runner. |
| `scripts/run_complex_adversarial_simulation.py` | Mixed-intent + long-context runner. |
| `scripts/guardrail_inbox_triage.sh` | 7-step guardrail: scenario pack, scenario runner, API test, case persistence, multi-turn, adversarial, complex adversarial. |
| `scripts/unified_intake_smoke_check.sh` | Guardrail + manual UI smoke steps. |

### Docs / product map

| Path | Purpose |
|------|---------|
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Doc map, goals, runbooks, guardrails. |
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Per-category reply strategy. |
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Case focus, Your next move, Collected/Still needed, queue triage. |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Demo story, best flows, what to say. |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Dev loop, scenario runner, commands. |
| `docs/BROKER_REPORTS_INDEX.md` | Sprint reports index. |

---

## 2. Major modules

| Module | Purpose |
|--------|---------|
| **Triage engine** | Classify inbound text, assign urgency, produce broker_next_step, client_prep, client_reply_draft. Rule-based primary; LLM optional when enabled. |
| **Progressive intake** | Multi-turn: detect → ask 1–2 next things → enough? → hand off. Add-car, renewal, claim, missing-document have structured extraction. |
| **Case store** | Persist triage results as lightweight cases; status, waiting_on, next_contact_by, notes, activity. |
| **Customer Entry** | Simple conversational UI: paste → reply → continue → handoff. |
| **Broker Workbench** | Paste → triage → case card → copy draft → status update → follow-up → notes → queue. |
| **Config layer** | Markers, reply templates, handoff phrases from config. Industry + client merge. |
| **Retrieval** | Optional augmentation for notice/document confusion. Uses Qdrant; falls back to template when retrieval fails. |
| **Simulation / guardrail** | 7-step guardrail: single-turn, multi-turn, adversarial, complex adversarial, case persistence, API. |

---

## 3. Completion review by module

### Customer Entry / Unified front-end intake

| Aspect | Maturity | Strong | Partial | Weak |
|--------|----------|--------|---------|------|
| **Overall** | **Good but partial** | Same-page conversational flow; 5 flows (add-car, renewal, claim, notice/payment, missing doc); multi-turn with progressive ask; handoff phrasing; 客户入口 / 办公室 labels. | No image upload; no OCR; no persistence of conversation across sessions; no real CRM integration. | Edge cases (very fragmented inputs); no explicit "session" concept. |

### Broker Workbench

| Aspect | Maturity | Strong | Partial | Weak |
|--------|----------|--------|---------|------|
| **Overall** | **Good but partial** | Paste-first triage; case card with urgency, next move, client prep, draft; Collected/Still needed chips for 4 flows; status, follow-up, notes; Work now / Waiting or parked; founder demo queue. | Local-only persistence; no assignments, no notifications; no CRM integration. | No bulk actions; no search/filter; no export. |

### Structured intake

| Aspect | Maturity | Strong | Partial | Weak |
|--------|----------|--------|---------|------|
| **Overall** | **Strong** | Add-car: year, make_model, zip, delivery_date, primary_driver, vin. Renewal: premium_concern, renewal_context, remove_vehicle_interest, policy_bill_sent. Claim: accident_reported, hit_and_run, photos, other_driver_info. Missing Document: requested_*, customer_says_sent_*, verify_carrier_received. | Extraction is regex/keyword-based; some edge cases. | No schema validation; no formal "structured payload" beyond chips. |

### Queue triage

| Aspect | Maturity | Strong | Partial | Weak |
|--------|----------|--------|---------|------|
| **Overall** | **Good but partial** | Attention labels (Action now, Your move, Due today); readiness (Ready to act / Needs more info / Verify receipt); Work now vs Waiting or parked; compact flow-specific preview. | Sorting by score; no filters; no search. | No due-date reminders; no overdue escalation. |

### Retrieval / knowledge layer

| Aspect | Maturity | Strong | Partial | Weak |
|--------|----------|--------|---------|------|
| **Overall** | **Early / foundational** | Two retrieval paths: notice confusion + document confusion. Knowledge files: DMV/SR-22, declaration page, garaging proof. Graceful fallback when retrieval unavailable. | Retrieval is optional; triage does not depend on RAG. | Knowledge corpus small; ingestion scripts exist but not integrated into CI; no automated validation of retrieval quality. |

### Simulation / regression / guardrail system

| Aspect | Maturity | Strong | Partial | Weak |
|--------|----------|--------|---------|------|
| **Overall** | **Strong** | 7-step guardrail; single-turn, multi-turn, adversarial, complex adversarial packs; case persistence check; API test. | API test optional (server must be running); no E2E browser automation. | No coverage metrics; no regression trend tracking. |

---

## 4. Unified front-end intake status

### What it can do now

- **Customer Entry tab:** One input, conversational flow. Customer pastes → system replies with intent-specific draft (add-car, payment risk, notice confusion, missing document, claim, DMV/SR-22) → customer can continue → handoff when enough info or after 2–3 turns.
- **Multi-turn:** Progressive ask (1–2 items per turn, not a 6-item checklist). Acknowledges what customer said (e.g. "好的，2024年的。") before asking next.
- **Handoff:** "办公室会尽快处理" + handoff phrasing; "查看工作台" to switch to broker view.
- **Broker Workbench:** Paste → triage → case card → copy draft → status update → follow-up → notes → queue with Work now / Waiting or parked.

### "Real office front desk" feeling

- **Already:** Intent-specific replies (not generic "provide more context"); Chinese + English; broker-natural phrasing; urgency tags; handoff flow.
- **Partial:** No OCR; no image upload; no real CRM; no persistence of conversation across sessions; no "session" concept.

### What still blocks full maturity

- No image/OCR upload; no attachment parsing.
- No multi-message thread context (e.g. WeChat history).
- No customer identity or case history.
- No automatic outbound communication.
- No explicit "session" or persistence of conversation across page reloads.

---

## 5. Overall product completion view

| Tier | What | Examples |
|------|------|----------|
| **Product-grade** | Triage logic, config layer, case store, API, structured intake (4 flows), guardrail, demo flow. | Paste → triage → case card → copy draft → status → follow-up → notes. |
| **MVP-grade** | Customer Entry UI, Broker Workbench, queue triage, multi-turn, founder demo queue. | Ready for founder demo; repeatable walkthrough. |
| **Pre-polish** | Retrieval (optional, fallback); knowledge ingestion; E2E automation. | Retrieval works when Qdrant + embedder ready; no CI for ingestion. |

**Can demo to a real person:** Yes. Best flows: cancellation risk, missing document, add-car, premium review, claim intake, English notice + Chinese confusion. Best order: load founder demo queue → cancellation risk → reopen missing-document → add-car or premium review.

---

## 6. Messy / duplicated / confusing areas

| Area | Issue |
|------|-------|
| **triage.py size** | 1726 lines; many helpers (`_build_client_reply_draft`, `_get_category_templates`, `_classify_with_guardrails`, etc.). Logic is dense but coherent; refactor would help. |
| **Docs volume** | Many sprint reports in `docs/`; BROKER_REPORTS_INDEX lists 30+; archive boundary exists but some overlap. |
| **Config vs code** | Clear boundaries (markers, templates, handoff in config). Some hardcoded fallbacks in triage.py when config is empty. |
| **Retrieval** | Optional; triage works without it. Fallback when retrieval fails is clear; but integration path (ingestion, CI) is unclear. |
| **Reply templates** | Industry templates + client overrides; `reply_overrides.json` is empty; structure is clear. |

---

## 7. Best next step

**Recommendation: Tighten broker memory and reopen UX without crossing into CRM.**

**Why it matters most:**

- Demo is strong; the next gap is daily use. Brokers need to reopen cases quickly and see "where this case stands" without re-reading everything.
- The case card already has follow-up, notes, activity. The reopen surface and queue could be tightened so the broker can decide "what to do next" faster.

**Why now:**

- Core flows are done; triage, structured intake, and guardrail are stable. The next value is incremental improvement of the broker workflow, not new features.

**What it unlocks:**

- Fewer clicks to reopen and act.
- Clearer "where this case stands" without opening every card.
- Safer clear/reset or due-state labeling.

**Concrete scope:**

- Improve due-state labeling (e.g. "Follow-up overdue" vs "Due today").
- Tighten reopen surface around existing follow-up context.
- Consider one small helper (e.g. clearer "what to do next" when reopening).
- Do **not** add: assignments, automation, notifications, full CRM.

---

## 8. 中文宏观总结

### 核心文件都在哪

- **后端:** `services/fiqa_api/inbox_triage/triage.py`（核心逻辑）、`case_store.py`（案例存储）、`config_loader.py`（配置）、`notice_retrieval.py`（检索增强）
- **前端:** `ui/src/pages/UnifiedIntakePage.tsx`、`ui/src/api/inboxTriage.ts`
- **配置:** `configs/industries/insurance/markers.json`、`reply_templates.json`、`configs/clients/chen_kui/handoff_phrases.json`
- **知识库:** `knowledge/industries/insurance/`（DMV、声明页、garaging proof 等）
- **测试:** `scripts/guardrail_inbox_triage.sh`、`run_inbox_triage_scenarios.py`、`run_multi_turn_simulations.py` 等

### 现在已经做成了哪些大块

1. **Triage 引擎** — 规则为主、LLM 可选；分类、优先级、broker 下一步、客户准备、回复草稿
2. **渐进式 intake** — 多轮对话，按 1–2 项追问；add-car、renewal、claim、missing-document 有结构化提取
3. **案例存储** — 本地 JSON 持久化；状态、follow-up、笔记、活动
4. **客户入口** — 统一入口，对话式界面，多轮后 handoff
5. **Broker Workbench** — 粘贴 → triage → 案例卡 → 复制草稿 → 状态、follow-up、笔记

### 用户统一入口做到了什么程度

- **已做到:** 对话式输入；多轮追问；按意图回复（加车、报价、付款风险、通知困惑、缺材料、理赔等）；中英双语；handoff 后「办公室会尽快处理」
- **未做到:** 图片上传、OCR；多会话持久化；CRM 集成

### 后台 workbench 做到了什么程度

- **已做到:** 粘贴 → triage → 案例卡；Collected/Still needed 芯片；状态、follow-up、笔记；Work now / Waiting or parked 队列；founder demo 队列
- **未做到:** 分配、通知、CRM 集成；批量操作；搜索/筛选

### 测试和回归保护做到了什么程度

- **已做到:** 7 步 guardrail（单轮、多轮、对抗、复杂对抗、案例持久化、API）；场景包完整
- **未做到:** 覆盖率指标；E2E 浏览器自动化；回归趋势

### 现在最大的缺口是什么

- **Broker 日常使用体验** —  reopen 后快速判断「下一步做什么」；due-state 更清晰；避免重复阅读
- **无 CRM 级能力** — 无分配、无通知、无自动化

### 下一步最值得做什么

**收紧 broker 记忆和 reopen 体验，不跨入 CRM。**

- 强化 due-state 标签（ overdue / due today）
- 优化 reopen 界面，围绕现有 follow-up 信息
- 增加一个小助手（如「下一步建议」）
- 不改：分配、自动化、通知、完整 CRM

---

*Report generated by scouting sprint. No implementation changes made.*
