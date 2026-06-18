# P16 Packet Builder — Kill Test Plan

**Date:** 2026-06-17  
**Sprint:** P16 Add-Car Packet Builder — Product Definition Sprint  
**Purpose:** Validate that the P16 Add-Car Packet Builder delivers usable packets in real-world scenarios.

---

## Wu Xiaojie Success Test

> Can Wu Xiaojie decide whether to quote without reading WeChat?

This is the single north star for quality. If Wu Xiaojie needs to go back to WeChat or call the customer after reading the packet, the case fails.

---

## Pass Criteria (Overall)

| Metric | Pass Threshold |
|--------|---------------|
| Cases producing usable packets | ≥ 7 of 10 |
| Minutes saved per case | ≥ 5 minutes |
| Office re-reads WeChat | ≤ 3 of 10 cases |
| VIN extraction accuracy | ≥ 8 of 10 correct (from docs with VIN present) |
| Missing field detection | 100% — no required field silently absent |
| Conflict detection | 100% — no conflict silently resolved |
| Customer confirmation required | 100% — always present before submit |

---

## 10-Case Kill Test

---

### Case 1: Standard — Dealer PDF + VIN Photo + Insurance Card

**Input:**
- dealer_contract.pdf (standard California dealer paperwork with year, make, model, VIN, purchase price, effective date)
- vin_photo.jpg (clear photo of VIN sticker on door jamb)
- insurance_card.png (current State Farm card with policy # and insurer)

**Expected behavior:**
- All required fields extracted: VIN, year, make/model, effective date
- Insurance card provides: current insurer, policy number
- Garaging ZIP: may or may not be in docs — prompt if missing
- Customer confirmation screen shows all pre-filled fields
- Packet status: COMPLETE (or MISSING FIELDS if ZIP not found)

**Pass criteria:**
- VIN matches across dealer PDF and VIN photo
- Year/make/model extracted correctly
- Packet generated in < 60 seconds
- Office packet is copy-ready without re-reading source files

---

### Case 2: Purchase Contract Only (No VIN Photo)

**Input:**
- purchase_contract.pdf (includes VIN, year, make, garaging ZIP, purchase price, delivery date)
- No VIN photo
- No insurance card

**Expected behavior:**
- VIN extracted from contract
- Garaging ZIP extracted from contract
- Primary driver: Missing → prompt customer
- Current insurer: Missing → optional, not blocking
- Packet status: MISSING FIELDS (primary driver required)

**Pass criteria:**
- VIN extracted without VIN photo (from text in contract)
- Missing fields flagged — not silently absent
- Packet does not incorrectly show "COMPLETE"

---

### Case 3: Blurry Insurance Card Screenshot

**Input:**
- insurance_card_blurry.jpg (screenshot, slightly out of focus — OCR confidence expected < 80%)
- No other files

**Expected behavior:**
- Attempt extraction
- Confidence on extracted fields < 80% → shown as "Please confirm" (yellow)
- Fields: current insurer, policy number, customer name (possibly)
- VIN, year, make/model: NOT on insurance card → missing
- Packet status: MISSING FIELDS + HAS LOW CONFIDENCE

**Pass criteria:**
- Low confidence fields shown as "Needs confirmation" — not pre-confirmed
- Customer prompted to review every low-confidence field
- No required field silently filled with low-confidence value

---

### Case 4: Conflicting VINs (Two Files Disagree)

**Input:**
- dealer_contract.pdf — VIN: 1HGBH41JXMN109186
- vin_photo.jpg — VIN: 1HGBH41JXMN109187 (last digit differs — common OCR error or actual typo)

**Expected behavior:**
- Conflict detected: VIN from dealer contract ≠ VIN from photo
- Customer shown: side-by-side conflict widget
- Customer must choose one or type the correct VIN
- Packet blocked until conflict resolved
- Packet records resolution: "Customer selected from dealer contract"

**Pass criteria:**
- Conflict detected and shown — not silently resolved
- Customer must take action
- Packet includes the resolution decision (which VIN was chosen and why)

---

### Case 5: Registration + Dealer Email Screenshot

**Input:**
- registration.jpg (clear photo of CA registration — VIN, year, make, model, plate, mailing address)
- dealer_email_screenshot.png (email from dealer with delivery date, VIN, and garaging address)

**Expected behavior:**
- VIN extracted from both sources → merged (same value) → no conflict
- Year/make/model from registration
- Garaging address/ZIP from dealer email
- Delivery date from dealer email
- Customer confirmation shows 4+ pre-filled fields

**Pass criteria:**
- At least 4 required fields extracted correctly
- Garaging ZIP extracted from email screenshot (not just registration)
- Merge is silent when values agree

---

### Case 6: Photo With Second Vehicle in Frame

**Input:**
- vehicle_photo.jpg (photo of VIN sticker, but background shows another car's plate or sticker)
- OR: dealer_fleet_email.pdf (email with two VINs, one for each car in a fleet deal)

**Expected behavior:**
- AI detects reference to a second vehicle (different VIN or year/make/model)
- Soft block shown: "We detected two vehicles. Each must be a separate request."
- Customer given options: submit for vehicle 1, start new request for vehicle 2, contact broker

**Pass criteria:**
- Second vehicle detected — not silently ignored
- Submission blocked with clear message
- One-vehicle constraint enforced

---

### Case 7: Unrelated Document (Driver License Only)

**Input:**
- drivers_license.jpg (customer's California driver license — no vehicle info, but has name and address)

**Expected behavior:**
- Name extracted (low/medium confidence depending on DL quality)
- Address may be extracted (mailing, not garaging — different)
- VIN, year, make/model: not found
- File flagged as: "No vehicle information found in this file"
- Customer can still continue (not blocked)
- Packet: all required vehicle fields are "Still Needed"

**Pass criteria:**
- File is processed and shown in source list
- Customer is shown "no vehicle info found" notice for that file
- No fake fields extracted from DL
- Submission not blocked if other docs have vehicle fields

---

### Case 8: No Documents at All

**Input:**
- Customer completed Screen 1 (phone + name)
- Customer skipped upload on Screen 2 (clicked "Submit without documents")

**Expected behavior:**
- Screen 4: All fields empty (no extraction)
- "What to upload" guide shown prominently
- All required fields shown as "Still Needed"
- Customer can fill manually (type VIN, year, etc.)
- OR customer sees "Contact your broker" option
- Packet submitted with manual entries if customer types them

**Pass criteria:**
- No crash or error state
- Customer shown clear guidance on what to upload
- System does not block progress entirely — can either fill manually or contact broker
- Manual-entry path results in a valid (but manually filled) packet

---

### Case 9: Fleet / Multi-Vehicle Dealer Document

**Input:**
- fleet_dealer_contract.pdf (dealer document with 3 vehicles, each with own VIN, year, make/model)

**Expected behavior:**
- AI detects multiple VINs in the document
- Hard block: "This document contains multiple vehicles."
- Message: "Please separate your vehicles into individual requests, or contact your broker for a fleet quote."
- System does not attempt to pick one vehicle from three

**Pass criteria:**
- Multi-vehicle document detected
- Submission blocked
- Clear message shown
- Customer not confused

---

### Case 10: Complete Packet — All 5 Document Types

**Input:**
- dealer_paperwork.pdf (complete dealer contract with all vehicle info)
- vin_sticker_photo.jpg (clean VIN photo)
- registration.jpg (CA registration)
- insurance_card.png (current policy)
- dealer_delivery_email.png (email confirmation with delivery date and garaging address)

**Expected behavior:**
- All 8 required fields extracted
- No conflicts (all sources agree)
- No missing required fields
- Customer confirmation screen shows all green checkmarks
- Packet status: COMPLETE
- Suggested office next action: "All required fields present. Ready to quote."

**Pass criteria:**
- Office packet is fully readable in 10 seconds
- Wu Xiaojie can determine quote-readiness without re-reading any source file
- Time from upload complete to packet ready: < 60 seconds
- Zero required fields missing
- Zero unresolved conflicts

---

## Measuring Results

### Time Measurement

| Step | Target |
|------|--------|
| Upload complete → extraction complete | < 30 seconds |
| Extraction complete → customer confirms | < 2 minutes (customer action) |
| Customer confirms → packet visible to office | < 5 seconds |
| Office reads packet → quote decision | < 10 seconds |

### Accuracy Metrics

After running 10-case test, record:

| Case | VIN correct | Fields complete | Conflicts caught | Packet readable | Time to packet | Wu Xiaojie reread needed |
|------|-------------|-----------------|-----------------|-----------------|----------------|--------------------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |
| **Total** | **/10** | **/10** | **/10** | **/10** | **avg** | **/10** |

### Pass Threshold Summary

| Metric | Required Pass | Reason |
|--------|---------------|--------|
| Usable packets | ≥ 7/10 | 70% usability = deployable product |
| VIN accuracy | ≥ 8/10 | VIN is highest-stakes field |
| Conflict detection | 10/10 | No silent resolution allowed |
| Missing field detection | 10/10 | No silent omission allowed |
| Time to packet | < 90 sec avg | Core value proposition |
| Wu Xiaojie re-reads WeChat | ≤ 3/10 | Primary success metric |

---

## Test Execution Instructions

1. Prepare 10 test document sets (use real or realistic mock documents)
2. Run each case against deployed P16 instance (staging)
3. For each case, record: extraction output JSON, confirmation screen state, packet output
4. Have Wu Xiaojie review each packet for 10 seconds and state: "quote-ready / not ready / need more info"
5. Record her decision and whether she needed to re-read any source material
6. Tally results against pass criteria

---

## GO / NO GO Decision

| Result | Decision |
|--------|---------|
| ≥ 7/10 packets usable + ≤ 3 Wu Xiaojie re-reads + avg time < 90 sec | **GO** |
| 5–6/10 usable but time > 90 sec | **CONDITIONAL GO** — fix extraction speed before Chen Kui demo |
| < 5/10 usable | **NO GO** — extraction needs debugging before demo |
| Any case with silent VIN conflict | **NO GO** — safety issue |

---

*End of P16 Packet Builder Kill Test Plan*
