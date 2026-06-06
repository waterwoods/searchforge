# Evaluation Criteria Spec

**Purpose:** Define how each conversation will be judged.

---

## 1. Classification Quality

- Correct `issue_category` for primary intent
- Correct `urgency` (critical/high/medium/low)
- `manual_followup_needed` matches broker expectation

---

## 2. First Useful Reply

- No generic "please provide more context" when intent is clear
- No "这段内容还不够完整" when add-car/premium/claim is obvious
- Draft asks for next concrete thing (year, zip, notice, screenshot)

---

## 3. Next-Best-Question Quality

- Asks 1–2 focused items, not 6 at once
- Uses customer language (zh when customer writes zh)

---

## 4. Later-Turn Realism

- Handoff at correct turn (2–3 for most flows)
- Add-car: hand off when year+model+zip+delivery present

---

## 5. Correction Handling

- Summary preserves "already sent", "corrected to X"
- broker_next_step reflects corrected context

---

## 6. Handoff Timing

- Not too early (missing critical field)
- Not too late (over-questioning)

---

## 7. Summary Usefulness

- conversation_summary actionable for broker
- Collected / still needed clear when applicable

---

## 8. Office Usefulness

- broker_next_step reads like work instruction
- client_reply_draft editable, not robotic

---

## 9. Trial-Readiness Impact

- Will this cause broker extra follow-up? → Higher priority
- Will this cause customer confusion? → Higher priority
- Will this cause trust loss? → Higher priority

---

*End of Criteria Spec*
