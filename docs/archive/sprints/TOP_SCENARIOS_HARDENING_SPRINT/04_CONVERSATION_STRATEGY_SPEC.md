# Conversation Strategy Spec

**Sprint:** Top Scenarios Hardening Master Sprint

---

## Shared Rules Across Scenarios

| Rule | Meaning |
|------|---------|
| **Answer-first** | Lead with conclusion or acknowledgment, then ask |
| **Reassure-first** | When "有办法吗", "发过了" — acknowledge before ask |
| **Next-best-question** | Ask 1–2 things per turn, not 6 |
| **Not too rigid** | Allow shorthand, mixed language |
| **Not too generic** | Do NOT "这段内容还不够完整" when intent is clear |
| **Clarify vs hand off** | Clarify when one critical field would help; hand off when enough |
| **Avoid robotic** | No "Thank you for reaching out"; office-natural tone |

## When to Clarify

- Add-car: missing year, model, or zip
- Add driver: missing which vehicle or driver info
- Premium: no policy/bill mentioned
- Missing doc: unclear which item or sent status

## When to Hand Off

- Threshold met (see MATURE_INTAKE_SKELETON)
- Customer says "先这样", "你先看"
- Turn count ≥ 2 (non–add-car)
- Add-car: (year+model) + zip present

## Anti-Patterns

- "Please provide more context" for add-car, payment, notice confusion
- "这段内容还不够完整" for 加个司机, bundling
- Routing premium + "我发你账单了" to payment_lapse_expiration

---

*See: 05_EXECUTION_OUTLINE.md*
