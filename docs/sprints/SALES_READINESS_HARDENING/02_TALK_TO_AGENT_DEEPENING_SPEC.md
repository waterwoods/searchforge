# Talk to Agent Deepening Spec

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17

---

## 1. When Talk to Agent Should Appear or Be Encouraged

| Trigger | When | Visibility |
|---------|------|------------|
| **Quick-start button** | Always when turns.length === 0 | Same prominence as 报价, 变更, etc. |
| **Welcome card** | Always | "如需人工协助，可点击「联系人工」" |
| **Free-text detection** | User types "联系人工", "联系陈奎", "联系办公室", "我要找人工", "talk to agent" | Route to handoff immediately |

**Decision:** Add free-text markers so Talk to Agent works when user types, not only when they click.

---

## 2. How It Should Be Worded

### Button
- Label: **联系人工**
- Short label: **联系人工**

### Starter message (button click)
- "我想联系陈奎办公室"

### Customer-facing reassurance (handoff reply)
- **ZH:** "好的，已帮您转给陈奎办公室，他们会尽快联系您。"
- **EN:** "Got it. We've forwarded your request to the office. They will contact you shortly."

### When offered mid-conversation (future)
- "如需人工协助，可随时说「联系人工」或点击上方按钮。"

---

## 3. How It Should Reassure the Customer

| Moment | Reassurance |
|--------|-------------|
| After click / detection | "已帮您转给陈奎办公室，他们会尽快联系您。" |
| Persist / save | "已整理成 case，办公室会尽快跟进。" |
| No "Are you sure?" | User chose; we honor it. No confirmation step. |

---

## 4. What workflow_state / Summary / Context Should Be Included

| Field | Value |
|-------|-------|
| `issue_category` | `customer_requested_human` |
| `handoff_ready` | `true` |
| `lifecycle_status` | `handoff_pending` |
| `next_best_question` | `""` |
| `conversation_summary` | "Customer requested to speak with office / 客户要求联系人工" |
| `broker_next_step` | "Customer requested human contact. Call or message back promptly." |
| `client_reply_draft` | "好的，已帮您转给陈奎办公室，他们会尽快联系您。" |
| `collected_fields` | `["customer_requested_human"]` or `[]` |
| `still_needed_fields` | `[]` |

**When multi-turn before Talk to Agent:** Include prior context in `conversation_summary` or `source_text` so office sees what customer was discussing.

---

## 5. What the Office Should See Immediately

| Item | Content |
|------|---------|
| **Case focus** | "联系人工 / Customer requested human" |
| **Your next move** | "Customer requested human contact. Call or message back promptly." |
| **Recent customer messages** | Last 2–3 customer messages (including "我想联系陈奎办公室" or typed request) |
| **Context hint** | "客户要求联系人工" badge when issue_category = customer_requested_human |
| **Collected** | Empty or ["customer_requested_human"] |
| **Still needed** | Empty |

---

## 6. What Makes Talk to Agent "Good Enough" for Trial

1. **Always visible** — Button + welcome mention
2. **Works when typed** — Free-text markers route to handoff
3. **Reassuring reply** — "已帮您转给办公室，他们会尽快联系您"
4. **Office sees clearly** — Case focus "联系人工"; broker_next_step actionable
5. **No friction** — No "Are you sure?"; immediate handoff
6. **Context preserved** — If multi-turn before request, prior context in handoff

---

*End of Talk to Agent Deepening Spec*
