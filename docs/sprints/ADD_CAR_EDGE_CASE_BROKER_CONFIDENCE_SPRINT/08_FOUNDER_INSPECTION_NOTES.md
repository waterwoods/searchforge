# Founder Inspection Notes

## What to inspect after this sprint

1. **ACE02-style thread (UI or API):**  
   Message 1: `我想加车 2024 Toyota Camry 这个保费能便宜吗`  
   **Expect:** Reply collects zip/delivery/driver; **not** “send dec page and bill” renewal wording.

2. **ACE09-style thread:**  
   Single turn: `加车 2024 宝马X3 95123 明天提车 我开`  
   **Expect:** Handoff / quote-ready; summary or workbench shows **宝马 / X3** context, not blank vehicle.

3. **ACE04-style correction:**  
   Turn 1: `加车 2024 BMW X5 90210 下周提车`  
   Turn 2: `不是这辆 是另一辆 2024 X3 还是我开`  
   **Expect:** Summary mentions **correction**; vehicle line favors **X3** where extractor applies.

4. **ACE03 materials:**  
   After quote-ready, customer: `材料发你微信了`  
   **Expect:** Handoff copy acknowledges **sent materials** and verify, not a cold generic template.

5. **ACE08 dense bubble:**  
   One message with vehicle + zip + delivery + driver + extra questions  
   **Expect:** Handoff-ready case without forcing extra assistant turns.

6. **Append / follow-up (optional):**  
   Open a case, append a correction message  
   **Expect:** `triage_for_append` still marks handoff_pending (existing behavior).

## “Safe enough to show Chen Kui”

Means: **guardrail PASS**, no weak multi-turn regressions, and spot-checks 1–4 look **office-realistic** in the actual UI the broker will use—not only in JSON sims.
