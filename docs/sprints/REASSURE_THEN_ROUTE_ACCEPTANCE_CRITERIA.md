# Reassure-Then-Route Intake Sprint — Acceptance / SLA Criteria

**Sprint**: Reassure-Then-Route Intake

---

## 1. Answer-First Quality

| Scenario | Criterion |
|----------|-----------|
| Payment failed / cancellation | Draft states what matters first (e.g. "现在最关键的是...") before asking for notice |
| Claim / hit-and-run | Draft gives first-step guidance (safety, photos, plate) before asking for details |
| Missing document + already sent | Draft acknowledges "发过了" before asking for resend |
| Notice confusion | Draft explains likely meaning or asks for full notice — not generic "provide context" |

---

## 2. Reassurance Quality

| Scenario | Criterion |
|----------|-----------|
| High-emotion (payment, claim) | Draft includes brief reassurance (e.g. "先别慌", "先确保人没事") |
| Premium too high + "有办法吗" | Draft includes "一般有办法的" or equivalent |
| Already sent | Draft includes "我这边帮你核对" or equivalent |

---

## 3. Uncertainty Handling

| Scenario | Criterion |
|----------|-----------|
| When system cannot confirm | Draft says "办公室会确认" or "office will confirm" — not vague |
| Payment/cancellation + "already paid" | Draft says broker will verify — no confident claim |

---

## 4. Over-Collection Avoidance

| Scenario | Criterion |
|----------|-----------|
| Add-car | Asks 1–2 next things, not 6-item checklist |
| Missing document | Asks for specific item, not "all documents" |

---

## 5. Case-Creation Timing

| Criterion |
|-----------|
| `handoff_ready` true when enough info collected |
| `case_creation_suggested` or equivalent when meaningful point reached (optional) |
| No silent auto-create on every message when multi-turn |

---

## 6. Mechanical Tone Avoidance

| Blocklist |
|-----------|
| "Dear", "Best regards", "Thank you for reaching out" |
| "We are reviewing your message" |
| "Please provide more context" for obvious intents |

---

*End of criteria*
