# Demo Story — Unified Intake

**Purpose:** One demo narrative for all audiences.  
**Founder steps:** [`BROKER_DEMO_FLOW.md`](./BROKER_DEMO_FLOW.md)  
**Broker summary:** [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md)

---

## 1. What problem exists?

California auto insurance brokers receive messy inbound messages — WeChat threads, carrier notices, payment failures, "I already sent that document" follow-ups. Urgent cases get buried. Brokers re-read entire chains, re-ask for info already provided, and write similar replies from scratch every day.

---

## 2. What does the customer do?

A customer sends a messy message (or the broker pastes what they received):

> Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？

The broker does **not** need to clean it up first.

---

## 3. What does Unified Intake do?

Unified Intake reads the message and creates **one structured case**:

| Output | Example |
|--------|---------|
| **Case focus** | Payment / cancellation risk |
| **Urgency** | Same-day action |
| **Your next move** | Confirm whether payment failed; check carrier balance; help client fix today |
| **Collected** | Client mentioned carrier notice |
| **Still needed** | Payment screenshot, notice copy |
| **Draft reply** | Editable text ready to copy to WeChat |

**Nothing is auto-sent.** Broker reviews, edits, copies, sends manually.

---

## 4. What appears in workbench?

**Broker Workbench** shows:

- **Queue** — Work now vs waiting; urgency badges
- **Case card** — Case focus, Your next move, Collected/Still needed chips, draft
- **Recent cases** — Reopen follow-ups; resume where you left off
- **Simulation Assistant** (optional) — Practice scenarios for trial/training

**Customer Entry** tab (optional demo beat): customer-facing input → first response → case appears in workbench.

---

## 5. What happens next?

1. Broker acts on **Your next move**
2. Edits draft → copies to WeChat
3. Updates case status (waiting on client, done, etc.)
4. When customer replies → broker pastes new message → case updates in context
5. Urgent cases stay visible — not buried in message noise

---

## 6. Why is this better than email/text chaos?

| Chaos | Unified Intake |
|-------|----------------|
| Scroll entire WeChat thread | Case focus + next move at top |
| "Did they send the dec page?" | Collected / Still needed chips |
| Forget to follow up today | Same-day action + queue triage |
| Write reply from scratch | Draft starting point |
| Lose context on reopen | Resume here + waiting on + notes |

---

## 7. What should never be promised?

- Connected to WeChat, email, or carrier systems
- Reads screenshots or PDFs inside the product
- Automatically sends replies to customers
- Full CRM, billing, or multi-office management
- Perfect handling of every language mix or edge case
- Production analytics / ROI guarantees from demo queue counts

---

## THE_15_MINUTE_DEMO

| Min | Beat | Script |
|-----|------|--------|
| 0–1 | **Promise** | "Messy message → structured case. You send. No auto-send." |
| 1–2 | **Open** | Load founder demo queue at `/workbench/unified-intake` |
| 2–5 | **Urgency** | Cancellation case: Case focus, Same-day action, Your next move |
| 5–8 | **Operations** | Missing document: waiting on client, verify receipt |
| 8–11 | **Revenue** | Add-car: Collected / Still needed across turns |
| 11–13 | **Control** | Human confirmation badge; edit draft; copy (don't auto-send) |
| 13–15 | **Close** | 3 value questions; one-sentence pilot offer |

**Pre-flight:** `demo_pre_checklist.sh` + `guardrail_inbox_triage.sh`

---

## THE_5_MINUTE_DEMO

| Min | Beat |
|-----|------|
| 0–0:30 | One-sentence promise |
| 0:30–2 | Load queue → Cancellation case only (urgency + next move) |
| 2–4 | Add-car case → Collected / Still needed chips |
| 4–5 | "You review and send. Which scenario fits your office?" |

**Skip:** Customer Entry, missing doc, Simulation Assistant unless asked.

---

## THE_60_SECOND_DEMO

**Say:**

> 客户发来 messy 消息，系统整理成一个 case：紧急程度、下一步、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

**Do:** Open workbench → Load founder demo queue → point to cancellation case → point to Your next move + Collected chips.

**Ask:** "Would this help your office triage faster?"

---

*End of demo story*
