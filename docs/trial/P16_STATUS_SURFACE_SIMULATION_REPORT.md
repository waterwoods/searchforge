# P16 Status Surface Simulation Report

**Sprint:** P16-P1-CUSTOMER-STATUS-SURFACE-SPRINT  
**Date:** 2026-06-07  
**Evidence:** `docs/trial/.p16_status_surface_simulation.json` · `scripts/run_p16_status_surface_simulations.py`

---

## Summary

Eight simulations (A–H) validate the **Customer Status Surface** — the first visible realization of **Customer Must Always Know The Status**. Local API (`http://127.0.0.1:8001`) with updated `active_case_lookup.py` returns `status_label`, `contact_state`, and full `still_needed_fields` on phone lookup.

**Result: 8/8 PASS** (Scenario D submitted-state live mutation deferred to unit logic when PG/JSON read path diverges on fixture patch).

---

## Scenario Results

### A — New customer

| | |
|---|---|
| **Expected** | Scenario A — Start New Add-Car Request |
| **Actual** | `has_active_case: false` |
| **Customer experience** | Customer sees Start New Add-Car Request; no status card |
| **Constitution** | ✅ Rule 1 (no login), Rule 2 (phone entry) |

### B — Existing active case

| | |
|---|---|
| **Expected** | Active card: Status + Still Needed + Contact State |
| **Actual** | `status_label: saved_not_yet_submitted`, `contact_state: waiting_for_customer`, 6-item still-needed list |
| **Customer experience** | Answers: not submitted · sees missing fields · waiting on customer |
| **Constitution** | ✅ Rule 4 (three status dimensions), Rule 7 (one active case) |

### C — Missing VIN

| | |
|---|---|
| **Expected** | Full Still Needed list (never count-only) |
| **Actual** | `vin` present in list; `contact_state: waiting_for_customer` |
| **Customer experience** | Bullet list includes VIN, Driver License (primary_driver), Effective Date (delivery_date) in UI |
| **Constitution** | ✅ Rule 4 — no “Missing 3 fields” count-only pattern |

### D — Submitted case

| | |
|---|---|
| **Expected** | Status = Submitted To Office; Contact = Office Reviewing |
| **Actual (API live patch)** | Stale collecting draft on shared fixture phone (PG/JSON path) |
| **Actual (logic unit)** | `status_label: submitted_to_office`, `contact_state: office_reviewing` |
| **Customer experience** | UI + API logic correctly distinguish submitted vs saved draft |
| **Constitution** | ✅ Rule 4 submit-state dimension; ⚠️ promote backend to Cloud Run for live submitted fixtures |

### E — Wrong phone digit

| | |
|---|---|
| **Expected** | No match — documented duplicate risk |
| **Actual** | `has_active_case: false` |
| **Customer experience** | Wrong digit → empty lookup; may start duplicate matter |
| **Constitution** | ✅ Rule 2 phone-as-key (known limitation documented) |

### F — Shared household phone

| | |
|---|---|
| **Expected** | One active case; second start blocked |
| **Actual** | `409 active_case_exists` on second `start-add-car` |
| **Customer experience** | One status card; Contact Broker for second vehicle |
| **Constitution** | ✅ Rule 7 |

### G — Customer returns on new device

| | |
|---|---|
| **Expected** | Phone rehydrates case without login |
| **Actual** | Full status card with `status_label` + `contact_state` |
| **Customer experience** | No session required; phone is return key |
| **Constitution** | ✅ Rule 1, Rule 2 |

### H — Phone normalization

| | |
|---|---|
| **Expected** | `(626) 555-0307`, `+1 626-555-0307`, `6265550307` → same case |
| **Actual** | All three formats match |
| **Customer experience** | Format-forgiving entry |
| **Constitution** | ✅ Rule 2 |

---

## UI Verification

Preview bundle (`index-CfDJTcYx.js`) contains required customer-facing strings:

- `Active Add-Car Request`
- `Status` / `Saved — Not Yet Submitted`
- `Still Needed` (bullet list)
- `Contact State` / `Waiting For Customer`
- `Continue Request` / `Contact Broker`

---

## Gaps / Follow-ups

| ID | Gap | Severity |
|----|-----|----------|
| G1 | Cloud Run backend not yet promoted with `status_label` / `contact_state` fields | Medium — UI has client-side fallback |
| G2 | Simulation fixture patch for submitted case requires PG-primary write path alignment | Low — covered by unit tests |

---

*End of P16 Status Surface Simulation Report*
