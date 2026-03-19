# Minimal Production Backbone Master Report

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17  
**Execution:** ~90 minutes

---

## 1. Sprint Theme

- **What was chosen:** Strengthen the backend foundation into a more formal, more reusable, more pilot-ready minimal production backbone.
- **Why now:** The product has evolved from AI demo to customer entry + stateful intake + case handoff + broker workbench. Scaling to many merchants will be fragile without a tighter backbone.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product / System Blueprint | `01_PRODUCT_SYSTEM_BLUEPRINT.md` |
| Minimal Production Backbone Architecture Spec | `02_MINIMAL_PRODUCTION_BACKBONE_ARCHITECTURE_SPEC.md` |
| Persistence / Storage Strategy Spec | `03_PERSISTENCE_STORAGE_STRATEGY_SPEC.md` |
| Data Contract / Schema Spec | `04_DATA_CONTRACT_SCHEMA_SPEC.md` |
| Demo vs Production Boundary Spec | `05_DEMO_VS_PRODUCTION_BOUNDARY_SPEC.md` |
| Execution Outline | `06_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `07_ACCEPTANCE_SLA_CRITERIA.md` |
| Founder Demo / Inspection Notes | `08_FOUNDER_DEMO_INSPECTION_NOTES.md` |
| Baseline Audit and 10–20 Point Breakdown | `09_BASELINE_AUDIT_AND_20_POINT_BREAKDOWN.md` |

---

## 3. Baseline Audit

### Current Backbone State (Summary)

| Area | State |
|------|-------|
| Message persistence | Strong |
| Session persistence | Strong |
| Case persistence | Strong (lifecycle_status weak) |
| workflow_state contract | Strong |
| lifecycle_status | **Weak** — overwritten in _normalize_case on every read |
| Frontend/backend | Acceptable |
| Storage | Acceptable (JSON) |
| Demo/prod | Weak (path override only) |

### Biggest Current Weakness

**lifecycle_status overwritten in _normalize_case:** Every read overwrote lifecycle_status with a derived value, ignoring stored value. append_follow_up_message did not set lifecycle_status.

### Biggest Current Fragility

**No session_id → case_id linkage:** No traceability from case back to pre-handoff session.

### Biggest Current Ambiguity

**Source of truth for lifecycle_status:** Code mixed triage, stored value, and derived-from-case_status.

---

## 4. 10–20 Point Breakdown

| # | Point | Implemented |
|---|-------|-------------|
| 1 | Message record model | Documented |
| 2 | In-progress session model | Documented |
| 3 | workflow_state model | Single WORKFLOW_STATE_KEYS |
| 4 | Case record model | + origin_session_id |
| 5 | Lifecycle/status model | **Fixed** — preserve stored; derive only when missing |
| 6 | session_id / case_id boundaries | origin_session_id for traceability |
| 7–9 | When created/updated/linked | Documented |
| 10–11 | Frontend/workbench contract | Documented; SavedCase + origin_session_id |
| 12 | Source-of-truth vs derived | **Fixed** — lifecycle_status stored wins |
| 13 | Storage strategy | Stay on JSON; documented |
| 14 | Demo/prod separation | Env vars documented in demo.env.example |
| 15–18 | Config, guardrails, regression, deferred | Documented |

---

## 5. Iteration Loop 1

### What problem was fixed

lifecycle_status was overwritten on every case read; append_follow_up_message did not set lifecycle_status.

### Why this fix was chosen

Stored value must be source of truth. Deriving on every read caused ambiguity and wrong display after append.

### What became more formal

- _normalize_case preserves lifecycle_status when valid; derives only when missing (legacy migration)
- append_follow_up_message explicitly sets lifecycle_status = "office_followup"

### What became more durable

- New cases: lifecycle_status = "handed_off"
- After append: lifecycle_status = "office_followup"
- Status/notes updates: preserve existing lifecycle_status

### What did not improve

- SQLite migration
- Formal schema validation
- Demo/prod mode flag

### Whether it was worth it

**Yes.** lifecycle_status is now coherent and correct.

---

## 6. Iteration Loop 2

### What problem was fixed

No traceability from case to pre-handoff session; demo/prod boundary undocumented.

### Why this fix was chosen

origin_session_id enables debugging and audit. Env doc is low-effort, high-clarity.

### What improved vs loop 1

- save_case accepts origin_session_id; route passes session_id when persisting
- configs/demo.env.example documents UNIFIED_INTAKE_SESSIONS_PATH, UNIFIED_INTAKE_CASES_PATH
- SavedCase TypeScript includes origin_session_id

### What still remained weak

- No formal demo/prod mode flag
- No backup/restore
- No per-broker isolation

### Whether it was worth it

**Yes.** Traceability and env documentation improve pilot readiness.

---

## 7. Optional Loop 3

**Used:** No.

**Reason:** Loop 1 and 2 addressed the highest-value backbone issues. Remaining items (schema validation, demo mode flag) are lower priority and would add complexity without clear payoff for this sprint.

---

## 8. Validation Summary

| Script | Result |
|--------|--------|
| run_inbox_triage_scenarios.py | PASS (53/53) |
| run_multi_turn_simulations.py | PASS (38/38) |
| audit_state_field_accuracy.py | PASS (7/7) |
| verify_speed_routing.py | PASS |
| test_state_workflow_backbone.py | PASS |
| guardrail_inbox_triage.sh | PASS |
| verify_inbox_case_persistence.py | PASS (incl. lifecycle_status, append) |

**Limitations:** unified_intake_smoke_check.sh requires server on 8001; not run in this sprint.

---

## 9. Deployment / Release Judgment

- **Backend live:** No redeploy performed. Backend changes are backward-compatible.
- **Frontend live:** No redeploy. TypeScript change (origin_session_id) is additive.
- **Founder can inspect:** Yes. Run `bash scripts/guardrail_inbox_triage.sh`; try Customer Entry → handoff → reopen → append follow-up.

---

## 10. Founder Showcase

### Example 1: Add-car handoff

- **User flow:** Paste "我买了台2024宝马X5，zip 90210" → triage → handoff_ready → Save case
- **What now persists:** case_messages, workflow_state, lifecycle_status = "handed_off"
- **What state now tracks:** collected_fields, still_needed_fields, handoff_ready
- **What case now shows:** Case card with "Handed off" tag
- **Why better:** lifecycle_status is correct and preserved on read

### Example 2: Append follow-up

- **User flow:** Reopen case → Paste "客户说材料明天早上重发" → Update with new customer message
- **What now persists:** case_messages appended, lifecycle_status = "office_followup"
- **What state now tracks:** Updated broker_next_step, collected_fields
- **What case now shows:** "Office follow-up" tag
- **Why better:** lifecycle_status correctly reflects office follow-up flow

### Example 3: Traceability

- **User flow:** Multi-turn conversation with session_id → handoff → case created
- **What now persists:** origin_session_id on case (when session_id was present)
- **Why better:** Can trace case back to pre-handoff session for debugging

---

## 11. Final Judgment

- **Biggest gain:** lifecycle_status coherence — stored value is source of truth; append sets office_followup.
- **Biggest remaining weakness:** No formal demo/prod mode flag; JSON storage remains prototype-like for scale.
- **Whether this meaningfully strengthens the reusable backbone:** Yes. Message/state/case relationship is clearer; persistence contract is tighter.
- **Best next step:** Run paid pilot; if scaling needed, consider SQLite migration and demo/prod mode flag.

---

## 12. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Next step |
|------|--------------|-----------------|----------------------|-----------|------------|
| 1 | _normalize_case preserve lifecycle_status; append sets office_followup | lifecycle_status correct | SQLite, schema validation | Yes | Loop 2 |
| 2 | origin_session_id; demo/prod env doc; SavedCase type | Traceability; env clarity | Demo mode flag | Yes | Stop |
| 3 | — | — | — | — | — |

---

## 13. 中文宏观总结

- **为什么现在做主线一：** 产品从 AI 演示演进为客户入口 + 状态化受理 + 案件交接 + 经纪人工作台，需要更正式、更可复用的后端骨干。
- **主要用了什么方法/技术：** lifecycle_status 存储优先、append 显式设置 office_followup、origin_session_id 可追溯、env 文档化。
- **这样做的好处：** 状态一致、持久化契约更清晰、可追溯、更接近付费试点基础。
- **现在已经实现了什么：** lifecycle_status 修复、append 设置 office_followup、origin_session_id、8 份控制文档、基线审计、验证脚本全部通过。
- **比原系统提升了哪些地方：** lifecycle_status 不再被覆盖、append 后状态正确、案件可追溯、demo/prod 边界文档化。
- **还差什么：** 正式 demo/prod 模式、SQLite 迁移、多租户隔离。
- **有没有重大问题：** 无。
- **下一步最该做什么：** 运行付费试点；若需扩展再考虑 SQLite 和 demo 模式。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest backbone improvement:** lifecycle_status is now coherent — stored value is source of truth; append correctly sets office_followup.

**Biggest remaining weakness:** No formal demo/prod mode flag; JSON storage remains prototype-like for scale.

**Whether this makes the product more reusable:** Yes. Message/state/case relationship is clearer; persistence contract is tighter; origin_session_id enables traceability.

**Whether redeploy is needed:** No. Changes are backward-compatible.

**What Andy should inspect next:** Run `bash scripts/guardrail_inbox_triage.sh`; try Customer Entry → handoff → reopen → append follow-up; verify "Handed off" and "Office follow-up" tags.

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品从演示演进为入口+受理+案件+工作台，需要更正式、更可复用的后端骨干以支持付费试点。

### 主要用了什么方法/技术

lifecycle_status 存储优先、append 显式设置 office_followup、origin_session_id 可追溯、8 份控制文档、基线审计。

### 这轮最大的提升

lifecycle_status 一致性 — 存储值优先，append 正确设置 office_followup；origin_session_id 可追溯。

### 现在还差什么

正式 demo/prod 模式、SQLite 迁移、多租户隔离。

---

## 16. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

- 8 份控制文档
- 基线审计 + 10–20 点分解
- Loop 1: lifecycle_status 修复、append 设置 office_followup
- Loop 2: origin_session_id、demo/prod env 文档、SavedCase 类型
- 验证脚本扩展（verify_inbox_case_persistence 增加 lifecycle_status 断言）

### 哪些地方比原系统提高了

- lifecycle_status 不再被 _normalize_case 覆盖
- append 后 lifecycle_status = office_followup
- 案件可追溯（origin_session_id）
- demo/prod 边界文档化

### 每一轮大概花了哪些时间 / 精力

- Phase A + 基线：~25 分钟
- Loop 1：~20 分钟
- Loop 2：~15 分钟
- 报告 + 验证：~30 分钟

### 还有哪些值得下一轮继续做

- 正式 demo/prod 模式
- SQLite 迁移（若试点扩展）
- 多租户隔离
- 备份/恢复自动化
