# Handoff / Office Readiness Spec

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17

---

## 1. What the Broker/Assistant Should Receive on Handoff

| Item | Source | Display |
|------|--------|---------|
| **Case focus** | issue_category, collected_fields, still_needed_fields | Tag: "Add car quote", "联系人工", "Missing document", etc. |
| **Your next move** | broker_next_step | One operational sentence |
| **Collected** | collected_fields | Green chips |
| **Still needed** | still_needed_fields | Orange chips |
| **Client reply draft** | client_reply_draft | Editable; broker confirms before sending |
| **Recent customer messages** | case_messages (last 2–3 customer) | Above fold; no parsing raw text |
| **Correction / context hint** | follow_up_type | Badge: "Customer corrected", "Client says already sent" |
| **Lifecycle status** | lifecycle_status | "Ready for handoff" / "Collecting" / "Handed off" |

---

## 2. What Raw Messages / Corrections / Context Hints Should Be Visible

| Type | When | Badge / Display |
|------|------|-----------------|
| **Correction** | follow_up_type = correction | "Customer corrected/clarified" |
| **Already sent** | follow_up_type = already_sent | "Client says already sent" |
| **Customer requested human** | issue_category = customer_requested_human | "客户要求联系人工" or "Contact requested" |
| **Human confirmation** | human_confirmation_required | "Verify before acting: …" |

---

## 3. What Next Action Should Be Visible

- **broker_next_step** always shown as "Your next move"
- For customer_requested_human: "Customer requested human contact. Call or message back promptly."
- For billing + already_sent: "Verify receipt of notice/screenshot; confirm with client if needed."

---

## 4. How Edge-Case Information Should Survive Handoff

| Edge case | Survival path |
|-----------|---------------|
| Billing "我发你了" | follow_up_type=already_sent; collected includes already_sent_claimed; broker_next_step reflects verify-receipt |
| Late correction | follow_up_type=correction; conversation_summary or context hint; correction badge |
| Talk to Agent mid-flow | Prior turns in source_text; conversation_summary includes prior context |

---

## 5. What Makes the Handoff Actually Usable

1. Broker understands case in <5 seconds
2. Next move is one clear sentence
3. Correction/already_sent/human-request visible without parsing
4. Recent customer messages above fold
5. No re-asking for what customer already said

---

*End of Handoff / Office Readiness Spec*
