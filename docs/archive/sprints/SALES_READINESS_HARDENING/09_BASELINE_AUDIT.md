# Baseline Audit — Sales Readiness Hardening Sprint

**Purpose:** Audit current product from sales-readiness perspective. Classify trust/readiness quality; document biggest weaknesses.

---

## 1. Current Trust / Readiness Quality

| Area | Status | Notes |
|------|--------|------|
| **Talk to Agent (button)** | Acceptable | Works via soft_route; immediate handoff; workflow_state consistent |
| **Talk to Agent (free-text)** | Weak | NOT implemented — user must click button; typing "联系人工" not detected |
| **Talk to Agent handoff payload** | Acceptable | broker_next_step, client_reply_draft, conversation_summary present |
| **Office display for Talk to Agent** | Acceptable | inferCaseFocusFromStructuredFields returns "联系人工" for customer_requested_human |
| **Billing "我发你了"** | Acceptable | MT40 in config; already_sent path exists; verify routing |
| **Late correction** | Acceptable | follow_up_type=correction; badge exists; verify append preserves |
| **Handoff / workbench** | Strong | Recent messages, correction/already_sent badges, Collected/Still needed |

---

## 2. Classification

| Area | Classification | Reason |
|------|----------------|--------|
| **Talk to Agent free-text** | Trial-risky | Customer types "联系人工" → ignored; feels like escape hatch not found |
| **Talk to Agent overall** | Weak | Button works but feels lightweight; no mid-flow support |
| **Billing "我发你了"** | Commercially important | High-frequency; already_sent handoff must work |
| **Handoff payload** | Acceptable | Could add customer_requested_human handoff phrase |
| **Office usability** | Strong | Recent messages, badges, next move visible |

---

## 3. Biggest Current Trust Weakness

**Talk to Agent only works via button.** If a customer types "联系人工" or "我要找人工" mid-conversation, the system does not detect it and continues triage. This makes Talk to Agent feel like a thin escape hatch — visible only when you know to click, not when you naturally ask for human help.

---

## 4. Biggest Current Office Handoff Weakness

**customer_requested_human cases** use generic handoff phrasing. handoff_phrases.json has no `customer_requested_human` or `talk_to_agent` entry; the backend hardcodes the reply. Office display is acceptable (case focus "联系人工") but could add explicit "客户要求联系人工" badge for consistency with correction/already_sent.

---

## 5. Biggest Current Edge-Case Risk

**Billing "我发你了"** — If the already_sent path does not fire correctly for "通知我发你了，你看下" or "账单我发你微信了", the system may re-ask for the notice, breaking trust. MT40 exists; need to verify triage routes correctly.

---

## 6. Biggest "Still Feels MVP" Issue

**Talk to Agent feels like a button, not a service capability.** It works when you click, but:
- No free-text detection
- No mid-flow "我想直接跟人说" support
- Handoff could be more reassuring with explicit handoff phrase in config

---

## 7. What Is Already Solid

- Multi-turn continuity
- Workflow state backbone
- Add-car, payment, missing doc, renewal, claim flows
- Workbench: Recent messages, correction/already_sent badges
- Standard scenario package definition
- Guardrail scripts, simulations

---

*End of Baseline Audit*
