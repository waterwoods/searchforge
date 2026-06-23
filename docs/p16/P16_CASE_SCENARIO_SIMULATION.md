# P16 Business Scenario Simulation — Add / Replace / Multi-Vehicle Case Rules

**Date:** 2026-06-19  
**Sprint:** P16 Timeline Design — Pre-Implementation Business Review  
**SSOT:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Status:** SIMULATION ONLY — no code written  
**Purpose:** Validate Case Identity rule and edge-case handling before Timeline implementation  

---

## 1. Executive Summary

The current P16 Case Identity rule is:

> **(phone, VIN) = one Add-Car Case**

This simulation stress-tests that rule against 10 real-world scenarios: simple add, old insurance card, replace/trade-in, two new cars, same-car follow-up, wrong document only, teen driver added, no VIN yet, and customer returning days later.

**Verdict: The (phone, VIN) rule is correct and sufficient for the paid pilot.**

However, three edge cases require explicit sub-rules to prevent silent errors:

1. **Old insurance card must never become the main case vehicle.** Only a purchase agreement, new registration, or dealer document can anchor the main case VIN. An insurance card for an old vehicle is supporting context only.
2. **Replace/trade-in is a single case with a related action, not two cases.** The new VIN anchors the case. The old VIN is flagged as a related vehicle. Broker confirms removal.
3. **Two new cars at the same time = two cases, one per VIN.** No merge, no exception.

All ten scenarios fit cleanly within the existing rule once these three sub-rules are spelled out. No case explosion. No giant customer case. The broker sees one main case per new vehicle, with related-vehicle warnings when needed.

**Go/No-Go for Timeline implementation: GO** — the case identity rule is validated. The Timeline design in `P16_TIMELINE_STATE_MACHINE_DESIGN.md` can proceed as written.

---

## 2. Best Business Rule

**Primary rule (keep as-is):**

> One Add-Car Case = one (phone, VIN) pair.

**Three mandatory sub-rules (new — add to SSOT):**

| Sub-Rule | Statement |
|----------|-----------|
| **SB-1 New Vehicle Anchor** | Only a purchase agreement, new vehicle registration, or dealer paperwork can anchor the main case VIN. An insurance card or title for a vehicle the customer already owns is supporting context, not a new case trigger. |
| **SB-2 Replace = One Case** | When a customer says they are replacing an old vehicle with a new one, create one case for the new VIN. Attach the old VIN as `related_vehicle` with action `PENDING_REMOVAL`. Do not create a case for the old car. Do not remove old car automatically. Broker confirms. |
| **SB-3 Two New Cars = Two Cases** | If a customer buys two vehicles in the same session or same phone interaction, create two separate cases — one per new VIN. Never merge. Show broker both. |

**Hard prohibitions (never do these):**

1. Never silently overwrite a VIN already anchored to a case.
2. Never merge two different new vehicle VINs into one case.
3. Never auto-remove an old vehicle from the policy — always flag for broker.
4. Never create a case for an old insurance card alone when the stated intent is "add car."
5. Never treat every upload as a new case (same VIN + same phone = append).

---

## 3. Scenario Table

| # | Scenario | Main Case? | Main VIN | Related Vehicle? | New Case? | Merge? | Ask Broker? | Ask Customer? | Case State | Next Action |
|---|----------|------------|----------|------------------|-----------|--------|-------------|---------------|------------|-------------|
| 1 | Simple Add-Car | ✅ Yes | New VIN (e.g. Tesla) | None | ✅ Yes | No | No | No | READY_FOR_QUOTE | Copy packet → submit |
| 2 | New Car + Old Insurance Card | ✅ Yes | New Tesla VIN | BMW (old) = supporting context | No | No | ⚠️ Soft flag | No | READY_FOR_QUOTE (Tesla) | Verify old BMW is not being quoted |
| 3 | Replace Old Car | ✅ Yes | New Tesla VIN | BMW = related / pending removal | No | No | ✅ Yes — confirm removal | No | READY_FOR_QUOTE | Broker confirm: remove BMW from policy |
| 4 | Trade-In | ✅ Yes | New car VIN | Trade-in VIN = flagged | No | No | ✅ Yes — verify VINs | No | READY_FOR_QUOTE + VIN_CONFLICT | Broker verify which VIN is new |
| 5 | Two New Cars | ✅ Yes ×2 | Tesla VIN / Honda VIN | None | ✅ Yes ×2 | Never | ✅ Yes — show both | No | Two READY_FOR_QUOTE | Broker processes both cases |
| 6 | Same Car, More Docs Later | ✅ Same case | Same VIN | None | No | ✅ Append | No | No | READY_FOR_QUOTE | New docs added to existing case |
| 7 | Wrong Old Card Only | ✅ Yes | Old BMW VIN (wrong) | None | ✅ Yes (incomplete) | No | ✅ Yes — flag | ✅ Yes — ask for new vehicle docs | MISSING_ITEMS | Customer must upload new vehicle docs |
| 8 | Teen Driver Added | ✅ Same Tesla case | Tesla VIN | None | No | Append event | No | No | READY_FOR_QUOTE | Related driver action logged; broker confirms |
| 9 | No VIN Yet | ✅ Pending | MISSING | None | ✅ Yes (pending) | No | No | ✅ Yes — ask for VIN | MISSING_VIN | Customer must provide VIN |
| 10 | Customer Returns Days Later | ✅ Same case | Same VIN | None | No | ✅ Append | No | No | (existing state) | New docs appended to existing case timeline |

---

## 4. Scenario Detail — Each Case

---

### Scenario 1: Simple Add-Car

**What happened:** Andy uploads an insurance card + new car purchase agreement. One new Tesla VIN found.

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, Tesla VIN) |
| **Main vehicle** | Tesla (new) |
| **Related vehicle** | None |
| **New case?** | Yes — first upload for this VIN |
| **Merge?** | No |
| **Ask broker?** | No |
| **Ask customer?** | No |
| **Timeline events** | CASE_CREATED → DOCUMENT_UPLOADED ×2 → AI_EXTRACTED_PACKET → VIN_VALIDATED → PACKET_READY |
| **Case state** | READY_FOR_QUOTE |
| **Next action** | Broker copies packet and submits to carrier |

**Ruling:** Standard happy path. No rule complexity. (phone, VIN) works perfectly.

---

### Scenario 2: New Car + Old Insurance Card

**What happened:** Andy uploads a new Tesla purchase agreement AND an old BMW insurance card in the same session.

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, Tesla VIN) |
| **Main vehicle** | Tesla (new purchase agreement = anchor document) |
| **Related vehicle** | BMW (old) — detected as second vehicle in upload set |
| **New case?** | No — same session, one case |
| **Merge?** | No |
| **Ask broker?** | Yes — soft flag: "Second vehicle detected (BMW). Confirm this is supporting context, not a new vehicle to add." |
| **Ask customer?** | No |
| **Timeline events** | CASE_CREATED → DOCUMENT_UPLOADED ×2 → AI_EXTRACTED_PACKET → VIN_VALIDATED (Tesla) → VIN_CONFLICT_FLAGGED (BMW detected) → PACKET_READY |
| **Case state** | READY_FOR_QUOTE (Tesla) with warning |
| **Next action** | Broker verifies: "This case is for the Tesla. The BMW card is context only — not adding BMW." |

**Critical rule validated here:** The anchor VIN for the main case must be determined by document type priority:

| Document Type Priority | Rule |
|-----------------------|------|
| 1. New purchase agreement / dealer contract | Always anchor. This is the new vehicle. |
| 2. New vehicle registration | Anchor if purchase agreement absent. |
| 3. Existing insurance card | Supporting context only. Never becomes main case VIN unless it is the only document AND intake intent is "add car for this vehicle." |

**Why this matters:** If the system naively picks whichever VIN appears first in the extraction, it might anchor to the BMW and quote the wrong car. The purchase agreement must win.

**SB-1 sub-rule is validated:** Old insurance card does not anchor a new case automatically.

---

### Scenario 3: Replace Old Car

**What happened:** Andy says "I bought a Tesla. Please replace my BMW." Uploads Tesla purchase agreement. May also include old BMW registration.

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, Tesla VIN) |
| **Main vehicle** | Tesla (new purchase) |
| **Related vehicle** | BMW — flagged as `related_vehicle` with `pending_action: REMOVE_FROM_POLICY` |
| **New case?** | Yes — new VIN, new case |
| **Merge?** | No — never merge replace context into old vehicle case |
| **Ask broker?** | Yes — "Customer stated they are replacing their BMW. Confirm removal before policy change." |
| **Ask customer?** | No — customer already stated intent. No need to re-confirm. |
| **Timeline events** | CASE_CREATED → DOCUMENT_UPLOADED → AI_EXTRACTED_PACKET → VIN_VALIDATED (Tesla) → RELATED_VEHICLE_FLAGGED (BMW, pending_removal) → PACKET_READY |
| **Case state** | READY_FOR_QUOTE with related vehicle action pending |
| **Next action** | Broker: (1) Process Tesla add. (2) Confirm BMW removal separately. |

**SB-2 sub-rule is validated:**

- One case (for the new Tesla).
- Related vehicle action (remove BMW) is a broker-confirmed step.
- System never auto-removes BMW.
- System does not create a second "BMW case."
- Timeline shows the pending removal action clearly.

---

### Scenario 4: Trade-In

**What happened:** Dealer paperwork includes both the new car VIN and the trade-in VIN. Customer uploads the full dealer packet as one PDF.

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, new car VIN) |
| **Main vehicle** | New car (purchase agreement wins as anchor) |
| **Related vehicle** | Trade-in VIN — flagged as `trade_in_detected` |
| **New case?** | No — same upload session |
| **Merge?** | No |
| **Ask broker?** | Yes — VIN_CONFLICT_FLAGGED: "Trade-in VIN detected. Verify which VIN is the new vehicle." |
| **Ask customer?** | No (broker handles) |
| **Timeline events** | CASE_CREATED → DOCUMENT_UPLOADED → AI_EXTRACTED_PACKET → VIN_VALIDATED (new) → VIN_CONFLICT_FLAGGED (trade_in_detected) → PACKET_READY |
| **Case state** | READY_FOR_QUOTE + VIN_CONFLICT warning |
| **Next action** | Broker verifies new VIN is correct. Treats trade-in VIN as vehicle being removed (same as replace). |

**Decision Freeze §4 alignment:** "Complex trade-in workflow" is frozen out. This simulation confirms the right behavior: flag the trade-in VIN, let the broker handle it manually. No automation. No second case. One packet, one warning.

---

### Scenario 5: Two New Cars

**What happened:** Andy buys a Tesla AND a Honda at the same dealership on the same day. Uploads both purchase agreements.

| Field | Value |
|-------|-------|
| **Main case identity** | Two separate cases: (Andy's phone, Tesla VIN) and (Andy's phone, Honda VIN) |
| **Main vehicle (case A)** | Tesla |
| **Main vehicle (case B)** | Honda |
| **Related vehicle** | None — these are independent new vehicles |
| **New case?** | Yes ×2 — one per new VIN |
| **Merge?** | Never — SB-3 hard rule |
| **Ask broker?** | Yes — show both cases in broker view. "Two new vehicles detected for same customer. Processing as separate cases." |
| **Ask customer?** | No |
| **Timeline events** | Each case gets its own full timeline |
| **Case state** | Two × READY_FOR_QUOTE |
| **Next action** | Broker handles Tesla case, then Honda case, separately. Each gets its own packet. |

**Why not merge?** If VIN-A is for a $90,000 Tesla (comprehensive + collision) and VIN-B is a $15,000 Honda (liability only), they will have different coverage, different lienholders, different rates. Merging is a quoting disaster.

**UI implication:** Broker queue shows two cases for same phone. This is correct and expected. Not a bug.

**SB-3 sub-rule is validated:** Two new cars = two cases, always. No exception.

---

### Scenario 6: Same Car, More Docs Later

**What happened:** Andy uploaded an insurance card on Monday. On Thursday, Andy uploads the registration for the same car (same VIN).

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, BMW VIN) — same as Monday's case |
| **Main vehicle** | Same BMW |
| **Related vehicle** | None |
| **New case?** | No — `find_active_add_car_case_by_phone()` returns existing case. VIN matches. Append. |
| **Merge?** | Yes — append new document to existing case. Emit DOCUMENT_UPLOADED on existing case. |
| **Ask broker?** | No |
| **Ask customer?** | No |
| **Timeline events** | (existing events from Monday) → DOCUMENT_UPLOADED (registration.png) → AI_EXTRACTED_PACKET (incremental) → VIN_VALIDATED (same) → PACKET_READY (updated) |
| **Case state** | READY_FOR_QUOTE (updated with new fields from registration) |
| **Next action** | Broker re-reviews updated packet. New fields from registration now present (e.g., garaging ZIP confirmed). |

**Key behavior:** The extraction runs again on the new document. New fields extracted from the registration (odometer, mailing address, ZIP confirmation) are merged into the packet. Existing confirmed fields (VIN, make, model, year) are not overwritten — they are confirmed by the second document.

**Conflict detection:** If the registration has a different VIN than what was already anchored → VIN_CONFLICT_FLAGGED. Do not auto-overwrite.

---

### Scenario 7: Wrong Old Insurance Card Only

**What happened:** Andy uploads only an old BMW insurance card, but says the intent is "add car." No purchase agreement, no new vehicle documents.

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, BMW VIN from insurance card) — but this is the wrong vehicle |
| **Main vehicle** | BMW (old) — extracted from insurance card |
| **Related vehicle** | None |
| **New case?** | Yes — but incomplete / wrong direction |
| **Merge?** | No |
| **Ask broker?** | Yes — flag: "Only existing insurance card uploaded. No new vehicle document found. Customer intent was to add a car." |
| **Ask customer?** | Yes — "To add a new car, please upload your purchase agreement, new registration, or dealer paperwork." |
| **Timeline events** | CASE_CREATED → DOCUMENT_UPLOADED → AI_EXTRACTED_PACKET → VIN_VALIDATED (BMW VIN) → MISSING_ITEM_DETECTED (no_new_vehicle_doc) |
| **Case state** | MISSING_ITEMS — specifically `new_vehicle_document_required` |
| **Next action** | Customer uploads correct documents. Case transitions to READY_FOR_QUOTE when new VIN found. |

**Why this matters:** Without this rule, the system would happily generate a Trusted Packet for the customer's existing BMW and the broker would try to quote a car that's already on the policy. Silent, wrong, and trust-destroying.

**Sub-rule added:** If the only extracted VIN appears only on an insurance card (field: `current_policy_number` present, no purchase agreement or new registration), flag as MISSING_NEW_VEHICLE_DOCUMENT.

---

### Scenario 8: Teen Driver Added During Add-Car

**What happened:** Andy is adding a Tesla. While uploading, he also includes his son Kevin's driver license photo (Kevin will be a new driver on the policy).

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, Tesla VIN) |
| **Main vehicle** | Tesla (unchanged) |
| **Related vehicle** | None |
| **New case?** | No — driver addition is a related action on the same case |
| **Merge?** | Append — driver license doc added to same case |
| **Ask broker?** | Soft notice: "Teen driver license detected. Kevin [name] appears to be an additional driver. Confirm primary vs. additional driver." |
| **Ask customer?** | No (broker handles) |
| **Timeline events** | ... (normal extraction events) ... → ADDITIONAL_DRIVER_DETECTED (Kevin, teen, DL#) → PACKET_READY |
| **Case state** | READY_FOR_QUOTE with driver confirmation needed |
| **Next action** | Broker: confirm Kevin as additional driver on Tesla policy. |

**Why not a new case?** Kevin is not buying a car. He's being added as a driver on Andy's car. Drivers are a field in the packet (primary driver, additional drivers), not a vehicle. Case is still (Andy's phone, Tesla VIN).

**Timeline implication:** The `ADDITIONAL_DRIVER_DETECTED` event type should be added to the V1 event list for this edge case, or folded into `DOCUMENT_UPLOADED` with a note in the message field.

---

### Scenario 9: No VIN Yet

**What happened:** Andy sends a message (text/chat) or uploads a photo of the car's exterior that shows no VIN. He says "adding a car" but has no documents yet.

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone) — VIN unknown, pending |
| **Main vehicle** | Unknown — VIN not yet extracted |
| **Related vehicle** | None |
| **New case?** | Yes — create case anchored to phone only, state = MISSING_VIN |
| **Merge?** | No — nothing to merge yet |
| **Ask broker?** | Soft notice: "Case created. No VIN found. Waiting for vehicle documents." |
| **Ask customer?** | Yes — "Please upload your purchase agreement, window sticker, or registration so we can find your VIN." |
| **Timeline events** | CASE_CREATED → DOCUMENT_UPLOADED → AI_EXTRACTED_PACKET → MISSING_ITEM_DETECTED (vin) |
| **Case state** | MISSING_VIN (sub-state of MISSING_ITEMS) |
| **Next action** | Customer uploads correct doc → system extracts VIN → case transitions to (phone, VIN) identity → PACKET_READY |

**VIN arrival rule:** When the VIN is later extracted (on a subsequent upload), the system promotes the case from `(phone, null)` to `(phone, VIN)`. This is the one moment where the VIN anchoring logic runs at transition time rather than at creation time.

**Conflict on VIN arrival:** If two pending-VIN cases exist for the same phone (customer uploaded twice with no VIN), and both now resolve to different VINs → each becomes its own case (SB-3 applies).

---

### Scenario 10: Customer Returns Days Later

**What happened:** Andy submitted an add-car request on Monday for a Tesla. On Friday, he uploads the registration for the same Tesla (same VIN, same phone).

| Field | Value |
|-------|-------|
| **Main case identity** | (Andy's phone, Tesla VIN) — same as Monday |
| **Main vehicle** | Tesla (same VIN, same case) |
| **Related vehicle** | None |
| **New case?** | No — `find_active_add_car_case_by_phone()` finds existing case. VINs match. Append. |
| **Merge?** | Yes — DOCUMENT_UPLOADED event added to existing timeline |
| **Ask broker?** | No — soft notice in timeline: "Additional document added 4 days after initial upload." |
| **Ask customer?** | No |
| **Timeline events** | (existing Monday events) → DOCUMENT_UPLOADED (tesla_registration.png) → AI_EXTRACTED_PACKET → VIN_VALIDATED (same) → PACKET_READY (updated) |
| **Case state** | READY_FOR_QUOTE (updated) |
| **Next action** | Broker re-reviews packet with updated fields from registration. |

**Time gap handling:** The system does not care that 4 days passed. Same phone, same VIN = same case. There is no expiry window for case append in V1. If the broker has already closed the case, the append creates a new case (closed cases do not accept appends — existing guardrail behavior).

---

## 5. Add vs. Replace Rule

**Explicit rule (SB-2):**

```
IF customer states "replace" OR "trade-in" OR "new car, remove old car":
  → Create one new case anchored to NEW VIN
  → Set related_vehicle = OLD VIN, pending_action = PENDING_REMOVAL
  → Show broker: "[New Car] case ready. Related action: Remove [Old Car] — confirm."
  → Do NOT create a case for the old car
  → Do NOT auto-remove old car from policy
  → Broker must explicitly confirm removal (V2 action; V1 = soft broker note)
```

**System detects replace intent by:**

1. Customer explicitly says "replace" / "trade-in" in text/chat input.
2. Dealer paperwork contains both a new purchase agreement VIN and a trade-in vehicle line.
3. Upload set contains both a new purchase agreement and an old registration/insurance card for a different vehicle.

**Heuristic priority for VIN anchoring when two VINs present:**

| Document Type | Priority |
|--------------|----------|
| New purchase agreement VIN | 1 (anchor) |
| New vehicle registration | 2 |
| Dealer trade-in line | 3 (flag as trade-in, not anchor) |
| Existing insurance card | 4 (flag as old/replace, not anchor) |
| Existing title/registration | 4 (flag as old/replace, not anchor) |

**What happens if system cannot determine which VIN is new:**
→ Flag both VINs. Broker resolves. Do not guess. This is the existing VIN_CONFLICT_FLAGGED behavior.

---

## 6. Trade-In Rule

**Explicit rule (from Decision Freeze §4, confirmed here):**

```
Trade-in = flag for broker, no automation.
```

**Operational detail:**

| Condition | Action |
|-----------|--------|
| Single document with two VINs (one is trade-in) | VIN_CONFLICT_FLAGGED. New purchase VIN = main case. Trade-in VIN = flagged in meta. |
| Trade-in line clearly labeled in dealer paperwork | Extract both VINs. Mark the labeled trade-in as `vehicle_role: trade_in`. |
| Cannot determine which is trade-in | Flag both. Broker decides. |
| Broker confirms trade-in | V2 action — post pilot. V1: broker note field. |

**Why not automate:** The broker needs to confirm removal from the current policy and coordinate with the carrier. Automating this wrong (removing the wrong car from the policy) is a catastrophic trust failure. For the paid pilot with Chen Kui, this must be manual. Automation can be considered post-10-case gate.

---

## 7. Old Insurance Card Rule

**Problem:** Customers routinely include old insurance cards in their upload packet because they have them handy. The old card shows a VIN, year, make, model — exactly what the extractor needs — but for the wrong car.

**Rule:**

```
Old insurance card VIN is NEVER the main case anchor 
if a purchase agreement or new vehicle registration is present 
in the same upload set.
```

**Document precedence for VIN anchor:**

```
purchase_agreement > new_registration > VIN_photo > insurance_card > title
```

**Detection signals that an insurance card is "old" (for an existing vehicle):**

- Insurance card policy effective date is more than 30 days before upload date.
- Insurance card VIN matches a vehicle the customer has previously submitted.
- Insurance card contains a `current_policy_number` field (signals existing coverage, not new vehicle).
- Purchase agreement VIN is different from insurance card VIN in the same upload.

**When old insurance card is the ONLY document:**

→ Extract what you can (VIN, make, model, year).
→ Set case state = MISSING_ITEMS with `missing_field: new_vehicle_document`.
→ Do not generate a READY_FOR_QUOTE packet.
→ Prompt customer: "Please upload your new car purchase agreement or registration to complete your add-car request."

**When old insurance card + new purchase agreement are both present:**

→ Anchor to purchase agreement VIN.
→ Show old insurance card as supporting context (current coverage info: policy number, expiry, insurer).
→ VIN_CONFLICT_FLAGGED with `conflict_reason: old_insurance_card_detected`.
→ Broker sees both vehicles in packet context.

---

## 8. Two-New-Car Rule

**Rule (SB-3):**

```
Two different new vehicles in one customer session = two cases, 
one per new VIN. Never merge. Never combine into one packet.
```

**Detection:**

- Upload set contains two distinct purchase agreements with different VINs, both with recent delivery dates.
- Chat/text says "I bought a Tesla and a Honda."
- No trade-in signal present (if trade-in present, use trade-in rule instead).

**Case creation:**

```
POST /api/intake/add-car/extract (batch with both documents)
  → system detects two purchase agreement VINs
  → creates case_A: (phone, VIN_Tesla)
  → creates case_B: (phone, VIN_Honda)
  → returns two case_ids in response
  → UI prompts: "Two new vehicles detected. Each has been set up as a separate case."
```

**Broker view:**

- Both cases appear in broker queue for the same customer phone.
- Broker processes Tesla case first, Honda case second.
- No cross-contamination of fields between the two packets.

**Why the current system (single case per session) needs extension here:**

The existing extract endpoint assumes one upload session = one case. For two-new-car, the response schema must be extended to return an array of cases (`cases: [CaseA, CaseB]`) rather than a single `case_id`. This is a V1 extension point, not a breaking change.

**For pilot simplicity (V1 / Chen Kui):** Two-new-car is rare. If it occurs, acceptable fallback: system flags `second_vehicle_detected`, broker manually creates the second case. Automate the split in V2.

---

## 9. Pending VIN Rule

**Rule:**

```
IF no VIN found after extraction:
  → Create case anchored to phone only
  → Set case state = MISSING_VIN
  → Do not block customer submission (case is created, not rejected)
  → Prompt customer for vehicle documents
  → When VIN arrives (next upload), anchor case to (phone, VIN)
  → IF two pending-VIN cases exist for same phone and both resolve to different VINs: 
      create two separate cases (SB-3 applies)
```

**Phone-only case identity collision:**

A customer might upload twice with no VIN before their first VIN document arrives. This creates two pending-VIN cases for the same phone. Resolution:

1. On first VIN arrival: anchor first pending case to VIN. Merge any additional docs that appear to belong to same vehicle.
2. On second VIN arrival (same phone, different VIN): create separate case (SB-3).
3. Broker sees both — no silent behavior.

**What triggers VIN arrival detection:**

Any new upload to the same phone where VIN is successfully extracted for the first time on a pending-VIN case.

**State machine for pending VIN:**

```
MISSING_VIN → (VIN extracted on new upload) → PACKET_BUILT → READY_FOR_QUOTE
```

---

## 10. Timeline Implication

The 10 scenarios validate the existing Timeline design in `P16_TIMELINE_STATE_MACHINE_DESIGN.md` with four additions:

| Addition | Why |
|----------|-----|
| **`RELATED_VEHICLE_FLAGGED` event type** | Needed for Replace (Scenario 3) and Trade-In (Scenario 4). Carries `related_vin`, `relationship_type` (replace / trade_in / old_card), `pending_action`. |
| **`MISSING_VIN` case state** | Needed for Scenario 9 (no VIN yet). Sub-state of MISSING_ITEMS. Triggers different customer prompt. |
| **`ADDITIONAL_DRIVER_DETECTED` event type** | Needed for Scenario 8 (teen driver). Prevents driver license from being treated as a new vehicle case. |
| **`NEW_VEHICLE_DOCUMENT_REQUIRED` missing item reason** | Needed for Scenario 7 (wrong old card only). More specific than generic MISSING_ITEMS. |

**Revised event type list (V1 additions in bold):**

| Event Type | Status |
|------------|--------|
| CASE_CREATED | Existing design |
| DOCUMENT_UPLOADED | Existing design |
| AI_EXTRACTED_PACKET | Existing design |
| VIN_VALIDATED | Existing design |
| PRIMARY_DRIVER_DEFAULTED | Existing design |
| MISSING_ITEM_DETECTED | Existing design |
| VIN_CONFLICT_FLAGGED | Existing design |
| PACKET_READY | Existing design |
| **RELATED_VEHICLE_FLAGGED** | **New — add before Timeline implementation** |
| **ADDITIONAL_DRIVER_DETECTED** | **New — add before Timeline implementation** |

**`MISSING_VIN` state:**

Add to the state machine:

```
NEW → MISSING_VIN → (VIN arrives) → DOCS_UPLOADED → PACKET_BUILT → READY_FOR_QUOTE
```

The `MISSING_VIN` state is a sub-state of `MISSING_ITEMS`. No new database column needed. Store in `extra JSONB` as `p16_packet_state: "missing_vin"`.

---

## 11. Data Model Implication

The existing data model handles 8 of 10 scenarios without change. Two additions are needed:

### Addition 1: `related_vehicles` on Case

```python
# In service_records.extra JSONB (no schema change needed for V1)
{
  "p16_packet_state": "ready_for_quote",
  "related_vehicles": [
    {
      "vin": "5UXZV4C56BL402905",    # BMW VIN
      "relationship": "replace",      # or "trade_in", "old_insurance_card"
      "pending_action": "REMOVE_FROM_POLICY",  # or None
      "source_file": "old_insurance_card.png",
      "broker_confirmed": false
    }
  ]
}
```

This is additive to the existing `extra JSONB`. No migration needed. For V2, promote to a proper `related_vehicles` table after the pilot.

### Addition 2: `MISSING_VIN` as explicit state value

```python
# In p16_packet_state enum (stored in extra JSONB)
P16_PACKET_STATES = [
    "new",
    "docs_uploaded",
    "packet_built",
    "missing_items",
    "missing_vin",      # NEW — add to state machine
    "ready_for_quote",
    "closed",
]
```

### No other data model changes needed for V1 pilot.

The two new event types (`RELATED_VEHICLE_FLAGGED`, `ADDITIONAL_DRIVER_DETECTED`) are stored in `case_activity` JSONB just like existing events. No schema change.

The `related_vehicles` array and `missing_vin` state are stored in `service_records.extra` JSONB. No migration.

**Full model summary:**

| Scenario | Existing Model Sufficient? | New Field Needed |
|----------|---------------------------|-----------------|
| 1. Simple Add-Car | ✅ Yes | None |
| 2. Old Insurance Card | ✅ Yes | `related_vehicles` in extra |
| 3. Replace Old Car | ✅ Yes | `related_vehicles` + `pending_action` in extra |
| 4. Trade-In | ✅ Yes (existing `additional_vehicle_mentioned`) | `related_vehicles.relationship = trade_in` |
| 5. Two New Cars | ⚠️ Partial | Response schema returns array of cases (V1 fallback ok) |
| 6. Same Car, More Docs | ✅ Yes | None |
| 7. Wrong Old Card Only | ✅ Yes | `new_vehicle_document_required` in missing items |
| 8. Teen Driver | ✅ Yes | `ADDITIONAL_DRIVER_DETECTED` event type |
| 9. No VIN Yet | ✅ Yes (extra JSONB) | `p16_packet_state = missing_vin` |
| 10. Return Days Later | ✅ Yes | None |

---

## 12. Final Recommendation

### Case Granularity Decision

**Keep: (phone, VIN) = one Add-Car Case.**

This is the right granularity. It is simple enough for the paid pilot. It avoids case explosion (one case per customer) and avoids over-merging (one case per vehicle, not one per customer). It maps cleanly to the broker's mental model: one new car = one intake request.

### Case Identity Rule — Updated Statement

```
One Add-Car Case = one (phone, new_vehicle_VIN) pair.

If VIN is not yet known: case is anchored to phone only, state = MISSING_VIN.
If customer is replacing a car: one new case for the new VIN, 
  related_vehicle = old VIN with pending_action = REMOVE_FROM_POLICY.
If customer is buying two new cars: two cases, one per new VIN.
Same phone + same VIN = append to existing case, never create new case.
```

### Should `P16_DECISION_FREEZE_V1.md` Be Updated?

**Yes — one targeted addition only.**

Add to §14 (Timeline V1 Direction), under "Key implementation decisions":

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Related vehicle handling | `related_vehicles` array in `extra` JSONB; `RELATED_VEHICLE_FLAGGED` timeline event | Replace / trade-in context stored on case without separate case or schema change |
| MISSING_VIN state | Sub-state of MISSING_ITEMS; stored as `p16_packet_state: "missing_vin"` in `extra` | Phone-anchored pending case until VIN arrives |
| Document anchor priority | purchase_agreement > new_registration > VIN_photo > insurance_card > title | Prevents old insurance card from hijacking new vehicle case |

**Do not add:** New tables, new endpoints, new case types, new customer models. All additions stay within existing JSONB / event log pattern.

---

## Output Summary

---

**FILES_CREATED:**
`docs/p16/P16_CASE_SCENARIO_SIMULATION.md` (this document)

**FILES_UPDATED:**
None yet. Recommend one targeted addition to `docs/p16/P16_DECISION_FREEZE_V1.md` §14 as noted above. Defer until Andy approves this simulation.

**BEST_BUSINESS_RULE:**
One Add-Car Case = one (phone, new_vehicle_VIN) pair. Old vehicle / trade-in = related context on same case with pending broker action. Never auto-remove. Never auto-merge two new VINs.

**SCENARIO_FINDINGS:**
All 10 scenarios handled by (phone, VIN) rule + 3 sub-rules (SB-1: anchor priority, SB-2: replace = one case + related vehicle, SB-3: two new cars = two cases). No case explosion. No giant customer case. No silent VIN overwrites.

**CASE_GRANULARITY_DECISION:**
CONFIRMED — (phone, VIN) = one Add-Car Case. Correct granularity for paid pilot. Do not change.

**ADD_REPLACE_RULE:**
Replace = one new case for new VIN. Old VIN = `related_vehicle` with `pending_action: REMOVE_FROM_POLICY`. Broker confirms. System never auto-removes.

**TRADE_IN_RULE:**
Trade-in VIN flagged on main case as `relationship: trade_in`. No separate case. Broker resolves manually. No automation (frozen per Decision Freeze §4).

**OLD_CAR_RULE:**
Old insurance card does not anchor a new case. Document anchor priority: purchase_agreement > new_registration > VIN_photo > insurance_card > title. If old insurance card is only document and intent is "add car," case state = MISSING_ITEMS (new_vehicle_document_required). Customer prompted for new vehicle docs.

**TIMELINE_IMPLICATION:**
Add two event types before implementation: `RELATED_VEHICLE_FLAGGED` (for replace/trade-in/old-card scenarios) and `ADDITIONAL_DRIVER_DETECTED` (for teen driver scenario). Add `MISSING_VIN` as explicit `p16_packet_state` value. All other Timeline design in `P16_TIMELINE_STATE_MACHINE_DESIGN.md` confirmed correct.

**DATA_MODEL_IMPLICATION:**
Two additions, both JSONB-safe (no migration): (1) `related_vehicles` array in `service_records.extra`; (2) `p16_packet_state: "missing_vin"` as new state value. No new tables, no new columns, no migration needed for V1 pilot.

**GO_OR_NO_GO_FOR_TIMELINE:**
GO. Case identity rule is validated. All 10 real-world scenarios are handled cleanly. Timeline implementation can proceed per `P16_TIMELINE_STATE_MACHINE_DESIGN.md` with the two event type additions noted above.

**NEXT_ACTION:**
1. Andy reviews and approves this simulation.
2. If approved: add `RELATED_VEHICLE_FLAGGED` and `ADDITIONAL_DRIVER_DETECTED` event types to `P16_TIMELINE_STATE_MACHINE_DESIGN.md`.
3. Add targeted addition to `P16_DECISION_FREEZE_V1.md` §14 (related vehicle + MISSING_VIN rules).
4. Proceed to Timeline implementation (Day 1 — wire `save_case()` into `add_car.py`).

---

*Simulation authored 2026-06-19. No code written. SSOT: `docs/p16/P16_DECISION_FREEZE_V1.md`.*
