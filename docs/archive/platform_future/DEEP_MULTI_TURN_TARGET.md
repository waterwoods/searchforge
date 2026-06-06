# Deep Multi-Turn Target — 5 Core Flows

**Sprint:** Five Core Flows Deep Multi-Turn + Structured Case Report  
**Purpose:** Define what "good 3–4 turn behavior" means before changes.

---

## 1. Turn-by-Turn Behavior

| Turn | System should | Avoid |
|------|---------------|-------|
| **Turn 1** | Acknowledge what customer said; ask 1–2 next things; no generic "provide more context" when intent is clear | Checklist dump; robotic "thank you for reaching out" |
| **Turn 2** | Use new info; acknowledge before next ask or handoff; if enough collected → hand off with warm close | Ignore what customer just said; repeat same ask |
| **Turn 3** | Preserve context from T1+T2; acknowledge; ask one more thing OR hand off if enough | Flow switch; wrong follow-up ask; forget "already sent" |
| **Turn 4** | Same as T3; hand off when enough; reflect all collected info in structured output | Context loss; flow pollution |

---

## 2. Context Preservation

- **Across turns:** `conversation_summary` and `collected_fields` / `still_needed_fields` must reflect the full conversation, not just the last message.
- **"Already sent":** When customer says 发你了 / sent / 又发了, system must acknowledge and hand off with "好的，收到了" (or equivalent); structured output must show `customer_says_sent_*`.
- **Correction:** When customer corrects (不是 X，是 Y), system must use "好的，明白了" and update intent in summary.

---

## 3. Flow Stability

- **No flow switching:** If T1 is add-car, T2–T4 stay add-car. Same for claim, missing doc, renewal, notice/payment.
- **Progressive ask:** Ask only the next 1–2 most useful things. Do not re-ask what was already provided.
- **Handoff timing:** Hand off when thresholds met (see MATURE_INTAKE_SKELETON) or when customer says "先这样" / "你先看".

---

## 4. When Enough Is Collected

| Flow | Enough when |
|------|-------------|
| Add car | (year+model or VIN) + (zip OR delivery OR driver) |
| Notice / payment | Notice, screenshot, or "I sent it" mentioned |
| Missing document | Item identified + sent status clear |
| Claim intake | Accident details, photos, other driver info mentioned (or clear partial) |
| Renewal | Policy or bill mentioned |

---

## 5. Structured Result Over Time

- **Per turn:** `collected_fields` and `still_needed_fields` update as new info arrives.
- **At handoff:** Final structured output must show what was collected across all turns.
- **Broker visibility:** Case focus, collected, still needed, next move — all from structured data when available.

---

## 6. Human Confirmation

- Sensitive items (payment proof, VIN, driver) → broker must confirm before acting.
- Structured output should surface "Human confirmation recommended" for high-risk fields when applicable.
- Keep lightweight: badge or compact note, not full compliance system.

---

*Aligned with MATURE_INTAKE_SKELETON, CUSTOMER_ENTRY_REPLY_STRATEGY, FIVE_BUSINESS_FLOWS_TARGETS.*
