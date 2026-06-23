# P16 Simplicity Stress Test

**Date:** 2026-06-19  
**Mission:** Attack the business rules. Find where complexity explodes. Keep the system simple.  
**North Star assumed correct:** "Whatever a Chinese insurance customer sends, turn it into a Broker Ready Request. Show readiness. Identify missing items. Generate follow-up. Help the broker complete the insurance action."  
**Method:** No code design. Business logic and decision rules only.  
**Sources:** P16_DECISION_FREEZE_V1.md, P16_CASE_SCENARIO_SIMULATION.md, P16_FINAL_NORTH_STAR_REVIEW.md, P16_BROKER_PAIN_RESEARCH.md, P16_TIMELINE_STATE_MACHINE_DESIGN.md

---

## STEP 1 — STRESS TEST THE REQUEST MODEL

### Current model

```
Customer → Request → People → Vehicle → Coverage
```

### Scenario survival test

---

**1. Add vehicle**

Does the model survive? **YES — perfect fit.**

Customer uploads purchase agreement. Extraction produces People (name, phone), Vehicle (VIN, YMM, garaging ZIP, lienholder), Coverage (effective date). All three buckets fill cleanly.

**Verdict:** This is what the model was built for. No complexity.

---

**2. Remove vehicle**

Does the model survive? **NO — structural break.**

Customer sends "我把车卖了" (I sold my car). No document to upload. No new VIN. No extraction to run.

The Request model expects an upload. Remove-car is a pure intent statement plus a policy lookup. There is nothing for the extraction pipeline to do. The broker needs the existing vehicle's VIN from AMS — not from a customer document.

**What breaks:** The (phone, VIN) case identity assumes a VIN arrives from an uploaded document. Remove-car has no VIN document. The model cannot anchor.

**Simplest fix:** Remove-car is a structured text form, not a document upload. Ask: "Which vehicle are you removing?" + "Approximate sale/removal date?" No extraction. No packet. A simple follow-up message generator is sufficient. Do not force it into the Request model.

**Complexity trap to avoid:** Don't build a parallel "remove car case" model with its own states. Keep it simple: it's a broker note, not a case.

---

**3. Replace vehicle**

Does the model survive? **PARTIAL — with a bolt-on.**

The new vehicle part fits perfectly (purchase agreement → VIN → packet). The old vehicle removal is a bolt-on: `related_vehicle = old VIN, pending_action = REMOVE_FROM_POLICY`.

The "bolt-on" is where complexity creeps. The related_vehicle JSONB field in `service_records.extra` is correct for V1. But it creates a two-step broker workflow that the current UI doesn't surface: (1) process new car add, (2) confirm old car removal. Step 2 is invisible in the current packet.

**What breaks:** The broker sees a complete packet for the new car but nothing prompts them to handle the removal. Silent risk.

**Simplest fix:** Add one line to the Trusted Packet: "⚠ Customer stated they are replacing their [old VIN]. Confirm removal separately." Nothing more. No second case. No automation. One warning line.

---

**4. Carrier switch**

Does the model survive? **PARTIAL — wrong input document type.**

The customer sends a declaration page, not a new car purchase agreement. The broker wants to extract all existing vehicles + drivers + coverage limits from the dec page and port everything to the new carrier.

The People and Vehicle buckets technically work. But the Coverage bucket is now about existing coverage being ported, not new coverage being assigned. The semantics are inverted: the dec page describes what already exists, not what is being requested.

**What breaks:** The add-car packet assumes "new vehicle, new coverage." Carrier switch assumes "existing coverage, new carrier." The field schema diverges significantly: carrier switch needs `current_carrier`, `all_vehicles[]`, `all_drivers[]`, `current_limits`, `current_deductibles`, `current_premium`. Add-car needs `new_vin`, `new_vehicle_ymm`, `lienholder`, `garaging_zip`.

**Simplest fix:** Carrier switch is a different schema on the same extraction pipeline. Same upload → Gemini → packet flow. Different field contract. This is N2 (declaration page extraction), not an extension of the add-car model. Do not force carrier switch into the add-car Request model.

**Complexity trap to avoid:** A "universal request model" that tries to handle both add-car and carrier switch in the same schema will produce a bloated, field-sparse packet for each. Keep schemas separate. Same pipeline, different field contracts.

---

**5. Renewal**

Does the model survive? **NO — wrong trigger type.**

Renewal is a time-triggered event, not a customer-submitted request. The customer doesn't initiate it by uploading documents — the carrier sends a renewal notice. The broker must proactively reach out.

The Request model assumes customer sends something. Renewal often starts from the broker side. Even when the customer triggers it ("why did my rate go up?"), the input is a renewal notice PDF that looks like a dec page, not a new vehicle document.

**What breaks:** The entire customer → upload → extract flow is backwards for renewal. Renewal requires broker to pull the current dec page, compare to competing rates, then present options. It's broker-initiated research, not customer-submitted intake.

**Simplest fix:** Renewal = dec page upload to the same extraction pipeline (N2). Same infrastructure, broker-initiated flow. Do not model renewal as a customer Request. Model it as a broker-triggered document processing job.

---

**6. Add driver**

Does the model survive? **PARTIAL — People bucket works, but anchor breaks.**

The customer uploads a driver license photo. The People bucket should capture name, DL number, DOB. The Vehicle bucket needs to know which vehicle this driver will be assigned to — but the customer isn't uploading vehicle documents. The anchor is now a person (DL), not a vehicle (VIN).

**What breaks:** The (phone, VIN) case identity doesn't apply. An add-driver request is about a person being added to an existing vehicle already on the policy. The VIN comes from the broker's existing policy records, not from the customer upload.

**Simplest fix:** Add-driver is (phone, DL_number) identity, not (phone, VIN). The case anchor is the driver license. The broker assigns the driver to a vehicle manually using their AMS. Do not try to auto-match the driver to a vehicle.

---

**7. Remove driver**

Does the model survive? **NO — same problem as remove vehicle.**

Just a WeChat message: "我的女儿搬走了，她不开我的车了" (My daughter moved away, she doesn't drive my car anymore). No document. No extraction.

**Simplest fix:** Text form only. "Which driver are you removing?" Broker note. Not a case. Not a packet.

---

**8. Teen driver**

Does the model survive? **PARTIAL.**

Teen driver license photo → People bucket captures DL data. But the critical data (driver's ed completion, good student discount eligibility, which vehicle to assign) doesn't come from the license. It comes from a checklist the broker runs through verbally with the parent.

**What breaks:** The parent's anxiety about the premium increase is the #1 issue — and it's entirely outside the document extraction model. The Follow-Up message (N1) helps: it can list exactly what the broker needs (driver's ed cert, GPA, vehicle assignment). But the emotional conversation with the Chinese-speaking parent is irreducible human work.

**Simplest fix:** Teen driver = DL extraction (N3) + structured checklist follow-up in Chinese. No special case model needed.

---

**9. Address change**

Does the model survive? **NO — no document, no extraction.**

Customer says "我搬了" (I moved). No document. No VIN. The broker needs the new garaging ZIP for each vehicle on the policy.

**What breaks:** Nothing to extract. The model has no content to process. The complexity here is that garaging ZIP change must be applied to all vehicles on the policy, not just one — and the broker's AMS has the vehicle list, not P16.

**Simplest fix:** Structured text form only. "What is your new garaging address?" → broker updates each vehicle in AMS. P16 generates a Chinese follow-up message if the customer didn't provide the exact ZIP. That's the entire product contribution here.

---

**10. Coverage change**

Does the model survive? **NO — preference statement, not document.**

"我想降低免赔额" (I want to lower my deductible). No document. No extraction. The broker needs to know which vehicle, which coverage, current limits, desired new limits, effective date.

**What breaks:** Nothing to extract. Pure broker-guided conversation. P16's follow-up generator can help (generate the structured ask for which vehicle and what new deductible), but there's no packet to build.

---

**11. Payment update**

Does the model survive? **NO — hard no forever.**

PCI scope. Never build. This is explicitly frozen in Decision Freeze §4. Do not revisit.

---

**12. Wrong submission**

Does the model survive? **YES — with VIN_CONFLICT_FLAGGED.**

Customer submits wrong insurance card. System detects that the only VIN-bearing document is an existing insurance card. Case state → MISSING_ITEMS with `new_vehicle_document_required`. Chinese follow-up asks for the purchase agreement. When the correct document arrives, same case, append, update current truth.

**What breaks:** If the broker already started working from the wrong VIN packet, the correction is retroactive. The "has been acted on" flag is missing from the current model.

---

**13. Customer changes mind**

Does the model survive? **PARTIAL — needs a CANCELLED state.**

Customer says "never mind, I'm not buying that car." The existing case has READY_FOR_QUOTE on VIN_A. The case can be closed. But if a new upload arrives later for VIN_B from the same phone, the system will find no active case (VIN_A is closed), create a new case for VIN_B, and that's correct.

**What breaks:** There's no explicit CANCELLED state. Broker must manually close the case. The current state machine goes READY_FOR_QUOTE → CLOSED, which is the correct path. But "customer changed mind" and "broker completed quote" look identical from the outside. This matters for time-savings tracking (a changed-mind case shouldn't count toward the time-savings average).

**Simplest fix:** Add a `closed_reason` field to CLOSED state. Values: `quote_completed`, `customer_cancelled`, `duplicate`. One field, no new states.

---

**14. Customer submits conflicting information**

Does the model survive? **YES — VIN_CONFLICT_FLAGGED handles it.**

If the customer sends two documents with different VINs, the conflict is flagged, the broker resolves it, and the current truth is updated. This is the most thoroughly designed scenario in the current model.

---

### Request Model Survival Summary

| Scenario | Survives? | Risk Level |
|----------|-----------|------------|
| Add vehicle | ✅ Full | None |
| Remove vehicle | ❌ Breaks | HIGH — no document to extract |
| Replace vehicle | ⚠️ Partial | MEDIUM — removal step is invisible |
| Carrier switch | ⚠️ Partial | HIGH — wrong schema; needs N2 |
| Renewal | ❌ Breaks | HIGH — wrong trigger type |
| Add driver | ⚠️ Partial | MEDIUM — wrong case anchor |
| Remove driver | ❌ Breaks | LOW — rare, simple text form |
| Teen driver | ⚠️ Partial | LOW — DL + follow-up sufficient |
| Address change | ❌ Breaks | MEDIUM — no document to extract |
| Coverage change | ❌ Breaks | LOW — rare, pure conversation |
| Payment update | ❌ Hard No | NONE — frozen; never build |
| Wrong submission | ✅ Full | None |
| Customer changes mind | ⚠️ Partial | LOW — missing closed_reason |
| Conflicting information | ✅ Full | None |

**Key finding: The Request model survives perfectly for document-submission scenarios (add car, wrong submission, conflicting info). It breaks entirely for intent-only scenarios (remove car, address change, coverage change). These are fundamentally different problem types and should not share a model.**

---

## STEP 2 — REQUEST vs. CASE vs. TASK vs. ACTIVITY STREAM

### Option A: Request

**Mental model:** Customer submits a request. System processes it. Broker receives it.

**Broker mental match:** Moderate. Brokers say "I have a request from Mrs. Chen" but they don't think of requests as objects they manage.

**Customer mental match:** Strong. "I'm requesting to add my car" is natural.

**Simplicity:** High. A request has a clear start (submission) and end (broker action).

**Future complexity:** Medium. "Request" has no natural lifecycle. When is a request open vs. closed? When does a request become stale? The word doesn't carry state semantics.

**Verdict:** Right word for customer-facing language. Wrong internal model for broker workflow.

---

### Option B: Case

**Mental model:** A unit of work that gets opened, worked, and closed. Has a state. Can have attachments. Can be ongoing.

**Broker mental match:** Very strong. Insurance brokers say "I have a case for a new car." They mentally manage a queue of cases. Case is their native vocabulary.

**Customer mental match:** Low. Customers don't think in cases. They send documents and wait.

**Simplicity:** High for internal model. Cases have natural lifecycle states (open, pending, closed). Natural for a team to work a queue of cases.

**Future complexity:** Low. Case semantics are well-understood. Adding features to a case (timeline, attachments, notes) is natural. Extending a case to handle multiple scenario types is straightforward.

**Verdict:** Best internal model. Matches broker mental model exactly. Use "case" internally and in broker-facing UI.

---

### Option C: Task

**Mental model:** A unit of work assigned to a person to complete by a deadline.

**Broker mental match:** Poor. Tasks imply assignment, deadlines, and completion checklists. This is CRM/project management territory. Wu Xiaojie doesn't think "I have 15 tasks today." She thinks "I have cases to work."

**Customer mental match:** None. The customer never sees tasks.

**Simplicity:** Low. Tasks require assignment logic, priority rules, due dates — none of which P16 has or should have.

**Future complexity:** High. Task management is a product category (Asana, Monday, ClickUp). Building it invites comparison and scope expansion into areas that are explicitly frozen.

**Verdict:** Wrong model. Erases competitive moat. Sounds like EZLynx. Do not use.

---

### Option D: Activity Stream

**Mental model:** A continuous feed of events. No clear unit. No natural open/close state.

**Broker mental match:** Poor. Brokers don't manage feeds. They manage cases.

**Customer mental match:** Low to none.

**Simplicity:** Low as a top-level model. High as a component of a case. An activity stream is the Timeline inside a Case, not the Case itself.

**Future complexity:** High if used as top-level model. A feed with no unit of work leads to broker confusion about what's done vs. pending.

**Verdict:** Right design for the Timeline panel inside a Case. Wrong top-level model.

---

### Verdict: The Two-Word Answer

**Customer submits a Request. The system creates a Case. The broker works the Case.**

These are not competing models. They are the same flow with different vocabulary at each stage:

```
Customer language:    Request
System language:      Case  
Broker language:      Case
Timeline/log:         Activity Stream (inside the Case)
```

Never say "task" to a broker. Never say "case" to a customer. Never use "activity stream" as the top-level concept.

**REQUEST_VS_CASE_VERDICT: Case is the correct internal model. Request is the correct customer-facing word. They describe the same object at different stages of the same flow.**

---

## STEP 3 — READINESS MODEL

### Current concept

People, Vehicle, Coverage → Readiness %

### Challenge: Are the three buckets right?

**People** — captures: name, phone, primary driver, additional drivers.
**Vehicle** — captures: VIN, year, make, model.
**Coverage** — captures: effective date, lienholder, coverage limits.

**Problem 1: Garaging ZIP is in the wrong bucket.**

Garaging ZIP is the single most critical rating field for an add-car case. It determines the premium. It is required for the carrier portal. But it's neither a People field nor a Vehicle field — it's a property of where the vehicle lives. In the current model, garaging ZIP is implicitly in the intake form (collected before upload) and appears on the packet but isn't bucketed anywhere.

If garaging ZIP goes into "Vehicle," the bucket becomes: VIN, YMM, garaging ZIP. That's more accurate — the vehicle's location is part of its identity for rating purposes.

**Problem 2: Coverage is almost always empty.**

For add-car cases, "Coverage" means: effective date, lienholder (if financed), and coverage limits. But coverage limits are chosen by the broker, not extracted from customer documents. What the customer actually provides is lienholder (from the purchase agreement) and delivery date (also from the purchase agreement). Coverage limits are a broker decision.

The Coverage bucket is more accurately named "Finance & Timing": lienholder, delivery date, effective date. This is what matters for the intake packet.

**Problem 3: The % is misleading.**

A 67% readiness score (2 of 3 buckets complete) is meaningless if the missing bucket is "Vehicle" (can't quote without VIN) vs. "Coverage" (can quote without lienholder). Not all missing fields are equal.

**The simplest readiness model:**

Don't use buckets. Don't use percentages. Use a binary required-fields checklist:

```
Required to quote:
  ✅ VIN
  ✅ Year, Make, Model
  ✅ Garaging ZIP
  ⚠️ Primary Driver (defaulted — confirm)
  ❌ Lienholder (missing — ask if financed)
  
Status: Ready to quote. Confirm primary driver. Ask about lienholder if the car is financed.
```

This is more honest, more actionable, and requires no math. The broker sees exactly what's there, what needs confirmation, and what's missing. No percentage obscures the severity.

**Should Address, Payment, Documents, Policy be separate buckets?**

- **Address:** Garaging ZIP belongs in the required fields checklist, not a separate bucket.
- **Payment:** Hard no. PCI. Never touch.
- **Documents:** Source attribution (which file each field came from) is the right design, not a separate readiness bucket. "From: purchase_agreement.pdf" next to each field IS the document tracking.
- **Policy:** Policy management is AMS territory. P16 sees no policy data. Do not try to track this.

**BEST_READINESS_MODEL: Required fields binary checklist, not People/Vehicle/Coverage % buckets. Five required fields: VIN, Year/Make/Model, Garaging ZIP, Primary Driver, and (optional flag if financed) Lienholder. Each field is ✅ confirmed, ⚠️ needs confirmation, or ❌ missing. No percentage. Show exact status, not an abstracted score.**

---

## STEP 4 — CHANGE AND CORRECTION SCENARIOS

### Customer enters wrong VIN

**What should happen:**

System has VIN_A on the case. Customer uploads new document with VIN_B. Two sub-cases:

1. VIN_B is clearly from a purchase agreement (higher document priority) → VIN_CONFLICT_FLAGGED → broker sees both → broker resolves → current truth updates to VIN_B.
2. VIN_B is from another insurance card (lower priority) → old insurance card rule applies → VIN_A stays anchored → broker sees warning.

**Risk:** If the broker already copied VIN_A and submitted it to the carrier, the correction is retroactive. The system currently has no "has been acted on" flag.

**Simplest fix without complexity:** Add `copied_at: timestamp` to the case when the broker hits "Copy All." This single timestamp tells the system: "the broker has extracted data from this case." Any subsequent VIN change after `copied_at` should trigger a prominent warning: "VIN changed after packet was copied — re-copy updated packet."

---

### Customer uploads wrong insurance card

**What should happen:**

Detected via MISSING_ITEMS + `new_vehicle_document_required` state. System flags: "Only an existing insurance card was found. Please upload the purchase agreement or new registration." Customer uploads correct doc. System re-runs extraction. Current truth updates to the new VIN. Old insurance card's data is preserved in history as a prior event.

**No complexity needed.** The append-to-case model handles this exactly. Same phone + same session → append new doc → re-extract → update current truth.

---

### Customer changes vehicle

**What should happen:**

Customer had a Tesla case (VIN_TESLA) in READY_FOR_QUOTE. Customer calls back: "actually I bought a Honda instead." New upload with VIN_HONDA arrives.

System finds existing case (VIN_TESLA) for that phone. New upload has a different VIN. Decision: create new case (VIN_HONDA) per SB-3 logic — but this isn't two new cars simultaneously, it's a correction.

**The complexity trap:** Is this a new case or a correction to the existing case? The (phone, VIN) identity rule says different VIN = new case. But the broker's mental model is "same customer, same request, different vehicle." The broker doesn't want two cases for the same request.

**Simplest resolution:** Ask the broker. The system surfaces: "A different VIN was detected for the same customer. Is this a new vehicle addition, or a correction to the previous case?" Broker clicks one button. No automatic decision. This is the correct behavior for V1 — when the system can't determine intent from documents alone, ask the human.

---

### Customer changes address

**What should happen:**

Customer sends new garaging ZIP after the case is READY_FOR_QUOTE. System just updates the garaging ZIP on the case. No new case. No conflict. The ZIP is a mutable field, not a case anchor.

**No complexity needed.** ZIP updates don't change case identity.

---

### Customer uploads better documents later

**What should happen:**

Same phone + same VIN → append to existing case. New documents run through extraction. Fields that were previously missing may now be present. Fields that already had values are not overwritten (they are confirmed by the second document). If the second document has a different VIN → VIN_CONFLICT_FLAGGED → broker resolves.

**Critical rule:** Never silently overwrite a confirmed field. A confirmed VIN stays confirmed until the broker explicitly resolves a conflict.

---

### Customer returns 3 days later

**What should happen:**

Same phone + same VIN → same case. Timeline shows the 3-day gap as a "time elapsed" note. No new case. No new extraction. Just append the new document.

**Edge:** If the broker already closed the case (CLOSED state), the 3-day-later submission creates a new case. The old closed case is preserved in history. This is correct: a closed case means the broker completed the work. If the customer comes back with more documents after closing, it's a new intake.

**Simplest fix without complexity:** The closed-case rule is already in the codebase as a guardrail. No new logic needed.

---

### Customer returns 3 months later

**What should happen:**

At 3 months, the broker has long since closed the case. The customer is likely adding a new car (not the same one). Create a new case. The old case is archived but findable by phone lookup.

**Potential complexity:** If the same customer returns every 3 months to add a new car (common for multi-vehicle households), they accumulate cases. The broker needs a "customer history" view — all cases for phone 626-555-0000. This is the broker queue feature that is currently missing from V1.

**Simplest fix without full CRM:** A `/broker/cases?phone=6265550000` endpoint that returns all cases (open and closed) for a phone number, sorted by date. One endpoint, one list. Not a full dashboard. Just: "Here's what we've done for this customer." Build this before the 5-broker mark.

---

## STEP 5 — CURRENT TRUTH MODEL

### The concept

All submissions are stored. The system shows Current Truth to the broker.

```
Submission 1: VIN_A (from insurance card)
Submission 2: VIN_B (from purchase agreement)

Current Truth: VIN_B
History: VIN_A preserved in timeline
```

### Is this the correct model?

**Yes, with four qualifications.**

**Qualification 1: Document priority must be reliable.**

Current Truth is only trustworthy if the system reliably identifies which document type takes priority when VINs conflict. The hierarchy is `purchase_agreement > new_registration > VIN_photo > insurance_card > title`. This logic is specified in P16_CASE_SCENARIO_SIMULATION.md but not yet consistently implemented.

If the system picks the wrong VIN as "Current Truth" even once, broker trust collapses. The document priority logic is the highest-risk single component in the current system. It must be tested with real documents before the 5-broker mark.

**Qualification 2: "Has been acted on" is missing.**

When the broker copies the packet and submits to the carrier, the Current Truth is no longer just a data state — it's a real-world action. If the customer subsequently corrects a VIN, the broker must know that the old VIN was already submitted. Without a `copied_at` timestamp or `submitted_to_carrier` flag, the system cannot distinguish "the broker hasn't used this data yet" from "the broker already submitted this data."

**Qualification 3: Multiple corrections need a visible correction count.**

VIN_A → VIN_B is acceptable. VIN_A → VIN_B → VIN_C is a signal that something is structurally wrong (customer doesn't have the right documents, or system is picking wrong VINs). The broker should see: "This VIN has been corrected 2 times." Not buried in the timeline. Visible in the packet header. This prevents the broker from confidently using a VIN that has a correction history.

**Qualification 4: Closed cases must not accept Current Truth updates.**

A CLOSED case is terminal. If a new document arrives for a phone+VIN that matches a closed case, do not update the closed case. Create a new case. The Current Truth model applies only to OPEN cases.

### Edge cases that break the Current Truth model

**Edge 1: Two customers, same VIN**

Unlikely but possible: two different phones upload documents for the same VIN (e.g., dealer sells same car twice by mistake). The (phone, VIN) identity prevents this from creating a single case — they become two separate cases for the same VIN. Broker sees both. Correct behavior: flag it, let the broker sort it out with the dealer.

**Edge 2: VIN correction after carrier submission**

Broker submitted VIN_A to Mercury. Customer then uploads a document proving the correct VIN is VIN_B. The insurance policy is now written on the wrong VIN. P16 cannot correct this — it requires a carrier endorsement. The system should display: "This VIN was corrected after the initial packet was copied. If the carrier was already contacted with the previous VIN, an endorsement may be required."

**Edge 3: Current Truth disagrees with AMS**

The broker's AMS shows VIN_C (from a previous case that predates P16). P16 shows VIN_B as Current Truth. The broker is confused. P16 has no visibility into what's in the AMS. No fix possible without AMS integration (out of scope). The mitigation: source attribution ("from: purchase_agreement.pdf") gives the broker confidence in P16's version, not the AMS version.

**CURRENT_TRUTH_VERDICT: Correct model. Implement it. Add (1) `copied_at` timestamp when broker copies the packet, (2) visible correction count when VIN changes more than once, (3) hard rule that CLOSED cases don't accept Current Truth updates. The document priority logic is the highest-risk component — test it with 5 real document sets before the 5-broker mark.**

---

## STEP 6 — ZIP2 TEST

### The question: What would Elon / Craigslist / Zip2 remove, keep, and refuse to build?

---

### REMOVE (immediately, no discussion)

**1. The Timeline UI panel in the PacketStep.**

The Timeline (collapsed Ant Design `<Timeline>` behind a `<Collapse>`) is engineering work that produces zero broker action. Wu Xiaojie does not care that the system fired `AI_EXTRACTED_PACKET` at 9:06 AM. She cares that she can copy the packet. The Timeline is a developer-comfort feature, not a broker-productivity feature.

Remove it from the pilot. If brokers ask "what happened with this case?" — that's the signal to build it. Don't build it before they ask.

**2. The `related_vehicles` JSONB array.**

For V1 pilot, the replace-car scenario (new VIN + old VIN related) is handled by a one-line warning in the packet: "Customer stated they are replacing their BMW. Confirm removal separately." That one line is the entire product contribution. The JSONB metadata array with `relationship`, `pending_action`, `broker_confirmed` is data infrastructure with no UI surface. It serves no broker-visible function in V1.

Remove it from V1. Add it in V2 if brokers are confused about what to do with the old car.

**3. The document anchor priority hierarchy (as a system rule).**

`purchase_agreement > new_registration > VIN_photo > insurance_card > title` is a five-level hierarchy. For V1, simplify to a two-level rule: **"If two VINs are found in the same upload, flag both and ask the broker which one is the new vehicle."** No automatic anchor. No document type detection. Broker resolves all conflicts manually.

This removes the risk that the automatic anchor picks the wrong VIN silently. It increases broker touches slightly but eliminates a catastrophic silent failure mode.

Re-introduce automatic anchor priority in V2 once you've seen 50+ real document sets and know which document types actually appear in this brokerage.

**4. `MISSING_VIN` as a formal case state.**

The full `MISSING_VIN` sub-state with its own state machine transition (`MISSING_VIN → (VIN arrives) → DOCS_UPLOADED → PACKET_BUILT → READY_FOR_QUOTE`) is complexity. For V1: if VIN is missing, the case is MISSING_ITEMS. Period. No sub-state. The customer gets a follow-up message asking for their purchase agreement. When they re-upload, the case re-extracts. If VIN is found, it's READY_FOR_QUOTE. The broker doesn't need to know about the MISSING_VIN intermediate state.

**5. The three sub-rules (SB-1, SB-2, SB-3) as formal rules in the system.**

These rules are correct business logic. They should be documented (and are, in P16_CASE_SCENARIO_SIMULATION.md). But they should NOT be implemented as code branches in V1. For the Chen Kui pilot with 10–50 cases:
- SB-1 (anchor priority): Replace with "flag both VINs, ask broker."
- SB-2 (replace = one case + related vehicle): Replace with "one line warning, broker handles removal manually."
- SB-3 (two new cars = two cases): Acceptable fallback: system flags "second vehicle detected," broker creates second case manually.

All three sub-rules exist to automate what the broker can do manually in 30 seconds. At 10 cases, the automation provides zero time savings relative to its implementation cost.

---

### KEEP (non-negotiable, remove nothing)

**1. Upload → Extract → Packet (the core loop).**

This is the entire product. It cannot be simplified further. Every simplification outside this loop serves this loop.

**2. VIN validation (format check + warning).**

A wrong VIN in a submitted packet is a liability event. This is not optional complexity. It is the minimum trust layer the product provides.

**3. Source attribution ("from: purchase_agreement.pdf").**

This is the trust mechanism. Without it, the broker cannot verify any field. Source attribution is what separates P16 from "a random AI guess." It is the product's proof of integrity. Never remove it.

**4. Copy Fields (one-click clipboard copy).**

This is the moment of broker value: VIN appears in clipboard, pastes into carrier portal, no typing. Remove Copy Fields and you've removed the productivity gain. The rest of the product exists to make Copy Fields work correctly.

**5. Missing items detection with the exact missing field names.**

"Primary Driver: MISSING" + "Lienholder: MISSING" is more valuable than any readiness percentage. The broker knows exactly what to ask for. This is the cheapest follow-up automation that exists.

**6. Chinese bilingual follow-up message (N1) — once built.**

This is the single highest-ROI feature outside the core loop. It affects 70–80% of all cases. It eliminates the most repetitive manual task Wu Xiaojie does. Keep it. Build it now.

---

### REFUSE TO BUILD (ever, regardless of broker request)

**1. WeChat bot / native integration.** Paste-link achieves the same outcome without WeChat API compliance complexity. Refuse permanently.

**2. Carrier quote integration.** Regulated, expensive, 6-month project. Solves the quoting step, not the intake step. The intake step is P16's product.

**3. Customer-facing portal.** The customer hired a human broker, not a SaaS product. The customer's experience is correctly invisible. Building a customer portal means competing with the broker-customer relationship that is the entire basis of trust in this market.

**4. PDF generation.** Broker copies fields. A generated PDF adds legal liability without proportional value. If brokers ask for this, ask why they need a PDF instead of Copy Fields. The answer is almost always "because our AMS requires it" — which means AMS integration is the real request, not PDF generation.

**5. Any feature requiring PCI compliance.** Payment card handling is a compliance category, not a feature. Never.

---

## STEP 7 — FIRST 5 BROKER TEST

### Setup: 5 brokers × 100 cases/month = 500 cases/month

---

### WHAT SURVIVES AT SCALE

**Upload → Extract → Packet.** Survives at 500 cases. The pipeline is stateless per case. Each extraction runs independently. No shared state. No coordination overhead.

**VIN validation.** Survives at 500 cases. Fast, cheap, always needed.

**Source attribution.** Survives at 500 cases. No performance concern. Brokers will use it every time.

**Copy Fields.** Survives at 500 cases. It's a clipboard copy. Zero infrastructure.

**Chinese follow-up message (N1).** Survives at 500 cases. LLM call per missing-item packet. Cost is minimal at 500 cases.

---

### WHAT BECOMES PAINFUL AT SCALE

**1. No broker queue view.**

At 10 cases, Wu Xiaojie can remember all open cases. At 100 cases/month, she cannot. She needs a list: open cases, sorted by date, showing customer name + VIN + status. Without this, she must log into the system for each case separately after receiving the intake link. At 100 cases, this is chaos.

**The simplest broker queue:** A read-only list at `/broker/cases` showing all non-closed cases for one broker account. No authentication system required for V1 — use the same broker API key that's already scoped per broker. This is the single most important missing feature for scaling beyond 1 broker.

**2. (phone, VIN) identity collision at phone reuse.**

At 500 cases, there's a non-trivial chance that a phone number is recycled by a carrier and assigned to a new customer. The (phone, VIN) rule creates a false match: new customer submits a document, system finds old customer's case (same phone, same VIN in theory — very unlikely but possible), and appends to the wrong case.

At 10 cases: risk is near zero. At 500 cases: not zero. The simplest mitigation: add a 90-day case expiry. Cases older than 90 days don't accept appends — new submission creates a new case. This covers 99% of the phone-reuse risk without complex customer identity management.

**3. VIN conflict resolution burden at scale.**

For Chen Kui's 10-case pilot, every VIN conflict is a learning experience. For 500 cases/month, if 1 in 4 cases has a VIN conflict, that's 125 conflicts per month requiring broker attention. If each conflict takes 2 minutes to resolve, that's 250 minutes per month — 4+ hours of broker attention just on conflicts.

At this scale, the document anchor priority logic (purchase_agreement wins over insurance_card) becomes a time-saver, not just a nice-to-have. The V1 simplification (flag everything, broker resolves all conflicts) works for 10 cases. It becomes a bottleneck at 500 cases.

**Simplest path:** Run 10-case pilot with "flag everything." After 10 cases, audit: how many conflicts were ambiguous? How many were clear-cut (purchase agreement + insurance card together)? The answer determines when to implement automatic anchor priority.

**4. Case deduplication across brokers.**

At 5 brokers, two brokers might have the same customer (same phone) if a customer shops around. The current model creates separate cases in separate broker contexts. This is correct — cases are broker-scoped. But if both brokers call their extraction endpoint with the same phone, both create cases. There's no cross-broker deduplication, nor should there be (brokers don't share customer data).

This is not a complexity problem; it's a business reality. Just document it.

**5. Missing item follow-up tracking.**

At 500 cases/month, the broker sends a follow-up message to the customer. The customer replies 3 days later. The broker needs to find the original case. Currently: no link between the follow-up WeChat message and the P16 case. The broker must manually find the case.

This is a workflow gap that becomes painful at 100+ cases/month. The fix: include the case URL in the generated follow-up message. "To continue, re-upload at: [link with phone pre-filled]." This closes the loop without building any tracking infrastructure.

---

### WHAT SHOULD BE SIMPLIFIED NOW (before 5 brokers)

**1. Remove Timeline from PacketStep UI.**
The Timeline panel adds ~3 seconds of cognitive load to the broker's first view of the packet. The broker wants: packet fields → copy button → done. Timeline is secondary information. Move it to a separate "Case History" link. Build the history view only if brokers click the link more than 3 times in 10 cases.

**2. Add `closed_reason` to the CLOSED state (5-minute fix).**
`quote_completed` vs. `customer_cancelled` vs. `duplicate`. Three values. One field. This makes the time-savings tracker accurate and prevents inflated averages from cancelled cases.

**3. Build a minimal broker queue before the 3rd broker.**
One endpoint, one list view. Open cases, sorted newest-first, customer name + VIN + status + age. No filtering, no search, no pagination in V1. Just the list. Without this, the second broker cannot manage their incoming cases.

**4. Include the case re-upload URL in the follow-up message.**
"Please re-upload your documents here: [link]" eliminates the return-customer confusion at scale. This is a 10-minute change with significant scale impact.

**5. Implement 90-day case expiry.**
Closes the phone-reuse risk and also prevents old cases from cluttering the broker queue indefinitely.

---

## STEP 8 — FINAL RECOMMENDATION

---

### REQUEST_MODEL_SCORE: 7 / 10

Strong for document-submission scenarios (add car, carrier switch with N2, renewal with N2). Breaks for intent-only scenarios (remove car, address change, coverage change). The model is correctly scoped for P16's wedge. Do not force it to handle non-document scenarios.

---

### TOP_5_COMPLEXITY_TRAPS

**Trap 1: Document anchor priority as automatic system logic (HIGHEST RISK)**

The hierarchy `purchase_agreement > new_registration > VIN_photo > insurance_card > title` is specified but untested against real document variety in this brokerage. If the system automatically picks the wrong VIN anchor, it silently produces a packet with the wrong vehicle. At 10 cases, a single silent wrong VIN is a trust-destroying event. For V1: flag all conflicts. Broker resolves manually. Implement automatic anchor priority only after auditing 25+ real conflict cases.

**Trap 2: Extending the add-car model to cover carrier switch and renewal (HIGH RISK)**

Carrier switch and renewal require a declaration page extraction schema that is fundamentally different from the add-car schema. Trying to unify these into one "universal intake model" produces a field-sparse, confusing packet for both scenarios. Keep schemas separate. Same pipeline infrastructure, different field contracts. N2 is not an extension of add-car; it is a new document type.

**Trap 3: Building Timeline before building the broker queue (MEDIUM RISK)**

The Timeline (case activity log) is internal developer-comfort data presented as a broker feature. The broker queue (list of open cases) is an actual broker workflow tool. Building Timeline first — which is the current plan — inverts the priority. At 3 brokers, no timeline is needed. A queue is urgently needed.

**Trap 4: Infinite append on closed cases (MEDIUM RISK)**

If closed cases accept appends, a customer returning after 3 months will accidentally re-open old cases and confuse the broker. The 90-day expiry rule + "closed cases don't accept appends" guardrail must be strictly enforced. The guardrail already exists in `case_store.py` — do not weaken it.

**Trap 5: The readiness percentage abstraction (LOW-MEDIUM RISK)**

A readiness percentage (67%, 100%) is a simplification that destroys information. A 67% score with VIN missing is catastrophically different from a 67% score with lienholder missing. Brokers need to see exactly what's missing, not a score. The binary checklist (✅ / ⚠️ / ❌ per field) is more honest and more actionable. Never introduce a readiness percentage.

---

### TOP_5_SIMPLIFICATIONS

**Simplification 1: Replace all VIN conflicts with "broker resolves" for V1.**

Instead of automatic document anchor priority, flag all multi-VIN cases with a simple warning: "Multiple VINs detected. Primary VIN shown. Please verify." Broker confirms or corrects. Implement automatic anchor priority only after 25+ real conflict cases show a clear pattern.

**Simplification 2: Replace the `related_vehicles` JSONB structure with one warning line.**

"Customer stated they are replacing their [VIN]. Confirm removal separately." One line. One sentence. No metadata structure. No pending_action. No broker_confirmed flag. If the broker needs more guidance, they'll ask. Add the JSONB structure in V2 when it's justified by a specific broker request.

**Simplification 3: Replace MISSING_VIN sub-state with MISSING_ITEMS.**

If VIN is not found, the case is MISSING_ITEMS. That's all the broker needs to know. The specific field that's missing is visible in the missing items list. The sub-state machinery (`MISSING_VIN → VIN_arrives → transition`) is premature optimization for a scenario (no-VIN submission) that should be rare if the intake form guides the customer correctly.

**Simplification 4: Include the case URL in every follow-up message.**

One URL. "Re-upload here: [link with phone pre-filled]." Eliminates the return-customer workflow problem without any additional infrastructure. This turns the follow-up message into a complete workflow loop.

**Simplification 5: Defer Timeline to "broker asks for it."**

Remove the Timeline panel from the PacketStep. Move it to a "View Case History" link that opens a simple separate view. Track whether any broker clicks it in the first 30 cases. If no broker clicks it: confirm the Timeline was never needed. If brokers click it: they've told you they want it — then build it properly.

---

### REQUEST_VS_CASE_VERDICT

**Use "Case" internally and in the broker UI. Use "Request" in customer-facing language.**

Case wins because brokers think in cases. The broker mental model is: "I have open cases, I work cases, I close cases." The word "task" is wrong (too CRM). "Activity stream" is a component, not a model. "Request" is the customer's word for the same object.

One system, two vocabulary layers: customers submit Requests, brokers work Cases.

---

### BEST_READINESS_MODEL

**Binary required-field checklist with three statuses: ✅ confirmed / ⚠️ needs confirmation / ❌ missing.**

Required fields: VIN, Year, Make, Model, Garaging ZIP, Primary Driver.
Optional flag: Lienholder (flagged if not present, with note: "Ask if car is financed").

No percentage. No People/Vehicle/Coverage buckets. Each field is either present or not. The broker sees exactly what to copy and exactly what to ask for.

The current three-bucket model survives but is slightly wrong:
- "Garaging ZIP" belongs with Vehicle (it's a property of vehicle location), not as a standalone.
- "Coverage" should be renamed "Finance & Timing" (lienholder + effective date) to be honest about what the customer actually provides.
- "People" is accurate but should be renamed "Driver" for broker clarity.

---

### CURRENT_TRUTH_VERDICT

**Correct model. Add three things before 5-broker scale:**

1. `copied_at` timestamp (records when broker copied the packet — enables retroactive correction warnings).
2. Correction count displayed in packet header when a VIN has changed more than once.
3. Hard rule: CLOSED cases never accept Current Truth updates; new submission creates a new case.

The Current Truth model is the right mental model for the broker. History is preserved, current state is what the broker acts on. The risk is not the model but the implementation: the document anchor priority logic must reliably select the correct VIN as Current Truth under all document combinations.

---

### WHAT_TO_REMOVE

1. Timeline UI panel from PacketStep (defer to "broker asks for it")
2. `related_vehicles` JSONB structure (replace with one warning line)
3. `MISSING_VIN` as a formal sub-state (collapse into MISSING_ITEMS)
4. Document anchor priority as automatic logic (replace with "flag all conflicts, broker resolves")
5. SB-1, SB-2, SB-3 as code-enforced sub-rules (keep as documented business rules; implement only after 25+ real cases)
6. Readiness percentage (replace with binary field checklist)

---

### WHAT_TO_KEEP

1. Upload → Extract → Packet (the entire product lives here)
2. VIN validation (format check + conflict warning)
3. Source attribution (from: [filename] next to each field)
4. Copy Fields (the money moment)
5. Missing items display (exact field names, not abstracted scores)
6. Chinese bilingual follow-up message (N1) — highest-ROI feature after core loop
7. (phone, VIN) case identity rule — correct granularity; do not change
8. Hard rule: never silently overwrite a confirmed VIN
9. Hard rule: closed cases don't accept appends
10. Hard rule: never auto-remove an old vehicle from a policy

---

### WHAT_TO_FREEZE_NOW

1. **Ant Design 5 — frozen.** No UI library migration.
2. **Gemini Flash 2.5 — frozen.** Primary extraction provider.
3. **GCS — frozen.** Evidence storage.
4. **Trusted Packet as the product deliverable name — frozen.**
5. **Copy Fields as the broker UX — frozen.**
6. **(phone, VIN) as case identity — frozen for add-car.**
7. **"No auto-remove" rule — frozen.** Broker must always confirm vehicle removal.
8. **"No WeChat bot" — frozen.** Paste-link is sufficient and avoids WeChat API compliance.
9. **"No carrier quote integration" — frozen for 12 months.**
10. **"No customer portal" — frozen.** Customers interact with brokers, not with P16.

**New freeze to add:** The document anchor priority logic is NOT frozen in V1. It will be flagged-and-broker-resolves for the pilot. Automatic priority logic is locked for post-25-case review.

---

### GO_OR_NO_GO

**GO on the Chen Kui pilot. GO on N1 as the next build. NO-GO on Timeline implementation.**

The pilot is live. The product works (CK-DRY-01: 14 seconds). The first real case can run today. Nothing in this stress test changes that.

The one priority reorder: **build N1 (Chinese follow-up message generator) before building Timeline.** N1 affects 70–80% of all pilot cases immediately. Timeline affects zero broker workflows — it's internal event logging with a UI wrapper. N1 is the North Star's missing clause made real. Timeline is engineering.

If Timeline was scheduled before N1: swap the order. N1 first. Timeline when a broker asks for case history.

---

### FINAL_NORTH_STAR_ALIGNMENT

The current North Star — "Whatever a Chinese insurance customer sends, turn it into a Broker Ready Request. Show readiness. Identify missing items. Generate follow-up. Help the broker complete the insurance action." — aligns with the stress test findings on all critical dimensions:

- **"Whatever they send"** → the extraction pipeline handles all document types through the same core loop. ✅
- **"Broker Ready Request"** → the Trusted Packet with Copy Fields is exactly this. ✅
- **"Show readiness"** → binary checklist (✅/⚠️/❌ per field) is the correct implementation. Readiness % is not. ✅ (if implemented correctly)
- **"Identify missing items"** → missing items detection is live and working. ✅
- **"Generate follow-up"** → N1 (Chinese bilingual follow-up) is not yet built. This is the one gap between the North Star's promise and the current reality. ⚠️
- **"Help the broker complete the insurance action"** → Copy Fields is the mechanism. VIN validation + source attribution are the trust layers. ✅

**The North Star is correct. The current product fulfills 5 of 6 clauses. N1 closes the 6th. Build N1.**

---

### ONE_SENTENCE_RECOMMENDATION

**Keep the extraction pipeline and trust layer exactly as designed, remove the Timeline UI and related_vehicles metadata from V1, build N1 before anything else, and test the document anchor priority logic against 25 real cases before writing a single line of automatic conflict resolution code.**

---

```
FILES_CREATED:
  docs/p16/P16_SIMPLICITY_STRESS_TEST.md

FILES_UPDATED:
  None. All findings are advisory. Changes require Andy approval before any doc or code update.

REQUEST_MODEL_SCORE: 7 / 10
  Perfect for document-submission scenarios (add car).
  Breaks for intent-only scenarios (remove car, address change, coverage change).
  Do not extend to non-document scenarios. Keep it scoped.

TOP_5_COMPLEXITY_TRAPS:
  1. Document anchor priority as automatic system logic — test real docs first; flag+broker for pilot
  2. Universal intake model for carrier switch + add-car — keep schemas separate; N2 is not add-car extension
  3. Timeline before broker queue — broker queue is more urgent; build it by the 3rd broker
  4. Infinite append on closed cases — enforce 90-day expiry and closed-case guardrail strictly
  5. Readiness percentage — destroys information; replace with binary field checklist

TOP_5_SIMPLIFICATIONS:
  1. All VIN conflicts → flag + broker resolves (remove automatic anchor priority from V1)
  2. related_vehicles JSONB → one warning line in packet
  3. MISSING_VIN sub-state → collapse into MISSING_ITEMS
  4. Case URL in follow-up message (closes the return-customer loop for free)
  5. Defer Timeline until a broker explicitly asks for case history

REQUEST_VS_CASE_VERDICT:
  Case is the correct internal model. Request is the correct customer-facing word.
  Never say "task" to a broker. Never say "case" to a customer.

BEST_READINESS_MODEL:
  Binary per-field checklist: ✅ confirmed / ⚠️ needs confirmation / ❌ missing.
  Five required fields: VIN, Year/Make/Model, Garaging ZIP, Primary Driver.
  Optional flag: Lienholder (ask if car is financed).
  No percentage. No abstract buckets.

CURRENT_TRUTH_VERDICT:
  Correct model. Add: (1) copied_at timestamp, (2) correction count header warning,
  (3) closed-case immutability rule. Document anchor priority is the highest-risk component
  — test against 25 real conflict cases before automating.

WHAT_TO_REMOVE:
  Timeline UI from PacketStep; related_vehicles JSONB; MISSING_VIN sub-state;
  automatic document anchor priority; SB-1/SB-2/SB-3 as code rules; readiness percentage.

WHAT_TO_KEEP:
  Upload → Extract → Packet; VIN validation; source attribution; Copy Fields;
  missing items display; Chinese follow-up (N1); (phone, VIN) identity; 
  all hard prohibitions (no silent VIN overwrite, no auto-remove, no closed-case append).

WHAT_TO_FREEZE_NOW:
  Add to the frozen list: document anchor priority logic stays flag+broker-resolves for V1.
  All existing frozen decisions from P16_DECISION_FREEZE_V1.md remain frozen.

GO_OR_NO_GO:
  GO on Chen Kui pilot (already running).
  GO on N1 (Chinese follow-up message) as the immediate next build.
  NO-GO on Timeline implementation before N1.
  NO-GO on automatic anchor priority before 25 real conflict cases.
  NO-GO on related_vehicles JSONB in V1.

FINAL_NORTH_STAR_ALIGNMENT:
  5 of 6 North Star clauses are live. N1 closes the 6th ("generate follow-up").
  The North Star is correct. The product is aimed correctly.
  The only open execution item is N1. Build it.

ONE_SENTENCE_RECOMMENDATION:
  Keep the extraction pipeline and trust layer exactly as designed, remove the
  Timeline UI and related_vehicles metadata from V1, build N1 before anything else,
  and test the document anchor priority logic against 25 real cases before writing
  a single line of automatic conflict resolution code.
```

---

*Authored: 2026-06-19. Mission: attack business rules, find complexity, recommend simplification.*  
*All P16 documents as of 2026-06-19 used as context.*  
*No code designed. Business logic and decision rules only.*  
*Authority for scope changes: Andy approval required before any doc or code update.*  
*SSOT for P16: `docs/p16/P16_DECISION_FREEZE_V1.md`*
