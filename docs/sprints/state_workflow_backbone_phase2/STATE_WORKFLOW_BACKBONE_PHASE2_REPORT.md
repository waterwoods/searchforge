# State / Workflow Backbone Phase 2 Report

**Sprint**: State Workflow Backbone Phase 2  
**Date**: 2026-03-16  
**Scope**: Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen**: Strengthen the backbone's three highest-value gaps: conversation_id/session continuity, workflow_state contract completeness, and UI state visibility.
- **Why now**: Phase 1 fixed mixed-message handling and transition guardrails, but the founder correctly observed the backbone remained incomplete—no formal session identity before case, workflow_state not fully exposed, and UI did not clearly show lifecycle/state for office inspection.

---

## 2. Document Set Created

| Doc | Path | Purpose |
|-----|------|---------|
| Product / System Blueprint | `01_PRODUCT_SYSTEM_BLUEPRINT.md` | Why Phase 2 matters, what Phase 1 solved, what remains, what we strengthen |
| Phase 2 Backbone Design Spec | `02_PHASE2_BACKBONE_DESIGN_SPEC.md` | Target improvements, practical scope |
| Conversation / Session Continuity Spec | `03_CONVERSATION_SESSION_CONTINUITY_SPEC.md` | session_id, conversation_id, API contract |
| Workflow State Contract Spec | `04_WORKFLOW_STATE_CONTRACT_SPEC.md` | Full workflow_state shape, next_best_question, lifecycle_status |
| UI State Visibility Spec | `05_UI_STATE_VISIBILITY_SPEC.md` | What UI must show for state/lifecycle |
| Execution Outline | `06_EXECUTION_OUTLINE.md` | Workstreams, order, test plan |
| Acceptance / SLA Criteria | `07_ACCEPTANCE_SLA_CRITERIA.md` | Continuity, state clarity, visibility criteria |
| Founder Demo / Inspection Notes | `08_FOUNDER_DEMO_INSPECTION_NOTES.md` | What to inspect, tests that prove improvement |
| Phase 2 Baseline Audit | `00_PHASE2_BASELINE_AUDIT.md` | Honest audit of Phase 2 gaps |

---

## 3. Baseline Audit

| Area | Finding |
|------|---------|
| **conversation_id** | Blocking — none; in-progress session ephemeral |
| **workflow_state shape** | Acceptable — missing next_best_question, lifecycle_status |
| **UI state visibility** | Weak — lifecycle underused; next_best_question not shown |
| **Biggest weakness** | No conversation_id before case; refresh loses in-progress state |
| **Biggest ambiguity** | Workflow_state vs lifecycle not formalized |
| **Why this matters** | Reusability, multi-turn stability, office trust depend on explicit continuity and visibility |

---

## 4. 10–20 Point Breakdown

| # | Point | Status |
|---|-------|--------|
| 1 | conversation/session identity model | ✓ session_id (UUID) client-generated; localStorage |
| 2 | when conversation_id is created | ✓ Echoed from session_id when provided; no case persisted |
| 3 | relationship between conversation_id and case_id | ✓ case_id = canonical after persist; session_id pre-persist only |
| 4 | first-turn / follow-up / append semantics | ✓ Unchanged; triage_conversation for first/follow-up; append handoff |
| 5 | workflow_state standard fields | ✓ Extended: next_best_question, lifecycle_status |
| 6 | stage semantics | ✓ collecting \| enough_for_handoff |
| 7 | collected semantics | ✓ Per-flow snake_case |
| 8 | still_needed semantics | ✓ Per-flow |
| 9 | next_best_question semantics | ✓ What to ask when handoff_ready=false |
| 10 | handoff_ready semantics | ✓ Unchanged |
| 11 | case_creation_suggested semantics | ✓ Unchanged |
| 12 | human_confirmation_required semantics | ✓ Unchanged |
| 13 | lifecycle_status model | ✓ collecting \| handoff_pending \| handed_off \| office_followup |
| 14 | UI visibility contract | ✓ next_best_question, lifecycle_status, collected/still_needed |
| 15 | persistence timing | ✓ Only when handoff_ready |
| 16 | invalid transition guardrails | ✓ Unchanged (closed terminal) |
| 17 | regression tests | ✓ test_state_workflow_backbone extended for lifecycle_status |
| 18 | intentionally deferred | Server-side in-progress turn persistence; full append "still collecting" |

---

## 5. Iteration Loop 1

| Item | Result |
|------|--------|
| **What problem was fixed** | No session identity before case; workflow_state incomplete |
| **Why this fix was chosen** | session_id in localStorage + API is lightweight, no backend persistence; next_best_question and lifecycle_status formalize the contract |
| **What became more formal** | WORKFLOW_STATE_KEYS extended; session_id in TriageRequest; conversation_id in response |
| **What became more stable** | In-progress threads have identity; triage always returns next_best_question, lifecycle_status |
| **What did not improve** | Server-side persistence of in-progress turns; refresh still loses turns (turns in React state) |
| **Whether it was worth it** | Yes. Session continuity foundation; workflow_state contract complete. |

---

## 6. Iteration Loop 2

| Item | Result |
|------|--------|
| **What problem was fixed** | UI did not show next_best_question, lifecycle_status clearly |
| **Why this fix was chosen** | Minimal UI changes; Case Summary card and Broker Workbench case detail are the right places |
| **What improved vs loop 1** | Founder/office can see "下一步建议" when collecting; "Handed off" / "Office follow-up" in case detail |
| **What still remained weak** | Refresh still loses turns; no server-side in-progress persistence |
| **Whether it was worth it** | Yes. Visibility significantly improved. |

---

## 7. Optional Loop 3

| Item | Result |
|------|--------|
| **Whether used** | No |
| **Reason** | Main targets (session continuity, workflow_state contract, UI visibility) achieved. No clearly valuable, low-risk refinement remained. Stopping is correct. |

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios | 53/53 passed |
| audit_state_field_accuracy | 7/7 passed |
| test_state_workflow_backbone | PASS |
| guardrail_inbox_triage.sh | PASS |
| verify_speed_routing | OK |
| UI build | ✓ built in 22s |

**Limitations**: API test skipped (no server on 8001); LLM-enabled multi-turn not re-run.

---

## 9. Deployment / Release Judgment

| Component | Status |
|-----------|--------|
| **Backend** | Changes in triage.py, case_store.py, routes/inbox_triage.py. Backend redeploy needed if Cloud Run. |
| **Frontend** | Changes in inboxTriage.ts, UnifiedIntakePage.tsx. Frontend redeploy needed if Vercel. |
| **Founder can inspect** | Yes. Run `bash scripts/guardrail_inbox_triage.sh`; try Customer Entry with add-car; check Broker Workbench case detail for lifecycle_status. |

---

## 10. Founder Showcase (5 Examples)

### Example 1: Add-car / Quote (3-turn)

- **User flow**: Turn 1 "我买了台宝马X5" → Turn 2 "2024年的，zip 90210" → Turn 3 "下周提车"
- **Conversation/session now tracks**: session_id in localStorage; passed to API; conversation_id echoed when no case
- **Workflow state now tracks**: next_best_question (Turn 1–2: "先把年份和地址邮编发我"); lifecycle_status: collecting → handoff_pending
- **UI now shows**: "下一步建议" in Case Summary when collecting; "Collecting" / "Ready to save" tag; lifecycle_status "Handed off" after persist
- **Why better**: Explicit session identity; next ask visible; lifecycle clear for office

### Example 2: Missing Document (dec sent + garaging clarification)

- **User flow**: Turn 1 "UW need dec page + garaging. 客户说发过了" → Turn 2 "declaration page 发你了，garaging 是什么意思"
- **Conversation/session now tracks**: session_id; conversation_id echoed
- **Workflow state now tracks**: follow_up_type=clarification_question; lifecycle_status=handoff_pending
- **UI now shows**: "Ready for handoff"; "Handed off" after persist
- **Why better**: Same as Phase 1; lifecycle_status now in case detail

### Example 3: Payment / Cancellation (correction + urgency)

- **User flow**: Turn 1 "payment failed 什么意思" → Turn 2 "我昨天付了，截图发你" → Turn 3 "其实已经付了，那我现在最要紧做什么？"
- **Conversation/session now tracks**: session_id; conversation_id
- **Workflow state now tracks**: lifecycle_status; human_confirmation_required
- **UI now shows**: "Handed off" / "Office follow-up" in case; lifecycle status tag
- **Why better**: Lifecycle visibility for office

### Example 4: Talk to Agent

- **User flow**: User clicks "联系人工" or pastes "我想联系陈奎办公室"
- **Conversation/session now tracks**: session_id (if Customer Entry)
- **Workflow state now tracks**: handoff_ready=true; lifecycle_status=handoff_pending
- **UI now shows**: Immediate handoff; "Ready to save"
- **Why better**: Bypass path; lifecycle consistent

### Example 5: Append / Follow-up Continuity

- **User flow**: Broker reopens case; pastes new customer message "garaging 发你了"
- **Conversation/session now tracks**: case_id (append uses case; no session_id)
- **Workflow state now tracks**: handoff_ready=true; lifecycle_status=handoff_pending
- **UI now shows**: Case updated; "Office follow-up" in case detail
- **Why better**: Append path explicit; lifecycle_status in case

---

## 11. Final Judgment

| Question | Answer |
|----------|--------|
| **Is the State/Workflow backbone significantly stronger after Phase 2?** | Yes. Session continuity, complete workflow_state contract, better UI visibility. |
| **Single biggest architectural improvement** | session_id + conversation_id for in-progress continuity; next_best_question + lifecycle_status. |
| **Biggest remaining weakness** | No server-side persistence of in-progress turns; refresh loses state. |
| **Is the product now much closer to a reusable small-business intake backbone?** | Yes. Formal session identity, complete state contract, clearer visibility. |
| **Single best next move after this sprint** | Optional: persist in-progress turns in localStorage keyed by session_id for refresh recovery. |

---

## 12. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Next step |
|------|--------------|-----------------|----------------------|-----------|-----------|
| 1 | session_id in API; next_best_question, lifecycle_status in triage; WORKFLOW_STATE_KEYS extended | Session continuity; workflow_state contract complete | Server-side turn persistence | Yes | Loop 2 |
| 2 | UI: next_best_question, lifecycle_status in Case Summary and case detail | Founder/office visibility | Refresh still loses turns | Yes | Stop |
| 3 | — | — | — | — | — |

---

## 13. 中文宏观总结

- **为什么现在做 Backbone Phase 2**：Phase 1 已修复混合消息和过渡守卫，但创始人指出主干仍不完整：无正式会话身份、workflow_state 不完整、UI 缺乏生命周期可见性。
- **主要方法/技术**：session_id（localStorage + API）、next_best_question、lifecycle_status、WORKFLOW_STATE_KEYS 扩展、UI 显示下一步建议和生命周期标签。
- **好处**：进行中会话有身份；状态更完整；办公室可更清晰看到收集/交接/跟进状态。
- **已实现**：8 份文档、Loop 1–2 实现、guardrail 通过。
- **比原系统提升**：session_id 支持；next_best_question 显式；lifecycle_status 显式；UI 显示下一步建议和生命周期。
- **还差什么**：服务端不持久化进行中对话；刷新仍丢失 turns。
- **有无重大问题**：无。改动低风险。
- **下一步最该做**：可选：localStorage 按 session_id 持久化 turns，支持刷新恢复。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest backbone Phase 2 improvement**: session_id + conversation_id for in-progress continuity; next_best_question + lifecycle_status in workflow_state; UI shows "下一步建议" and "Handed off" / "Office follow-up".

**Biggest remaining weakness**: No server-side persistence of in-progress turns; refresh loses state.

**Makes product more reusable**: Yes. Formal session identity, complete state contract, clearer visibility.

**Redeploy needed**: Backend yes (if Cloud Run). Frontend yes (if Vercel).

**What Andy should inspect next**: Run `bash scripts/guardrail_inbox_triage.sh`; try Customer Entry add-car flow → see "下一步建议" when collecting; persist case → see "Handed off" in Broker Workbench; check Network tab for session_id in request.

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

Phase 1 已修复混合消息和过渡守卫，但主干仍不完整：无会话身份、workflow_state 不完整、UI 缺乏生命周期可见性。需要加强 continuity、contract、visibility。

### 主要用了什么方法/技术

session_id（localStorage + API）、next_best_question、lifecycle_status、WORKFLOW_STATE_KEYS 扩展、UI 显示下一步建议和生命周期标签。

### 这轮最大的提升

session_id + conversation_id 支持进行中会话身份；next_best_question + lifecycle_status 完善 workflow_state；UI 显示「下一步建议」和「Handed off / Office follow-up」。

### 现在还差什么

服务端不持久化进行中对话；刷新仍丢失 turns；可选：localStorage 按 session_id 持久化 turns。

---

## 16. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

- 创建 8 份 Phase 2 文档 + 基线审计
- Loop 1：session_id API、next_best_question、lifecycle_status、WORKFLOW_STATE_KEYS 扩展、前端 session_id/localStorage
- Loop 2：UI 显示 next_best_question、lifecycle_status 标签
- 扩展 test_state_workflow_backbone 验证 lifecycle_status

### 哪些地方比原系统提高了

- 进行中会话有 session_id 身份
- workflow_state 包含 next_best_question、lifecycle_status
- UI 显示「下一步建议」和生命周期状态
- 办公室可更清晰看到收集/交接/跟进

### 每一轮大概花了哪些时间/精力

- 文档 + 基线：~20 min
- Loop 1：~35 min（API、triage、case_store、frontend）
- Loop 2：~15 min（UI 可见性）
- 报告：~15 min

### 还有哪些值得下一轮继续做

- 可选：localStorage 按 session_id 持久化 turns，支持刷新恢复
- 可选：服务端轻量级 in-progress 会话存储
