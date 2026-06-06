# Add-Car Quote Excellence Blueprint

**Sprint:** Add-Car Quote Excellence  
**Created:** 2026-03-19  
**Purpose:** Make add-car the strongest, cleanest, most trial-worthy scenario in the product.

---

## 1. Why Add-Car Matters Now

Add-car / quote is one of the broker's most valuable and frequent workflows. If this single scenario becomes excellent, the product becomes much easier to:
- demonstrate to Chen Kui
- trial with a real broker
- justify commercially
- position as useful right away

The founder wants this scenario good enough that:
- the user feels guided naturally
- the broker receives a case with useful details
- the handoff is not too early
- the workbench next step is clear
- this can become one of the product's strongest selling points

---

## 2. Why This Is the Right Move Before Real Broker Trial

Before a real broker trial, add-car must be a "star scenario" the founder can confidently show. Current state is strong (handoff timing, HT8 fix, ask order) but gaps remain:
- broker summary could surface concrete vehicle details
- coverage-adjust side questions not explicitly handled
- add_car_rules config incomplete (ask_driver_only)
- no dedicated add-car excellence simulation pack

---

## 3. What This Sprint Will Strengthen

| Area | Target |
|------|--------|
| Ask-next quality | Clearer, more natural sequencing; no redundant asks |
| Correction handling | "不是X5，是X3" / "ZIP 改成 92620" — same case, updated fields |
| Late detail handling | "对了 是我老婆开" — captured before handoff |
| Garaging / doc clarification | Answer first, hand off (already fixed in HT8) |
| Mixed-intent inside add-car | "顺便问一下 coverage 可以调吗" — brief answer, hand off |
| Broker summary | Concrete vehicle (year, model) when available |
| broker_next_step | Actionable, quote-specific |
| Quote-readiness clarity | Collected vs still-needed explicit |

---

## 4. What This Sprint Intentionally Will NOT Do

- **No real carrier quote engine** — no premium calculation, no carrier integrations
- **No full insurance product modeling** — no coverage tiers, limits
- **No giant form systems** — keep conversational intake
- **No redesign of unrelated scenarios** — premium, payment, missing doc unchanged

---

## 5. Success Criteria

Add-car is "excellent enough for trial" when:
1. Ask-next feels natural and never redundant
2. Corrections stay in same case
3. Side questions (garaging, coverage) are answered before handoff
4. Broker sees concrete vehicle + zip + delivery/driver in summary
5. broker_next_step tells broker exactly what to do
6. Founder can demo 4–6 add-car flows confidently on Vercel

---

*See also: 02_FIELD_COLLECTION_SPEC.md, 03_HANDOFF_QUOTE_READINESS_SPEC.md*
