# Add-Car Intake Mode Comparison Spec

Modes compared: **A Chat-only**, **B Form-first**, **C Hybrid**.

| Criterion | A — Chat-only | B — Form-first | C — Hybrid |
|-----------|----------------|----------------|------------|
| **Customer friction** | Lowest for “I just want to type”; higher if user doesn’t know what to list | Higher upfront; can feel like DMV | Medium: optional structure + escape to free text |
| **Speed of collection** | Slower if user is vague; faster if they dump everything in one message | Fast when fields are known | Fast when user uses short form; still flexible |
| **Completeness** | Depends on prompts and user literacy | High if form is enforced | High when structured card is used; chat fills gaps |
| **Broker usefulness** | Good if structured extraction is strong; bad if case looks “chatty” | Excellent scanability | Best: structured first pass + same extraction pipeline |
| **Commercial / office feel** | Risks “chatbot demo” | Risks “consumer app form” | Reads as **intake + office workflow** |
| **Implementation cost** | Already shipped (conversation + soft route) | New form-only product path + validation UX | **Low incremental:** compose message + existing triage |
| **Risk** | Repeated questions annoy customers | Abandonment if form feels long | Must not duplicate conflicting paths — one pipeline |

## Likely broker reaction (honest)

- **Chat-only:** “Interesting” if replies feel smart; “annoying” if customer forgets zip/driver.
- **Form-only:** “Clean data” if completed; “customers won’t fill it” in WeChat-style habits.
- **Hybrid:** “This matches how our clients actually text us” — quick facts + messy context.

## Decision for **current commercialization**

**Mode C — Hybrid wins now.**

**Why:** Smallest gap between **customer habit** (short unstructured messages) and **broker need** (year, model, zip, delivery, driver) without forking a second product. Implementation stays one triage pipeline; structured entry becomes **accelerator**, not a separate backend.

## Best later / defer

- **Later:** Deeper form validation (VIN format, ZIP regex), progressive disclosure by state rules, saved customer profiles.
- **Defer:** Full standalone form-only journey, multi-page wizards, CRM sync.
