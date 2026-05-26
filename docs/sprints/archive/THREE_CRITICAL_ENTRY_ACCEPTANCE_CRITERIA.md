# Three Critical Entry Scenarios — Validation / Acceptance Criteria

---

## Pass/Fail Criteria (Practical)

| Criterion | Payment | Quote | Missing-doc |
|-----------|---------|-------|-------------|
| **Intent recognition** | category = payment_lapse_expiration or cancellation_warning | category = customer_question; add_vehicle detected | category = missing_document |
| **Answer-first quality** | Draft addresses payment urgency before asking | Draft acknowledges vehicle/quote before asking | Draft acknowledges "发过了" before asking |
| **Next-missing-info quality** | Asks only notice/screenshot/payment proof | Asks only 1–2 next fields (e.g. ZIP, year/model) | Asks only verify or resend, not generic |
| **Tone / reassurance** | Feels urgent but helpful | Feels broker-natural, not robotic | Feels empathetic, not dismissive |
| **Non-mechanical feel** | No "内容不够完整"; no "please provide more context" | No generic fallback for clear quote intent | No "请再发一次" without acknowledgment |

---

## Blocklist (Fail if present)

- "这段内容还不够完整" for clear payment/quote/missing-doc intent
- "please provide more context" for clear intent
- "Thank you for reaching out" / "feel free to ask"
- Draft asks 6 things when 1–2 suffice
- Missing-doc reply ignores "发过了" / "already sent"
