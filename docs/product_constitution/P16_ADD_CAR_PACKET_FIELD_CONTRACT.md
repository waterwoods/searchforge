# P16 Add-Car Packet Field Contract

**Date:** 2026-06-17  
**Sprint:** P16 Add-Car Packet Builder — Product Definition Sprint  
**Authority:** This is the locked field definition for Add-Car MVP. Changes require explicit sprint revision.

---

## Purpose

This document defines:
1. Every field that appears in a Quote-Ready Packet
2. Whether it is required before office submission
3. Whether AI can extract it from uploaded documents
4. Whether customer must confirm it
5. How conflicts and missing values are handled

---

## Field Contract Table

| Field | Category | Required | AI Extractable | Customer Confirms | Source |
|-------|----------|----------|----------------|-------------------|--------|
| Customer name | Customer | ✅ Required | ⚠️ Sometimes (from docs) | ✅ Yes | Screen 1 input + optional doc extraction |
| Phone number | Customer | ✅ Required | ❌ No | ❌ No | Screen 1 input only |
| VIN | Vehicle | ✅ Required | ✅ Yes | ✅ Yes (always) | VIN photo, dealer PDF, registration |
| Year | Vehicle | ✅ Required | ✅ Yes | ✅ Yes | Dealer paperwork, registration |
| Make | Vehicle | ✅ Required | ✅ Yes | ✅ Yes | Dealer paperwork, registration, insurance card |
| Model | Vehicle | ✅ Required | ✅ Yes | ✅ Yes | Dealer paperwork, registration |
| Trim / package | Vehicle | ❌ Optional | ✅ Yes | ❌ No | Dealer paperwork |
| Color | Vehicle | ❌ Optional | ✅ Yes | ❌ No | Dealer paperwork |
| Purchase price | Vehicle | ❌ Optional | ✅ Yes | ❌ No | Purchase contract |
| Odometer reading | Vehicle | ❌ Optional | ✅ Yes | ❌ No | Registration, contract |
| Lienholder / lender | Policy | ❌ Optional | ✅ Yes | ❌ No | Purchase contract, dealer paperwork |
| Loan account # | Policy | ❌ Optional | ✅ Yes | ❌ No | Financing documents |
| Garaging ZIP | Location | ✅ Required | ✅ Yes | ✅ Yes | Registration, insurance card, dealer address |
| Mailing address | Location | ❌ Optional | ✅ Yes | ❌ No | Registration, insurance card |
| Primary driver name | Driver | ✅ Required | ⚠️ Sometimes | ✅ Yes | Sometimes on insurance card or contract |
| Primary driver DOB | Driver | ❌ Optional | ⚠️ Sometimes | ✅ Yes (if extracted) | Insurance card |
| Driver license # | Driver | ❌ Optional | ⚠️ Sometimes | ✅ Yes (if extracted) | Registration, insurance card |
| Delivery date | Dates | ✅ Required | ✅ Yes | ✅ Yes | Dealer paperwork, purchase contract |
| Effective / start date | Dates | ✅ Required | ✅ Yes | ✅ Yes | Dealer paperwork, insurance card |
| Current insurer | Policy | ❌ Optional | ✅ Yes | ❌ No | Insurance card |
| Current policy number | Policy | ❌ Optional | ✅ Yes | ❌ No | Insurance card |
| Current policy expiry | Policy | ❌ Optional | ✅ Yes | ❌ No | Insurance card |
| Uploaded evidence sources | Evidence | ✅ Required | N/A (system) | N/A | File upload |

---

## Required vs Optional Classification

### Required Before Office Submit (8 fields)

These 8 fields must be present and customer-confirmed before the packet is submitted:

1. Customer name
2. Phone number
3. VIN
4. Year
5. Make / Model
6. Garaging ZIP
7. Primary driver name
8. Delivery / effective date

If any required field is missing → packet status = `MISSING FIELDS` → office sees red flag → customer is prompted to complete.

### Optional Fields (nice-to-have for better quote accuracy)

- Trim / package
- Color
- Purchase price
- Odometer
- Lienholder / lender
- Loan account number
- Mailing address
- Primary driver DOB
- Driver license number
- Current insurer
- Current policy number
- Current policy expiry

Optional fields that are found are always included in the packet. Their absence does not block submission.

---

## Extraction Confidence Levels

| Confidence Level | Definition | Action |
|------------------|------------|--------|
| High (≥90%) | Field clearly present in document | Show pre-filled, minimal confirmation |
| Medium (70–89%) | Field found but partially ambiguous | Show with "Please confirm" yellow indicator |
| Low (<70%) | Field found but high ambiguity | Show with "Needs confirmation" warning; do not pre-fill as fact |
| Not found | Field not in any document | Show as empty "Still Needed" |

---

## Conflict Rules

### Duplicate Same Value

- Two documents contain the same VIN → **merge silently**
- Source: "VIN confirmed in 2 documents"

### Duplicate Different Value

- Two documents contain different VINs → **show conflict**
- UI: side-by-side comparison with customer choice required
- Packet status: `HAS CONFLICTS` until resolved

### Low Confidence + Missing

- AI extracted field but confidence <70% → shown as "Needs confirmation" in yellow
- Customer must click confirm or correct

### Unrelated Document

- Uploaded file contains no recognizable insurance or vehicle fields → flagged as "No vehicle info found in this file"
- File is still attached as source evidence
- No blocking behavior — submission allowed

### Second Vehicle Detected

- AI detects VIN, year/make/model references to a second distinct vehicle → **soft block**
- Customer shown: "Two vehicles detected. Each must be a separate request."
- Options: submit for vehicle 1 only, start new request, contact broker

### Blocked Submission Cases

| Scenario | Block Type | Reason |
|----------|------------|--------|
| Required field missing | Soft block | Customer must fill |
| Unresolved conflict | Soft block | Customer must choose |
| Two vehicles detected | Soft block | One-request = one-vehicle rule |
| All 5 files unreadable | Hard block | Cannot extract; escalate to broker |

---

## VIN Validation Rules

VIN is the most critical field and has specific validation rules:

1. **Length:** Must be exactly 17 characters
2. **Characters:** No I, O, or Q (VIN standard)
3. **Format:** Alphanumeric only
4. **Checksum:** 9th character is a check digit (optional to validate in MVP, recommended)
5. **Conflict:** If two VINs found and they differ by even 1 character → conflict (no auto-resolution)

---

## Garaging ZIP Rules

- Must be a valid 5-digit US ZIP code
- Dealer ZIP ≠ garaging ZIP — AI must not assume garaging ZIP from dealer address
- If no garaging ZIP found in documents → prompt customer manually
- Customer-provided garaging ZIP overrides any extracted ZIP

---

## Date Fields

- Delivery date: the date the customer took possession of the vehicle
- Effective / start date: the date insurance should start (may equal delivery date)
- If delivery date found but effective date not → default effective = delivery date (show for confirmation)
- Past dates → warn "This date is in the past. Please confirm or update."

---

## Data Mapping to Existing case_id

The current codebase uses `case_id` terminology for triage cases. Mapping for P16:

| P16 Customer Concept | Codebase Concept | Notes |
|---------------------|------------------|-------|
| "Request" | `case_id` | Customer-facing uses "request"; internal code may still use `case_id` |
| "Add-car request" | `case_type = add_car` | Already supported in triage.py |
| "Quote-Ready Packet" | Case workbench output | Extended with extraction fields |
| "Submitted to office" | `case_status = submitted` | Existing state |
| "Still needed" | `still_needed` array in case | Existing field |

Customer-facing language must use "request," never "case."  
Internal APIs and database may continue using `case_id`.

---

## Extraction Schema (JSON)

The AI extraction output should conform to this schema:

```json
{
  "extraction_id": "ext_xxx",
  "request_id": "req_xxx",
  "extracted_at": "ISO8601",
  "fields": {
    "vin": {
      "value": "1HGBH41JXMN109186",
      "confidence": 0.95,
      "source_file": "dealer_contract.pdf",
      "source_page": 1,
      "needs_confirmation": false,
      "conflict": null
    },
    "year": { "value": "2024", "confidence": 0.98, "source_file": "dealer_contract.pdf", "needs_confirmation": false, "conflict": null },
    "make": { "value": "Toyota", "confidence": 0.98, "source_file": "dealer_contract.pdf", "needs_confirmation": false, "conflict": null },
    "model": { "value": "Camry", "confidence": 0.97, "source_file": "dealer_contract.pdf", "needs_confirmation": false, "conflict": null },
    "garaging_zip": { "value": null, "confidence": 0, "source_file": null, "needs_confirmation": true, "conflict": null },
    "primary_driver": { "value": null, "confidence": 0, "source_file": null, "needs_confirmation": true, "conflict": null },
    "effective_date": { "value": "2024-08-01", "confidence": 0.90, "source_file": "dealer_contract.pdf", "needs_confirmation": false, "conflict": null }
  },
  "conflicts": [
    {
      "field": "vin",
      "values": [
        { "value": "1HGBH41JXMN109186", "source_file": "dealer_contract.pdf" },
        { "value": "1HGBH41JXMN109187", "source_file": "vin_photo.jpg" }
      ],
      "resolution": null
    }
  ],
  "unrelated_files": [],
  "second_vehicle_detected": false,
  "missing_required_fields": ["garaging_zip", "primary_driver"]
}
```

---

*End of P16 Add-Car Packet Field Contract*
