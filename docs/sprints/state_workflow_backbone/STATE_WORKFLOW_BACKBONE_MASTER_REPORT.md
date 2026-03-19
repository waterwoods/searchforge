# State / Workflow Backbone Master Report

**Sprint**: State Workflow Backbone  
**Date**: 2026-03-16  
**Scope**: Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen**: Strengthen the State/Workflow backbone for conversation continuity, workflow progression, handoff decisions, and case lifecycle.
- **Why now**: The product has triage, handoff logic, and case persistence, but the state layer was implicit and scattered. Multi-turn continuity, broker handoff clarity, and pilot readiness require a formal, document-driven backbone.

---

## 2. Document Set Created

| Doc | Path | Purpose |
|-----|------|---------|
| Product / System Blueprint | `01_PRODUCT_SYSTEM_BLUEPRINT.md` | Why backbone matters, current weaknesses, what we strengthen, what we don't do |
| State / Workflow Architecture Spec | `02_STATE_WORKFLOW_ARCHITECTURE_SPEC.md` | Conversation lifecycle, workflow progression, handoff, message vs case, 10–20 point breakdown |
| Data Contract / Schema Spec | `03_DATA_CONTRACT_SCHEMA_SPEC.md` | Conversation/case identity, message record, workflow_state, frontend/backend contract |
| Transition / Guardrail Spec | `04_TRANSITION_GUARDRAIL_SPEC.md` | Valid/invalid transitions, first-turn, follow-up, handoff, persistence, regression guardrails |
| Execution Outline | `05_EXECUTION_OUTLINE.md` | Workstreams, implementation order, test plan |
| Acceptance / SLA Criteria | `06_ACCEPTANCE_SLA_CRITERIA.md` | Continuity, state correctness, workflow clarity, case progression, handoff timing |
| Founder Demo / Inspection Notes | `07_FOUNDER_DEMO_INSPECTION_NOTES.md` | What to inspect, behaviors that should improve |
| Baseline Audit | `00_BASELINE_AUDIT.md` | Current backbone, weaknesses, fragility |

---

## 3. Baseline Audit

| Area | Finding |
|------|---------|
| **Current backbone** | Unified entry (triage_conversation), persist only when handoff_ready, per-flow field extractors, follow_up_type, collection_stage |
| **Biggest weakness** | No conversation_id before case; append always handoff_ready; state fields not consistently documented |
| **Biggest fragility** | Scattered transition logic; follow_up_type order (already_sent vs clarification) caused M1 audit failure |
| **Why this matters** | Multi-turn quality, broker clarity, and pilot readiness depend on explicit, predictable state |

---

## 4. 10–20 Point Backbone Breakdown

| # | Point | Status |
|---|-------|--------|
| 1 | Unified conversation entry path | ✓ triage_conversation for first and follow-up |
| 2 | First-turn vs follow-up vs append semantics | ✓ Documented and implemented |
| 3 | conversation_id / case_id / customer_id boundaries | Partial (no conversation_id pre-persist) |
| 4 | Standard workflow_state structure | ✓ WORKFLOW_STATE_KEYS constant added |
| 5 | Standard collected structure | ✓ Per-flow snake_case |
| 6 | Standard still_needed structure | ✓ Per-flow |
| 7 | next_best_question / next-step logic | ✓ _get_next_ask_draft |
| 8 | handoff_ready decision rules | ✓ _should_handoff + per-flow enough |
| 9 | case_creation_suggested decision rules | ✓ handoff + (collected>0 or high-value category) |
| 10 | human_confirmation_required decision rules | ✓ _derive_human_confirmation_fields |
| 11 | Lifecycle status model | ✓ new, reviewing, waiting_customer, agent_followup, done, closed |
| 12 | Message history persistence model | ✓ case_messages with sequence |
| 13 | Case persistence timing | ✓ Only when handoff_ready + persist_case |
| 14 | Summary / office-readable handoff contract | ✓ conversation_summary, broker_next_step |
| 15 | Frontend/backend contract | ✓ handoff_ready, collection_stage in response |
| 16 | Regression guardrails | ✓ Backbone test in guardrail_inbox_triage.sh |
| 17 | Testing matrix | ✓ run_inbox_triage_scenarios, run_multi_turn_simulations, audit_state_field_accuracy |
| 18 | What remains deferred | conversation_id, full transition validation, SQL migration |

---

## 5. Iteration Loop 1

| Item | Result |
|------|--------|
| **What changed** | Added WORKFLOW_STATE_KEYS constant; reordered follow_up_type (clarification before already_sent for SIM2); added why_still_chasing branch; added test_state_workflow_backbone.py |
| **What became more formal** | Workflow state schema documented; follow_up_type detection order explicit |
| **What became more stable** | M1 audit passes (declaration page 发你了，garaging 是什么意思 → clarification_question); all workflow keys present in triage result |
| **What did not improve** | conversation_id; append "still collecting" path |
| **Whether it was worth it** | Yes. M1 fix improves mixed "I sent X + what does Y mean?" reply quality. Schema constant aids future maintenance. |

---

## 6. Iteration Loop 2

| Item | Result |
|------|--------|
| **What changed** | Added TERMINAL_STATUS guardrail (closed is terminal); update_case_status rejects closed→other; added terminal_status test to backbone script |
| **What improved vs loop 1** | Transition guardrail enforced; invalid state transitions blocked |
| **What still remained weak** | conversation_id; lifecycle status underused in UI |
| **Whether it was worth it** | Yes. Prevents accidental closed→new transitions; aligns with Transition Guardrail Spec. |

---

## 7. Optional Loop 3

| Item | Result |
|------|--------|
| **Whether used** | Yes |
| **What changed** | Added test_state_workflow_backbone.py to guardrail_inbox_triage.sh (step 4b) |
| **Whether it was worth it** | Yes. Backbone regression now runs on every guardrail pass. |

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios | 53/53 passed |
| audit_state_field_accuracy | 7/7 passed |
| test_state_workflow_backbone | PASS |
| guardrail_inbox_triage.sh | PASS |
| verify_inbox_case_persistence | PASS |
| verify_speed_routing | OK |

**Limitations**: LLM-enabled multi-turn and adversarial simulations not re-run in this report; guardrail covers them.

---

## 9. Deployment / Release Judgment

| Component | Status |
|-----------|--------|
| **Backend** | Changes in triage.py, case_store.py. Backend redeploy needed if running Cloud Run. |
| **Frontend** | No frontend contract changes. No frontend redeploy required. |
| **Founder can inspect** | Yes. Run `bash scripts/guardrail_inbox_triage.sh` and `PYTHONPATH=. python3 scripts/test_state_workflow_backbone.py`. |

---

## 10. Founder Showcase (5 Examples)

### Example 1: Add-car / Quote (3-turn)

- **User flow**: Turn 1 "我买了台宝马X5" → Turn 2 "2024年的，zip 90210" → Turn 3 "下周提车"
- **State now tracks**: collection_stage=enough_for_handoff, collected_fields=[year, make_model, zip, delivery_date], still_needed=[primary_driver]
- **Case now stores**: case_messages with full thread; handoff_ready=true; broker_next_step actionable
- **Why better**: Explicit workflow state; add-car next_ask logic asks zip before handoff when missing
- **When handoff happens**: Turn 3 when year+model+zip+delivery present

### Example 2: Missing Document (dec sent + garaging clarification)

- **User flow**: Turn 1 "UW need dec page + garaging. 客户说发过了" → Turn 2 "declaration page 发你了，garaging 是什么意思"
- **State now tracks**: follow_up_type=clarification_question (not already_sent); collected includes customer_says_sent_declaration_page
- **Case now stores**: conversation_summary with collected/still_needed; handoff reply answers "garaging 是什么意思" first
- **Why better**: Mixed "I sent X + what does Y mean?" now gets answer-first reply (SIM2 fix)
- **When handoff happens**: Turn 2; reply explains garaging proof, then handoff suffix

### Example 3: Payment / Cancellation (correction + urgency)

- **User flow**: Turn 1 "payment failed 什么意思" → Turn 2 "我昨天付了，截图发你" → Turn 3 "其实已经付了，那我现在最要紧做什么？"
- **State now tracks**: follow_up_type=correction; urgency_next_markers trigger answer-first
- **Case now stores**: human_confirmation_required=true; broker_next_step for verify payment
- **Why better**: Correction + embedded urgency question gets "最要紧的是等办公室确认付款" answer, not generic "好的明白了"
- **When handoff happens**: Turn 2 or 3; Turn 3 reply answers urgency then handoff

### Example 4: Talk to Agent

- **User flow**: User clicks "联系人工" or pastes "我想联系陈奎办公室"
- **State now tracks**: handoff_ready=true immediately; case_creation_suggested=true
- **Case now stores**: issue_category=customer_requested_human; broker_next_step "Call or message back promptly"
- **Why better**: Bypass path documented; immediate handoff
- **When handoff happens**: Turn 1

### Example 5: Append / Follow-up Continuity

- **User flow**: Broker reopens case; pastes new customer message "garaging 发你了"
- **State now tracks**: triage_for_append returns full triage with handoff_ready=true; follow_up_type=already_sent
- **Case now stores**: case_messages grows; source_text updated; workflow fields refreshed
- **Why better**: Append path explicit; broker paste = handoff by design; workflow state persisted
- **When handoff happens**: On append (always)

---

## 11. Final Judgment

| Question | Answer |
|----------|--------|
| **Is the State/Workflow backbone significantly stronger now?** | Yes. Formal schema, explicit guardrails, follow_up_type fix, terminal status guardrail. |
| **Single biggest architectural improvement** | Formal WORKFLOW_STATE_KEYS + follow_up_type order (clarification before already_sent for mixed messages). |
| **Biggest remaining weakness** | No conversation_id before case; in-progress sessions ephemeral. |
| **Is the system now much closer to a reusable small-business intake product?** | Yes. Documented backbone, regression tests, transition guardrails. |
| **Single best next move after this sprint** | Add optional session_id/conversation_id for Customer Entry in-progress continuity (localStorage or URL param). |

---

## 12. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Next step |
|------|--------------|-----------------|----------------------|-----------|-----------|
| 1 | WORKFLOW_STATE_KEYS; follow_up_type order; why_still_chasing; backbone test | M1 audit pass; schema formalized | conversation_id | Yes | Loop 2 |
| 2 | TERMINAL_STATUS; closed→other rejected; terminal test | Transition guardrail enforced | Lifecycle UI | Yes | Loop 3 |
| 3 | Backbone test in guardrail | Regression coverage | — | Yes | Stop |

---

## 13. 中文宏观总结

- **为什么现在做 State/Workflow 主干专项**：产品已有 triage、handoff、case 持久化，但状态层分散、不显式，多轮连续性和经纪人交接清晰度依赖更形式化的主干。
- **主要方法/技术**：文档先行（7 份架构文档）、10–20 点分解、WORKFLOW_STATE_KEYS 常量、follow_up_type 检测顺序调整、closed 终端状态守卫、回归测试加入 guardrail。
- **好处**：状态更可预测；混合消息（如「发你了，garaging 是什么意思」）回复更准确；无效状态转换被拦截。
- **已实现**：架构文档、基线审计、Loop 1–3 实现、guardrail 集成。
- **比原系统提升**：follow_up_type 顺序修复 M1；workflow_state 显式化；closed 不可回退。
- **还差什么**：conversation_id 预持久化；生命周期在 UI 中的更强驱动。
- **有无重大问题**：无。现有改动低风险。
- **下一步最该做**：为 Customer Entry 增加可选 session_id（localStorage 或 URL），以支持刷新后恢复进行中会话。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest backbone improvement**: Formal workflow state schema + follow_up_type fix for mixed "I sent X + what does Y mean?" messages (SIM2). Reply now answers the clarification first.

**Biggest remaining weakness**: No conversation_id before case; in-progress sessions (Turn 1–2, not handoff) are ephemeral; refresh loses state.

**Makes product more reusable**: Yes. Documented backbone, regression tests, transition guardrails.

**Redeploy needed**: Backend yes (if Cloud Run). Frontend no.

**What Andy should inspect next**: Run `bash scripts/guardrail_inbox_triage.sh`; try "declaration page 发你了，garaging 是什么意思" in Customer Entry → should get garaging explanation first, then handoff. Try changing a case to "closed" then to "new" → should reject.

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品已有 triage、handoff、case，但状态/工作流主干不够形式化，导致多轮连续性弱、交接时机不清晰。需要建立显式、可预测的 State/Workflow 主干。

### 主要用了什么方法/技术

文档先行（7 份架构文档）、10–20 点分解、WORKFLOW_STATE_KEYS 常量、follow_up_type 检测顺序、closed 终端状态守卫、回归测试集成 guardrail。

### 这轮最大的提升

follow_up_type 顺序修复：混合消息「发你了，garaging 是什么意思」现在正确识别为 clarification_question，先回答再交接；closed 状态不可回退。

### 现在还差什么

conversation_id 预持久化；进行中会话刷新后丢失；生命周期在 UI 中的更强驱动。

---

## 16. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

- 创建 7 份架构文档 + 基线审计
- Loop 1：WORKFLOW_STATE_KEYS、follow_up_type 顺序、backbone 回归测试
- Loop 2：closed 终端状态守卫、transition 校验
- Loop 3：backbone 测试加入 guardrail

### 哪些地方比原系统提高了

- 混合消息（发你了 + 什么意思）回复策略正确
- workflow_state 显式化、可维护
- 无效状态转换被拦截
- 回归测试覆盖 backbone

### 每一轮大概花了哪些时间/精力

- 文档 + 基线：~30 min
- Loop 1：~25 min（实现 + 测试）
- Loop 2：~15 min（terminal 守卫 + 测试）
- Loop 3：~5 min（guardrail 集成）

### 还有哪些值得下一轮继续做

- 可选 session_id 支持进行中会话
- case_status 更细粒度 transition 校验
- UI 中 lifecycle 的更强驱动
