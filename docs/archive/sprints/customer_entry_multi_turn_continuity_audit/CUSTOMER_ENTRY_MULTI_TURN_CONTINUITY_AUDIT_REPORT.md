# Customer Entry Multi-Turn Continuity Audit Report

**Sprint:** Customer Entry Multi-Turn Continuity Audit Sprint  
**Date:** 2026-03-15  
**Execution mode:** Structured diagnostic / investigation

---

## 1. Sprint theme

- **What was investigated:** Why Customer Entry feels like single-turn intake + case handoff instead of true continuous multi-turn conversation.
- **Why now:** Founder observed that after one question, the UI shows 查看工作台 / 提交新问题 and appears "finished," with no obvious path to continue the same conversation.

---

## 2. Control docs created

- `01_SPRINT_BLUEPRINT.md` — Mission, key questions, working method
- `02_EXECUTION_OUTLINE.md` — Step-by-step execution, key files
- `03_DIAGNOSTIC_ACCEPTANCE_CRITERIA.md` — Must-answer list, trace requirements, pass criteria

---

## 3. Reproduction summary

### Input tested

"我才买了一个2026年的丰田花冠，我想问一下大约半年的保费是多少？"

(Add-car quote: year 2026, model Toyota Corolla, asking about ~6-month premium. Per MATURE_INTAKE_SKELETON, add-car needs year+model + zip/delivery/driver. This message has year+model but **no zip**.)

### What the UI did

1. User submits first message.
2. Frontend sends `{ text: "...", persist_case: true, conversation_turns: [] }` — **empty turns** because `turns` state is captured before the new customer turn is added.
3. Backend receives empty `conversation_turns` → uses **single-message path** (`triage_message` + hardcoded `handoff_ready = True`).
4. Backend returns `handoff_ready: true` (always for first message in this path).
5. Frontend receives response → `handoffReady` becomes true.
6. **Input area is hidden** (`{!handoffReady && (...)}`), replaced by handoff card with:
   - 查看工作台
   - 提交新问题

### What made it feel single-turn

- After one reply, the input box **disappears**.
- User cannot type a follow-up in the same thread.
- Only options: switch to broker workbench or start a **new** conversation (提交新问题 clears `turns`).
- No "继续补充" or "add more info" path in the same thread.

### API probe result

```
First message (no conversation_turns): handoff_ready = True (single-message path)
With conversation_turns: triage_conversation path used; handoff_ready depends on logic
```

For add-car with year+model but no zip, **triage_conversation** would correctly return `handoff_ready: false` and ask for zip. But the **first message never reaches triage_conversation** because the backend uses the single-message path when `turns` is empty.

---

## 4. Frontend state audit

### How state currently works

- `turns`: array of `{ role, content, triageResult? }` — customer and system messages.
- `handoffReady`: derived from `turns[turns.length-1]?.triageResult?.handoff_ready`.
- Input card: rendered only when `!handoffReady` (line 1153).
- Handoff card: rendered when `handoffReady` (line 1219).

### Where continuity breaks

1. **Submit flow:** `conversationTurnsForApi = turns` — uses **current** `turns` state. When user submits first message, `setTurns(prev => [...prev, customerTurn])` is called but React state updates asynchronously. So `turns` is still `[]` when building the API payload. **First message always sends empty conversation_turns.**

2. **When handoff_ready:** The input card is **completely hidden**. There is no "continue in same thread" option. User must either 查看工作台 or 提交新问题 (which calls `handleNewConversation()` and clears everything).

3. **No "continue same case" path:** Even if the user had a `lastCaseId`, there is no UI to append a follow-up to that case from Customer Entry. The append-message API exists (`/api/inbox/cases/{id}/append-message`) but Customer Entry does not use it for continuation.

### Likely frontend cause

- **Primary:** Input is hidden when `handoffReady` — UX design choice that makes the thread feel "done."
- **Secondary:** No "继续补充" or "add more to this case" option when handoff card is shown.

---

## 5. Backend / routing audit

### How handoff_ready / case_creation_suggested / workflow affect the flow

**Critical finding:** In `services/fiqa_api/routes/inbox_triage.py` (lines 204–209):

```python
turns = request.conversation_turns
if turns:
    result = triage_conversation(text, [...])  # Multi-turn path — proper handoff logic
else:
    result = triage_message(text)
    result["handoff_ready"] = True   # ALWAYS True for first message!
```

When `conversation_turns` is empty (first message), the backend:
1. Uses `triage_message` (single-message triage) — **no** add-car handoff-threshold logic.
2. **Unconditionally** sets `handoff_ready = True`.
3. Never runs `triage_conversation`, which has `_should_handoff`, `_add_car_enough_for_handoff`, `_get_next_ask_draft`, etc.

### Per MATURE_INTAKE_SKELETON

- Add-car: enough when (year+model) + (zip OR delivery OR driver).
- First message "2026 Toyota Corolla, 半年保费" has year+model but **no zip** → should **ask for zip**, not hand off.

### Likely backend cause

**Primary root cause:** The single-message path **always** sets `handoff_ready = True`, bypassing all multi-turn handoff logic. First message never gets a chance to ask for zip or other missing fields.

---

## 6. Session / persistence audit

### Whether case/thread continuity exists

- **Frontend:** `turns` is in-memory React state. No persisted conversation_id or thread_id. Refresh loses everything.
- **Backend:** Case is persisted when `handoff_ready` (or single message). Case has `case_id`, `source_text`, `case_messages`. Append-message API exists for broker workbench paste flow.
- **Customer Entry → append:** Customer Entry does **not** call append-message when user would "continue" the same case. It has no concept of "this input continues case X."

### Whether append-message path is actually used

- Append-message is used by **Broker Workbench** when broker pastes a follow-up into an existing case.
- **Customer Entry** does not use it. When user would continue, they must 提交新问题 → starts fresh.

### Likely continuity gap

- No stable conversation/thread id in Customer Entry.
- No "continue this case" flow from customer side.
- Backend supports multi-turn via `conversation_turns`, but first message never sends them (empty), so backend never enters multi-turn path.

---

## 7. UX / product intent audit

### Whether this was originally intentional

Design docs (`CONTINUOUS_CUSTOMER_INTAKE_MVP.md`, `MATURE_INTAKE_SKELETON.md`, `CUSTOMER_ENTRY_REPLY_STRATEGY.md`) explicitly describe:
- Same-page conversational flow
- Progressive collection: ask 1–2 things, then ask next missing field
- Hand off only when enough info
- Add-car: ask for zip when year+model present

**Intent:** True multi-turn, progressive intake, hand off when enough.

### Whether it is still appropriate

Yes. The design intent is correct. The implementation diverges:
- Backend single-message path short-circuits to handoff.
- Frontend hides input when handoff, offering no continuation path.

### Conclusion

This is **not** intentional single-turn design. It is an **implementation bug** (backend) plus **UX choice** (frontend) that together produce single-turn behavior.

---

## 8. Final judgment

### Is Customer Entry currently true multi-turn?

**No.** It behaves as single-turn intake + handoff because:
1. First message triggers `handoff_ready = true` unconditionally (backend).
2. Input is hidden when handoff (frontend).
3. No "continue same thread" option.

### Primary root cause

**Backend:** Single-message path in `inbox_triage.py` always sets `handoff_ready = True` when `conversation_turns` is empty. First message never runs `triage_conversation`, so add-car (and other) handoff thresholds are never applied.

### Secondary root cause

**Frontend:** When `handoff_ready`, input is hidden and replaced by handoff card. No "继续补充" or "add more to this case" path. User can only 查看工作台 or 提交新问题 (new conversation).

### Is the main issue frontend, backend, session model, or UX intent?

**Backend** is the main issue — it triggers handoff too early. **Frontend** amplifies the effect by hiding input. Session model is adequate for demo (in-memory turns); the break is in the first-message routing, not persistence.

### Minimum high-value fix direction

**Backend fix (highest impact):** When `conversation_turns` is empty, call `triage_conversation(text, [{"role": "customer", "text": text}])` instead of `triage_message(text)` + `handoff_ready = True`. This routes the first message through proper multi-turn logic. Add-car will then ask for zip when missing.

**Frontend improvement (second):** When `handoff_ready`, consider showing "继续补充" alongside 查看工作台 / 提交新问题, so user can add more info without starting fresh. Or keep input visible with a softer handoff card (e.g., "已整理，如需补充可继续输入").

### Best next sprint recommendation

**Backend handoff-threshold fix** — Route first message through `triage_conversation` so handoff logic applies. This is a small, targeted change with high impact.

**Optional follow-up:** Frontend continuity polish — "继续补充" or keep input visible when handoff, to support edge cases where user wants to add one more thing.

---

## 9. 中文宏观总结

- **现在是不是连续多轮对话？** 不是。目前表现为一次一问 + 转交。
- **为什么看起来像一次一问？** 后端对首条消息强制 `handoff_ready=true`，前端在 handoff 时隐藏输入框，只显示「查看工作台」「提交新问题」。
- **最大问题在前端、后端还是会话模型？** 最大问题在**后端**：首条消息走单条路径，不经过多轮逻辑，直接 handoff。前端在 handoff 时隐藏输入是次要因素。
- **下一步最该修什么？** 后端：首条消息也走 `triage_conversation`，让 add-car 等流程按 MATURE_INTAKE_SKELETON 正确判断是否该继续追问（如要邮编）。

---

## 10. COPY/PASTE FOUNDER BLOCK

```
Customer Entry Multi-Turn Continuity — Audit Summary

Is Customer Entry truly multi-turn right now? NO. It behaves as single-turn intake + handoff.

Biggest root cause: Backend always sets handoff_ready=true for the first message (when no conversation_turns). The first message never runs through triage_conversation, so add-car and other flows never get a chance to ask for missing fields (e.g., zip) before handoff.

Best next fix direction: Change the backend so the first message also uses triage_conversation with a single turn. One small change, high impact. Add-car will then correctly ask "先把地址邮编发我" when year+model present but zip missing.

Should founder treat current flow as one-shot intake or ongoing conversation? Treat it as one-shot intake until the backend fix is deployed. After the fix, Customer Entry will support true multi-turn for add-car and similar flows.
```
