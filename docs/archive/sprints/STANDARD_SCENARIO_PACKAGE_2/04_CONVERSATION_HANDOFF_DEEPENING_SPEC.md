# Conversation / Handoff Deepening Spec

**Sprint:** Standard Scenario Package 2.0  
**Purpose:** Shared rules across the chosen package flows.

---

## 1. Later-Turn Behavior

| Rule | Meaning |
|------|---------|
| **Acknowledge before ask** | "好的，2024年的。" before "先把地址邮编发我" |
| **Answer clarification first** | When customer asks "garaging 是什么意思", explain garaging proof, then hand off |
| **Answer urgency first** | When "最要紧做什么", answer "等办公室确认付款是否到账", then hand off |
| **Use warmer handoff for already_sent** | "好的，收到了。办公室会尽快核实" instead of generic |
| **Use correction handoff for correction** | "好的，明白了。办公室会尽快处理" when customer corrects |

---

## 2. How to Confirm Naturally

- **Add-car:** "好的，[year] [model]，[zip]。报价资料已收集，办公室会尽快出价。"
- **Material:** "好的，收到了。办公室会尽快核实，有结果会联系您。"
- **Renewal:** "好的，账单收到了。办公室会尽快帮你看有没有能调整的地方。"
- **Payment:** "好的，收到了。办公室会尽快确认付款是否到账，今天会处理。"

---

## 3. How to Handle Corrections

- Detect: "不是", "不是这个", "说错了", "是另一辆"
- Reply: Use other_corrected phrase; if embedded urgency question, answer first
- Summary: Include "Customer corrected/clarified."

---

## 4. How to Handle "Already Sent"

- Detect: "发了", "发你", "sent", "截图", "发过了"
- Reply: Use other_received phrase ("好的，收到了")
- Summary: Include "Client says already sent" or "Collected: [item] resent"
- Broker_next_step: When client says sent, add "Verify receipt with carrier" or "核实是否收到"

---

## 5. Handoff Timing

| Category | Hand off when |
|----------|---------------|
| Add-car | (year+model OR VIN) + (zip OR delivery OR driver) |
| Material | Item(s) identified + sent status clear |
| Renewal | Policy or bill mentioned/sent |
| Payment | Notice, screenshot, or "I sent it" / "I paid" |
| Talk to Agent | Immediate on detection |

---

## 6. Summary Usefulness

- **Intent hint** first: "Add car", "Missing document", "Premium review", etc.
- **Collected** next: Concrete fields (year, model, zip) or items (dec page sent)
- **Still needed** when relevant: "garaging still needed", "verify receipt"
- **Context** when relevant: "Client says already sent", "Customer corrected"
- **Message count** + **Latest snippet**

---

## 7. Office Handoff Usefulness

- **broker_next_step:** One operational sentence; mention concrete item, deadline, or action
- **collected_fields:** Accurate chips (year, model, zip, dec_page_sent, etc.)
- **still_needed_fields:** What broker should ask or verify next
- **human_confirmation_required:** True when client says "sent" or "paid" (broker must verify)

---

*End of Conversation / Handoff Deepening Spec*
