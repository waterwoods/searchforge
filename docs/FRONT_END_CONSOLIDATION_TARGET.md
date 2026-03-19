# Front-End Naturalness + Progression Consolidation Target

**Sprint:** Front-End Naturalness + Progression Consolidation  
**Purpose:** Define what a more mature, unified Customer Entry experience should feel like across all 5 flows.

---

## 1. What "Unified Front Desk" Means

The Customer Entry should feel like **one coherent, capable office front desk**—not five separate flows that happen to share a UI.

| Dimension | Weak (uneven) | Strong (unified target) |
|-----------|---------------|-------------------------|
| **Tone** | Flow A warm, Flow B cold, Flow C templated | Same calm, operational, office-natural tone across all 5 |
| **Turn 1** | Some flows acknowledge, others jump to ask | Every flow: acknowledge what customer said (when detectable) → ask 1–2 next things |
| **Turn 2 / 3** | Add-car has ack; renewal/notice/missing-doc don't | All flows: brief ack of what customer just said before next ask or handoff |
| **Next-step style** | "把资料发我" vs "先把...发我，我就能帮你算" | Consistently: specific ask + why it matters ("发我，我就能...") |
| **Handoff** | Add-car warm; others generic | All flows: reflect what was achieved ("报价资料已整理" / "收到了" when sent) |
| **Issue progression** | Some flows feel like forms | Every turn moves the case forward; user feels heard |

---

## 2. Turn-by-Turn Consistency

### Turn 1
- **Acknowledge** when we can (vehicle, year, model, "发过了", "有办法吗")
- **Ask** 1–2 next things, not a checklist
- **Explain** why when useful ("发我，我就能帮你算报价"; "核对好后就能往下推")

### Turn 2
- **Acknowledge** what customer just said ("好的，2024年的。"; "好的，收到了。")
- **Ask** next missing field OR **hand off** when enough
- **Do not** repeat the same ask

### Turn 3 (add-car only when needed)
- Same pattern: ack → ask or handoff
- Max 2–3 customer turns before handoff

### Handoff
- **Add-car:** "您说的报价资料已整理好了，办公室会尽快出价"
- **Customer said sent:** "好的，收到了。办公室会尽快处理"
- **Customer corrected:** "好的，明白了。办公室会尽快处理"
- **Other:** "您说的情况已收到，办公室会尽快处理"

---

## 3. What Makes It Feel Like a Real Front Desk

1. **Understands what I'm trying to do** — Intent-specific reply, not generic "provide more context"
2. **Asks the right next thing** — 1–2 items, prioritized ("先把...发我")
3. **Explains just enough** — "我就能帮你算报价"; "核对好后就能往下推"
4. **Helps my issue move forward** — Each turn feels like progress
5. **Less form bot, more real front desk** — Acknowledgement, natural phrasing, handoff that reflects what was collected

---

## 4. What Remains Intentionally Human/Office-Handled

- Actual quoting, carrier lookup, payment processing
- Document verification, carrier confirmation
- Final broker review and send
- Complex multi-intent or ambiguous cases

---

## 5. Known Gaps (Pre-Sprint)

| Gap | Flow(s) | Priority |
|-----|---------|----------|
| Renewal/premium turn 2+ no acknowledgement | Renewal | Medium (handoff at T2 so rarely applies) |
| Notice/payment turn 2+ no acknowledgement | Notice | Low |
| Missing-doc turn 2+ no acknowledgement | Missing doc | Low |
| LC-AC3: handoff before driver correction | Add-car | Edge case |
| Remove-car: no acknowledgement vs add-car | Remove car | Medium — fix in Loop 1 |

---

## 6. Stage 2 First-Pass UX Test Results

**Clean user variants (2 per flow):** All 5 flows return intent-specific replies with acknowledgement (add-car), empathy (claim), reassurance (renewal 有办法), urgency (notice), progress phrase (missing doc).

**Messy user variants:** Add-car shorthand, renewal 有办法吗, claim 对方跑了, notice payment failed, missing doc 发过了 — all get tailored replies.

**Turn 2 handoff:** Renewal/payment/missing-doc when customer says "sent" → "好的，收到了。办公室会尽快处理" (warm). Add-car partial → "好的，2024年的。先把地址邮编发我" (ack + ask).

**Identified unevenness:** Remove-car goes straight to ask without "好的，可以处理。" — feels colder than add-car which has "好的，宝马X5。"

---

*End of consolidation target*
