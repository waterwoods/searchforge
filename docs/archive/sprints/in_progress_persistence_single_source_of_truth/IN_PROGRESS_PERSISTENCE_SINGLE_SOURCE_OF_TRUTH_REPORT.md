# In-Progress Conversation Persistence + Single Source of Truth Report

**Sprint:** In-Progress Conversation Persistence + Single Source of Truth  
**Date:** 2026-03-16  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Close the in-progress conversation persistence gap and strengthen workflow_state as single source of truth.
- **Why now:** The founder and reviewer agreed this is the single most important remaining backbone gap. Refresh could still lose turns; workflow_state was not persisted before handoff.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/in_progress_persistence_single_source_of_truth/01_SPRINT_BLUEPRINT.md` |
| In-Progress Persistence Design Spec | `02_IN_PROGRESS_PERSISTENCE_DESIGN_SPEC.md` |
| Single Source of Truth Contract Spec | `03_SINGLE_SOURCE_OF_TRUTH_CONTRACT_SPEC.md` |
| Execution Outline | `04_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `05_ACCEPTANCE_SLA_CRITERIA.md` |
| Founder Demo / Inspection Notes | `06_FOUNDER_DEMO_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

### Current Persistence Gap (Before Sprint)

| Data | Ephemeral | Durable |
|------|-----------|---------|
| session_id | localStorage | — |
| conversation_turns | React state only | — |
| turns (Customer Entry) | React state | — |
| case_id, case_messages, workflow_state | — | JSON case store |

### Biggest Weakness

**In-progress turns lost on refresh.** Multi-turn flows (e.g. add-car) lost all context on refresh before handoff.

### Biggest State Divergence

Frontend derived handoff_ready from last turn; backend produced it. No server-side storage of pre-handoff workflow_state.

### Why This Matters

Users could lose work on accidental refresh. Product felt fragile for multi-turn intake flows.

---

## 4. 10–20 Point Breakdown

1. **session_id semantics:** Client-generated UUID; stored in localStorage; sent with each triage request.
2. **conversation_id semantics:** Echo of session_id when no case persisted; not stored.
3. **case_id semantics:** Created only when handoff_ready and persist_case; canonical identity after handoff.
4. **When in-progress session record is created:** On first triage with session_id when no case persisted.
5. **How messages are stored before handoff:** Each triage response (session_id + no case_id) saves full turns + new customer + new system to `data/unified_intake_sessions.json`.
6. **How workflow_state is stored before handoff:** Extracted from triage result (WORKFLOW_STATE_KEYS) and stored alongside turns.
7. **Recovery after refresh:** Frontend on mount calls GET /api/inbox/session/{session_id}; if 200, restores turns into React state; shows "已恢复对话".
8. **Relationship between in-progress session and later case:** Mutually exclusive; once case created, session is deleted; frontend clears session_id.
9. **Case created when:** Only when handoff_ready and persist_case=true.
10. **lifecycle_status during collecting stage:** "collecting" when handoff_ready=false; "handoff_pending" when handoff_ready=true.
11. **collected / still_needed persistence rules:** Stored in workflow_state; persisted in session and case.
12. **next_best_question persistence rules:** Stored in workflow_state; displayed from last turn's triageResult.
13. **Workbench visibility rules:** Reads workflow_state from case; no change.
14. **Frontend/backend contract:** Backend produces workflow_state; frontend displays it; no shadow logic.
15. **Regression guardrails:** test_state_workflow_backbone.py, run_inbox_triage_scenarios.py, guardrail_inbox_triage.sh, test_in_progress_session_api.py.
16. **Invalid states or transitions:** None introduced; closed remains terminal for case status.
17. **What stays lightweight:** JSON file store; max 50 sessions; no TTL; no auth.
18. **What is intentionally deferred:** TTL, session cleanup on case (we delete), multi-tab locking, per-user sessions.

---

## 5. Iteration Loop 1

### What Changed

- Added `session_store.py`: save_in_progress_session, get_in_progress_session, delete_in_progress_session.
- Modified `inbox_triage.py`: save session on triage when session_id and no case_id; delete session when case persisted.
- Added GET /api/inbox/session/{session_id}.
- Added `getInProgressSession`, `getSessionId` to inboxTriage.ts.
- CustomerEntryTab: useEffect on mount restores turns when session_id exists.

### Why It Matters

Refresh no longer loses in-progress conversation. Users can recover multi-turn flows.

### What Now Persists

- In-progress turns (customer + system) before handoff.
- workflow_state (handoff_ready, lifecycle_status, collected_fields, still_needed_fields, next_best_question, etc.).

### What Did Not Improve

- Workbench still reads from case only (no change needed).
- No TTL for orphaned sessions.

### Whether It Was Worth It

Yes. Core persistence gap closed with minimal implementation.

---

## 6. Iteration Loop 2

### What Changed

- Added "已恢复对话" message when restore succeeds.
- Added test_in_progress_session_api.py regression test.
- Session deleted when case persisted (cleanup).

### Why It Matters

User feedback on restore; regression coverage; no orphaned sessions when case created.

### What Improved vs Loop 1

- Clearer UX on restore.
- Regression guardrail for session store.
- Cleaner state when handoff completes.

### What Still Remained Weak

- Orphaned sessions (user refreshes, never completes) remain until evicted by limit.
- No explicit "restore in progress" loading state (brief async).

### Whether It Was Worth It

Yes. Polish and guardrails complete the loop.

---

## 7. Optional Loop 3

**Whether used:** No.

**Reason:** No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 8. Validation Summary

| Test / Check | Result |
|--------------|--------|
| test_state_workflow_backbone.py | PASS |
| run_inbox_triage_scenarios.py | 53/53 passed |
| guardrail_inbox_triage.sh | PASS |
| test_in_progress_session_api.py | PASS |

**Limitations:** Manual refresh recovery not automated; requires live backend + frontend.

---

## 9. Deployment / Release Judgment

- **Backend:** Changes in fiqa_api (session_store, inbox_triage route). Redeploy needed for Cloud Run.
- **Frontend:** Changes in UnifiedIntakePage, inboxTriage. Redeploy needed for Vercel.
- **Founder can inspect:** Yes, after redeploy. Local: `bash scripts/run_demo_local.sh` → http://localhost:5173/demo.

---

## 10. Founder Showcase

### Example: Add-Car Flow + Refresh

1. **User flow:** Customer Entry → "我想加新车报价" → send → "2025 Tesla Model Y" → send.
2. **What now persists:** Turns + workflow_state saved after each triage (before handoff).
3. **What workflow_state tracks:** lifecycle_status=collecting, collected_fields, still_needed_fields, next_best_question.
4. **What UI shows:** Tags (Collecting), 下一步建议.
5. **Refresh:** F5 → "已恢复对话" → conversation restored; can continue.
6. **Why better:** Before: refresh lost everything. After: full recovery.

---

## 11. Final Judgment

- **Biggest gain:** In-progress conversation survives refresh; workflow_state persisted before handoff.
- **Biggest remaining weakness:** Orphaned sessions (no TTL); manual testing only for restore.
- **Whether this meaningfully closes the persistence gap:** Yes. Core gap closed.
- **Best next step:** Add TTL or periodic cleanup for orphaned sessions; optional E2E test for refresh recovery.

---

## 12. Iteration Log

| Loop | What Changed | What Got Better | What Did Not Improve | Worth It? | Next Step |
|------|--------------|-----------------|----------------------|-----------|-----------|
| 1 | Session store, triage integration, restore API, frontend restore | Turns + state persist; refresh recovers | No workbench change | Yes | Add restore message + test |
| 2 | Restore message, regression test, session delete on case | UX, guardrails, cleanup | Orphaned sessions | Yes | Stop; optional TTL later |

---

## 13. 中文宏观总结

- **为什么现在做 in-progress persistence：** 刷新会丢失对话是当前最大的 backbone 缺口；创始人一致认为必须优先解决。
- **主要用了什么方法/技术：** 轻量 JSON 存储（unified_intake_sessions.json），每次 triage 无 case 时保存 turns + workflow_state；前端 mount 时 GET session 恢复。
- **这样做的好处：** 刷新可恢复对话；workflow_state 成为真正的单一数据源；case 创建不再是唯一的持久化时刻。
- **现在已经实现了什么：** 后端 session_store、triage 集成、GET session API、前端恢复逻辑、"已恢复对话" 提示、回归测试。
- **比原系统提升了哪些地方：** 刷新不再丢对话；多轮流程可恢复；workflow_state 持久化提前到 handoff 前。
- **还差什么：** 孤儿 session 的 TTL；刷新恢复的自动化 E2E 测试。
- **有没有重大问题：** 无。
- **下一步最该做什么：** 可选：孤儿 session 清理；E2E 刷新测试。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest persistence improvement:** In-progress conversation turns and workflow_state now persist before handoff. Refresh recovers the conversation.

**Biggest remaining weakness:** Orphaned sessions (user never completes) remain until evicted; no TTL.

**Whether this makes the backbone more reusable:** Yes. Multi-turn intake flows are now refresh-resilient.

**Whether redeploy is needed:** Yes. Backend + frontend both changed.

**What Andy should inspect next:** Start add-car flow, send 1–2 messages, refresh (F5). Verify conversation restores and "已恢复对话" appears. Continue and complete handoff; verify case appears in Workbench.

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

刷新会丢失对话是当前最大的 backbone 缺口；创始人一致认为必须优先解决。

### 主要用了什么方法/技术

轻量 JSON 存储（session_store），每次 triage 无 case 时保存 turns + workflow_state；前端 mount 时 GET /api/inbox/session/{session_id} 恢复。

### 这轮最大的提升

刷新可恢复对话；workflow_state 在 handoff 前持久化；case 创建不再是唯一的持久化时刻。

### 现在还差什么

孤儿 session 的 TTL；刷新恢复的自动化 E2E 测试。

---

## 16. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作

- 创建 6 份控制文档（Blueprint, Design Spec, Contract Spec, Execution Outline, Acceptance, Founder Notes）
- 实现 session_store.py（save/get/delete）
- 修改 inbox_triage 路由（保存 session、删除 on case、GET session 端点）
- 前端 API getInProgressSession、getSessionId
- CustomerEntryTab 恢复逻辑、"已恢复对话" 提示
- 回归测试 test_in_progress_session_api.py

### 哪些地方比原系统提高了

- 刷新可恢复对话
- workflow_state 在 handoff 前持久化
- session/case 关系更清晰（互斥；case 创建时删除 session）

### 每一轮大概花了哪些时间 / 精力

- Loop 1：设计 + 后端 + 前端 + 集成（约 25 分钟）
- Loop 2：恢复提示 + 测试 + 清理逻辑（约 10 分钟）

### 还有哪些值得下一轮继续做

- 孤儿 session 的 TTL 或定期清理
- 刷新恢复的 E2E 自动化测试

---

## REQUIRED CROSS-WINDOW SUMMARY (for ChatGPT)

**What the new persistence/state backbone now does:**
- In-progress conversation turns and workflow_state are stored in `data/unified_intake_sessions.json` on every triage when session_id is provided and no case is persisted.
- GET /api/inbox/session/{session_id} returns { turns, workflow_state } for refresh recovery.
- Frontend on mount restores turns when session_id exists in localStorage; shows "已恢复对话".
- When case is persisted, session is deleted; frontend clears session_id.

**What improved in this sprint:**
- Refresh no longer loses in-progress conversation.
- workflow_state persisted before handoff.
- Single source of truth: backend produces, frontend displays, no shadow logic.

**What remains weak:**
- Orphaned sessions (no TTL).
- No automated E2E test for refresh recovery.

**Whether the architecture direction is correct:** Yes. Lightweight, practical, no overbuild.

**Best next recommendation:** Optional TTL for orphaned sessions; E2E refresh test.
