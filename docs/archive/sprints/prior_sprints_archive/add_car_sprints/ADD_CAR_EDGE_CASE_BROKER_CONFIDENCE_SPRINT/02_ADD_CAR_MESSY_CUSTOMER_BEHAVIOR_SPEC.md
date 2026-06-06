# Add-Car Messy Customer Behavior Spec

Patterns to assume **normal** in office-grade Add-Car triage (not edge exceptions).

## Topic jumping

- Customer sends **zip or address** before year/make, or asks **garaging / dec page** meaning in the middle of add-car.
- **Expectation:** Answer or acknowledge the side thread, then continue the **same** add-car slot order without re-classifying as renewal review.

## Partial information

- One field per message across several hours (simulated as consecutive turns).
- **Expectation:** Progressive asks; no premature handoff until quote-ready rule set is satisfied (unless explicit human request).

## Corrections

- “不是 X5 是 X3”, “不是这辆 是另一辆”, “说错了 我老婆开”.
- **Expectation:** `correction` follow-up type when appropriate; conversation summary notes correction; **latest** vehicle hint preferred when rules support it.

## Side questions

- “保费能便宜吗”, “大概多少钱”, “需要先买保险吗” embedded with slot-filled text.
- **Expectation:** Stay on add-car playbook; add **one short** office-realistic line where price worry appears; still collect missing slots.

## Hesitation

- “先不确定”, “可能下周提车” without a firm date.
- **Expectation:** Treat as delivery signal when markers match; still collect zip + driver where required.

## Materials sent

- “材料发你微信了”, “registration 发你了” after or during quote intake.
- **Expectation:** Warm handoff / verify tone; do not block handoff on artificial extra turns when quote-ready + sent markers present.

## Contact late

- Name/phone appear on turn 2 or 3 only.
- **Expectation:** Identity-contact-lite fields update; broker still sees still_needed if quote-ready without contact.

## Odd or mixed language

- Chinese vehicle descriptors (“宝马 X3”) mixed with English doc terms.
- **Expectation:** Vehicle line in summary should not drop make when extractors fire.
