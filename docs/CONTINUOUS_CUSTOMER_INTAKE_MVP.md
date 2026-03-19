# Continuous Customer Intake MVP — Design

**Purpose:** Define the conversational intake architecture for the Customer Entry tab.  
**Sprint:** Continuous Conversational Intake  
**Scope:** Same-page guided intake, progressive collection, handoff to broker workbench.

---

## 1. Customer-Side Same-Page Conversation Flow

```
Customer opens 客户入口
    ↓
Customer types one messy message
    ↓
System responds inline (same page, no navigation)
    ↓
If key info missing → System asks 1–2 focused follow-up questions
    ↓
Customer can answer in the same conversation
    ↓
Once enough info exists → System forms broker-side case
    ↓
Customer sees "office will review / next step" state
    ↓
Broker can open the cleaned case in the workbench
```

**Key principle:** One conversation area, one input area, one clear CTA. No jarring "new page" feeling.

**Mature intake skeleton:** All scenarios follow the same flow shape: detect → ask → enough? → hand off. See `docs/MATURE_INTAKE_SKELETON.md`.

---

## 2. Progressive Information Collection Pattern

| Intent | First reply | Next ask (if missing) | Enough when |
|--------|-------------|------------------------|--------------|
| Add car / quote | Ask year, model, VIN, ZIP, driver, delivery date | 1–2 most useful missing pieces | Year+model OR VIN; ZIP; driver hint. Chinese "买了"/"保费多少钱" + vehicle = add-car. |
| Remove car | Ask sale date, vehicle details, transfer status | Sale date if not given | Vehicle identified + sale date |
| Premium review | Ask current policy, renewal notice, latest bill | Policy or bill | Policy or bill mentioned |
| Payment failed / cancellation | State urgency, ask for notice/payment | Notice or payment proof | Notice or payment mentioned |
| English notice confusion | Explain likely meaning, ask for full notice | Full notice or clearer photo | Full notice or enough to triage |
| Missing document | Name missing item, ask for resend | Exact item, whether already sent | Item identified |
| DMV / SR-22 | Explain workflow, ask for notice | DMV notice, suspension letter | Notice or enough to advise |

**Rules:**
- Ask only 1–2 items per turn.
- Avoid generic "please provide more context" when intent is obvious.
- Keep tone short, calm, office-natural (Chen Kui proxy style).

---

## 3. When to Ask vs When to Hand Off

| Condition | Action |
|-----------|--------|
| First message, intent clear, key fields missing | Ask 1–2 focused questions |
| First message, intent clear, enough info | Hand off immediately |
| First message, intent unclear | Light clarification ask |
| Follow-up message, still missing critical fields | Ask next 1–2 items |
| Follow-up message, now has enough | Hand off |
| 2+ follow-up turns with no progress | Hand off with "office will review" |

**Handoff trigger:** Either (a) enough info collected, or (b) max 2–3 follow-up asks reached, or (c) customer message suggests they want to stop (e.g. "先这样", "你先看").

**Second-turn quality:** For add-car quote, the system asks for the next most useful missing field (zip, delivery, driver) when the customer gives partial info in turn 2. It does not hand off too early. See `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` §4.

---

## 4. What Summary/Context Goes to Broker Workbench

When handoff occurs, the broker case receives:

| Field | Content |
|-------|---------|
| `source_text` | Full conversation (customer + system turns) or summary |
| `conversation_summary` | Short summary: likely issue, urgency, what customer asked, what was collected |
| `progressive_answers` | Key-value pairs from conversation (e.g. year=2021, model=Tesla Model Y) |
| `broker_next_move` | Actionable next step given the collected context |
| `client_reply_draft` | Latest customer-facing state or draft for broker to send |
| `what_still_needed` | If any critical info still missing after handoff |

**Broker sees:** A cleaner case than raw first message. The conversation context is visible so broker knows what was already asked and answered.

---

## 5. What Is Real vs Mock/Demo-Safe

| Area | Status |
|------|--------|
| Same-page conversation UI | **Real** |
| Progressive follow-up logic | **Real** (rule-based + optional LLM) |
| Conversation → case handoff | **Real** |
| Case persistence with conversation context | **Real** |
| "Enough info" heuristics | **Heuristic** (rule-based; not full NLP) |
| Conversation memory across sessions | **Demo-only** (local; no user identity) |
| Full chat memory across all users | **Deferred** |

---

## 6. MVP Experience Summary

1. **Customer opens 客户入口** — Sees one input box, one CTA.
2. **Customer types messy message** — e.g. "客户问：这个英文 notice 说 payment failed，我现在怎么办？"
3. **System replies inline** — "这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。"
4. **If missing info** — System asks 1–2 focused questions (e.g. "请把最新通知或付款截图发我").
5. **Customer continues** — Types follow-up in same input.
6. **System responds again** — Either another ask or handoff.
7. **Handoff** — "办公室会尽快处理，有结果会联系您。" + 查看工作台.
8. **Broker** — Opens case with conversation summary, collected answers, broker next move.

---

*End of design doc*
