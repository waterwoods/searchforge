# Human Front Door + Talk-to-Agent — Talk-to-Agent Policy Spec

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Created:** 2026-03-15

---

## 1. When and Where "联系人工" Appears

| Location | When | Visibility |
|----------|------|-------------|
| Quick-start buttons | Always, when turns.length === 0 | Same prominence as 报价, 变更, etc. |
| Welcome card secondary | Always | "如需人工协助，可点击「联系人工」" |
| During conversation | N/A (buttons hidden after first turn) | User can type "联系人工" in free text |

**Decision:** Always visible in button set. No contextual show/hide.

---

## 2. Whether Always Visible or Contextually Shown

**Decision:** Always visible. User should never have to search for the human path.

---

## 3. How It Should Behave

| Step | Behavior |
|------|----------|
| 1 | User clicks "联系人工" |
| 2 | If input empty: submit starter message "我想联系陈奎办公室" |
| 3 | Backend detects customer_requested_human (via soft_route or text markers) |
| 4 | Backend returns handoff_ready=true, broker_next_step="Customer requested human contact. Call or message back promptly." |
| 5 | Frontend shows handoff card: "好的，已帮您转给陈奎办公室，他们会尽快联系您。" |
| 6 | Case persisted with issue_category=customer_requested_human (or equivalent) |

**No multi-turn intake.** Immediate handoff.

---

## 4. What It Should Say

### Button
- Label: "联系人工"
- Optional: "联系陈奎办公室" (can be same or sublabel)

### Starter Message
- "我想联系陈奎办公室" (I want to contact Chen Kui's office)

### System Reply (Handoff)
- ZH: "好的，已帮您转给陈奎办公室，他们会尽快联系您。"
- EN: "Got it. We've forwarded your request to the office. They will contact you shortly."

### Broker View
- broker_next_step: "Customer requested human contact. Call or message back promptly."
- conversation_summary: "Customer requested to speak with office / 客户要求联系人工"

---

## 5. Immediate Case vs Confirmation

**Decision:** Immediate handoff. No "Are you sure you want to talk to an agent?" — that would undermine trust. User clicked; we honor it.

---

## 6. How This Path Differs from Normal AI-Guided Intake

| Aspect | Normal Intake | Talk-to-Agent |
|--------|---------------|---------------|
| Multi-turn | Yes, collect fields | No |
| handoff_ready | When enough info | Immediately |
| broker_next_step | Intent-specific | "Customer requested human contact" |
| collected_fields | year, make_model, etc. | [] or ["customer_requested_human"] |
| Client reply draft | Intent-specific | "已帮您转给办公室，他们会尽快联系您" |

---

## 7. Backend Implementation

### Option A: soft_route
- Frontend sends soft_route="talk_to_agent" with text "我想联系陈奎办公室"
- Backend checks soft_route first; if talk_to_agent, return handoff immediately

### Option B: Text markers
- Add markers: "联系人工", "联系陈奎", "联系办公室", "talk to agent", "want to speak to someone"
- Rule-based triage returns customer_requested_human
- Add to VALID_CATEGORIES; _should_handoff always true for this category

**Recommendation:** Use both. soft_route for button click; markers for free-text "联系人工".

---

*See also: UX Design Spec, Execution Outline*
