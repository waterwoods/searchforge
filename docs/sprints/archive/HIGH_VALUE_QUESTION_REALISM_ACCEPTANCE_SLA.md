# High-Value Question Realism — Acceptance / SLA Criteria

**Sprint:** High-Value Question Realism + Product Polish  
**Created:** 2026-03-14

---

## 1. More Realistic Customer Voice

| Criterion | Pass | Fail |
|-----------|------|------|
| First-person direct | Customer speaks as "我…" / "I…" when natural | Third-person "客户说…" when customer would speak |
| Natural short openings | "刚撞了" / "payment failed 怎么办" | "客户问：这个英文 notice 说 payment failed…" |
| Life context | "下周提车" / "对方跑了" | Generic "need quote" |
| Emotional tone | Appropriate urgency, confusion, frustration | Flat, label-like |

---

## 2. Better Product Usefulness

| Criterion | Pass | Fail |
|-----------|------|------|
| Still need to collect | Clear, actionable list | Vague or missing |
| Trust boundary | Visible, office-safe | Hidden or overpromising |
| Broker response style | Natural, progressive ask | Generic "provide more context" |

---

## 3. Acceptable Routing / Handling Quality

| Criterion | Pass | Fail |
|-----------|------|------|
| Category correct | Expected category in scenarios | Wrong category (e.g. premium_too_high → renewal_reminder) |
| Urgency correct | Critical for cancellation/payment | Downgraded to low |
| Draft quality | Contains expected phrases | Generic fallback |

---

## 4. Weak / Generic Phrasing (Avoid)

- "客户问：…" when customer would speak directly
- "客户说…" as wrapper for first-person
- Label-like: "Payment failed scenario"
- Test-case-like: "Underwriting requested driver's license copy. Client says \"I already sent it last week.\""
- Overly neat, formal carrier language when broker shorthand is realistic

---

## 5. Visible After Frontend Redeploy

- Updated scenarios visible in Simulation Assistant
- Wording feels more first-person and realistic
- Product still clear, not messy
- Trust boundary still visible
- No layout breakage or clutter

---

*See: Sprint Blueprint, Execution Outline*
