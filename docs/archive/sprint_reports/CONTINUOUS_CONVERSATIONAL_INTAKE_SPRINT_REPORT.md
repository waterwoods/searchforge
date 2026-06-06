# Continuous Conversational Intake Sprint Report

**Sprint:** Continuous Conversational Intake  
**Date:** 2026-03-09  
**Target:** Transform Customer Entry from one-shot result card into same-page guided intake conversation

---

## 1. Stages Completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Product outline + doc lock | **Completed** | Created `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` |
| Stage 2 — Same-page conversational Customer Entry | **Completed** | Conversation bubbles, inline replies, input always visible until handoff |
| Stage 3 — Progressive information collection | **Completed** | Backend `triage_conversation` merges context; handoff after 2nd message or when manual_followup not needed |
| Stage 4 — Summary + context handoff to broker | **Completed** | Full conversation saved as `source_text`; broker sees `[客户]` / `[系统]` turns |
| Stage 5 — Audit + validation | **Completed** | Guardrail, scenarios, proxy calibration, smoke check all pass |

**Skipped:** None.

---

## 2. Product/Design Changes Made

### Stage 1
| File | Change |
|------|--------|
| `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` | **Created.** Defines customer flow, progressive collection, when to ask vs hand off, broker handoff, real vs mock. |

### Stage 2 + 3
| File | Change |
|------|--------|
| `ui/src/pages/UnifiedIntakePage.tsx` | **CustomerEntryTab rewritten.** Conversation turns as bubbles (customer right, system left). Input stays visible until `handoff_ready`. "继续补充" flow. |
| `ui/src/api/inboxTriage.ts` | Added `ConversationTurn`, `handoff_ready`, `conversation_summary`. `triageMessage` accepts optional `conversationTurns`. |
| `services/fiqa_api/routes/inbox_triage.py` | Added `ConversationTurn`, `conversation_turns` to `TriageRequest`. Persist only when single message or `handoff_ready`. Build full conversation for `source_text`. |
| `services/fiqa_api/inbox_triage/triage.py` | Added `triage_conversation(latest_text, conversation_turns)`, `_build_conversation_text_for_triage`, `_should_handoff`. Returns `handoff_ready`, `conversation_summary`. |

### Stage 4
| File | Change |
|------|--------|
| `services/fiqa_api/routes/inbox_triage.py` | When persisting multi-turn, `source_text` = full `[客户]` / `[系统]` conversation. |
| `services/fiqa_api/inbox_triage/case_store.py` | No change; existing structure supports `source_text` as conversation. |

### Stage 5 (docs)
| File | Change |
|------|--------|
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Added section 3 on same-page conversational intake. |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Updated Customer flow description. |

---

## 3. Customer Conversational Flow

**What the customer sees first:** One input box, one CTA ("提交"). Optional "需要示例？" for example messages.

**How the same-page conversation works:**
1. Customer types first message → clicks 提交.
2. System reply appears inline as a bubble (left-aligned, green accent).
3. Input shrinks to 3 rows; placeholder: "继续补充信息，或直接发送".
4. Customer can send a second message.
5. System replies again. If `handoff_ready` (2nd message or low-urgency), handoff card appears.
6. Handoff card: "办公室会尽快处理，有结果会联系您。" + 查看工作台 + 提交新问题.

**How progressive information collection works:**
- First reply uses existing intent-specific logic (add car → ask year/model/VIN; payment failed → ask notice/payment).
- Second message is triaged with merged context (`[客户] msg1\n\n[系统] reply1\n\n[客户] msg2`).
- After 2nd customer message, or when `manual_followup_needed` is false, handoff occurs.

**How this differs from the previous one-shot result card:**
- Before: Submit → static result card → 查看工作台 or 提交新问题. No continuation.
- After: Submit → inline reply → can continue → handoff when ready → 查看工作台 or 提交新问题.

---

## 4. Broker-Side Continuity

**How the conversation becomes a broker-side case:**
- When `handoff_ready` is true, the case is persisted.
- `source_text` contains the full conversation, e.g.:
  ```
  [客户] 客户问：这个英文 notice 说 payment failed，我现在怎么办？
  [系统] 这看起来是付款出了问题。请把最新通知或付款截图发我...
  [客户] 我发了截图
  ```
- Broker sees the case in Recent cases. On reopen, "Message that opened this case" shows the full conversation.

**What summary/context is passed:**
- Full conversation in `source_text`.
- Triage result (broker_next_step, client_prep, client_reply_draft) from merged context.
- `conversation_summary` in triage result (for future use).

**Workbench coherence:** Broker still sees one dominant next move, client prep, and draft. The conversation context makes it clear what was already asked and answered.

---

## 5. Validation Summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` (ui/) | **Pass** | UI compiles |
| `run_inbox_triage_scenarios.py` | **Pass** (29/29) | Category, urgency, escalation |
| `run_chen_kui_proxy_calibration.py` | **Pass** (13/13) | Draft tone, proxy style |
| `guardrail_inbox_triage.sh` | **Pass** | Scenario pack, API, persistence |
| `unified_intake_smoke_check.sh` | **Pass** | Full guardrail + manual checklist |

---

## 6. Business Value Impact

- **Customer experience:** Same-page guided intake feels more like a real service entry. Customers can add info without starting over.
- **Broker work reduction:** Broker receives a cleaner case with full conversation context. Less re-reading and guessing.
- **Industry-standard feel:** Progressive collection and handoff align with common intake patterns.

---

## 7. Remaining Blockers

1. **Progressive logic is heuristic:** "Enough info" is rule-based (2nd message or manual_followup_needed=false). No NLP extraction of collected fields yet.
2. **Conversation memory is session-only:** No user identity; each new "提交新问题" starts fresh.
3. **No explicit "progressive_answers" struct:** Broker sees conversation text but not a structured key-value summary (e.g. year=2021, model=Tesla). Deferred.

---

## 8. Recommended Next Step

Tighten the broker case card to optionally show a short "Collected from conversation" summary (e.g. vehicle year/model if add-car) when `source_text` contains multiple turns. Keep it lightweight.

---

## 9. 中文或中英混合宏观总结

**这次主要把什么从单轮结果改成了连续对话：**
- 客户入口从「提交 → 静态结果卡」改成「提交 → 系统回复 → 可继续补充 → 交办」。
- 同一页面内完成多轮对话，无需跳转。

**渐进式补资料现在怎么工作：**
- 第一轮回复沿用既有意图逻辑（加车问年份车型、付款问题要通知等）。
- 第二轮会把前后文合并再 triage，最多两轮后交办。

**Broker 工作台怎么接住这些上下文：**
- 交办时把完整对话存进 `source_text`，格式为 `[客户]` / `[系统]`。
- Broker 打开 case 能看到整段对话，知道已问过什么、客户答了什么。

**有没有困难或限制：**
- 「够不够」是启发式（第二轮或 manual_followup=false 即交办），没有做字段级提取。
- 对话记忆只在当前 session，没有用户身份。

**现在最适合演示哪条路径：**
1. 高风险：客户问「payment failed 怎么办」→ 系统要通知/截图 → 客户补「我发了」→ 交办。
2. 日常：客户问「加一台 2021 Tesla Model Y 报价」→ 系统要年份/车型/VIN 等 → 客户补「90210」→ 交办。

---

## 10. 如何打开前端 / 后端

| Item | Command / URL |
|------|---------------|
| **Start demo** | `bash scripts/run_demo_local.sh` |
| **Frontend** | http://localhost:5173/workbench/unified-intake |
| **Backend** | http://localhost:8001 (default) |
| **First tab** | 客户入口 (Customer Entry) |
| **Port caveats** | If 8001 busy, use `restore_8001_readiness.sh`. If 5173 bumps to 5174, use the URL shown in Vite. |

---

## 11. Conversation Walkthrough Simulation

### Example 1: High-risk case (payment failed)

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 客户问：这个英文 notice 说 payment failed，我现在怎么办？ |
| 2 | System | 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。 |
| 3 | Customer | 我发了截图在微信 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Broker | Case shows full conversation in source_text. broker_next_step: "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today." |

**Why better than one-shot:** Broker sees that the client already said they sent a screenshot. No need to ask again.

### Example 2: Daily-use case (add car / quote)

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | I bought a new BMW X5, how much is insurance? |
| 2 | System | I can start a quote for the new car. Send me the year, make/model, VIN if you have it, delivery date, zip or address, and main driver and I will check it. |
| 3 | Customer | 2024, 90210, picking up next week |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Broker | Case shows year, zip, delivery hint. broker_next_step reflects collected context. |

**Why better than one-shot:** Broker receives year, zip, delivery timing instead of only "BMW X5".

---

## 12. Digital Employees Used

**Builder, Auditor, Validator:** All three roles were executed by **Cursor** (this agent) in a single sequential pass:

1. **Builder:** Created design doc, implemented conversational UI, API changes, triage_conversation logic, broker handoff.
2. **Auditor:** Reviewed flow against design doc; confirmed no overclaim, no feature sprawl; handoff and UI stay bounded.
3. **Validator:** Ran npm build, run_inbox_triage_scenarios, run_chen_kui_proxy_calibration, guardrail_inbox_triage, unified_intake_smoke_check.

**Why Cursor:** The sprint was run entirely within Cursor. OpenClaw was not invoked. The plan specified "Builder → Auditor → Validator" as sequential roles; one Cursor session performed all three in order, using the same codebase access and tooling.

---

*End of sprint report*
