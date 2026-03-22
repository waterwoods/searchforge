# Acceptance / Real-Intake Criteria

**Sprint:** Add-Car Real Intake Lite V1  
**Purpose:** Practical criteria for "real enough" add-car.

---

## 1. Reduced Fake/Demo Feel

- [ ] Quote-ready / almost-ready / need-more is visible for add-car
- [ ] Collected vs still-needed is clear during chat and at handoff
- [ ] User can see that real information is being collected (tags during flow)

---

## 2. Minimal But Useful Information Collection

- [ ] P0 fields (vehicle, zip, delivery or driver) collected before handoff
- [ ] VIN optional, not blocking
- [ ] No long form; chat + lightweight structure

---

## 3. Clearer Quote-Ready State

- [ ] quote_ready_status present in triage output for add-car
- [ ] UI shows Quote-ready / Almost ready / Need more for add-car cases
- [ ] Broker can scan status in <3 seconds

---

## 4. Stronger Broker Handoff

- [ ] broker_next_step includes concrete vehicle when extractable
- [ ] broker_next_step is actionable ("Run quote for X. Confirm Y.")
- [ ] Collected and still-needed visible in workbench

---

## 5. Acceptable Simplicity for V1

- [ ] No name/phone extraction required (deferred to V2)
- [ ] No OCR, no quote engine
- [ ] Chat flow preserved; no disconnect from structured intake

---

*See also: 07_FOUNDER_INSPECTION_NOTES.md*
