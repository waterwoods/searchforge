# P16 — Pilot Go-Live Checklist

**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Use before:** First case handed to Chen Kui  
**Format:** Work through top to bottom. Everything must be checked before Go.

---

## Infrastructure

- [ ] `bash scripts/run_demo_local.sh` starts clean on port 8001
- [ ] `bash scripts/trial_launch_check.sh` passes with no P0 failures
- [ ] `UNIFIED_INTAKE_PRODUCT_ONLY=1` set (or confirmed for demo mode)
- [ ] Extraction API key has quota (Gemini Flash 2.5 or gpt-4o fallback)
- [ ] GCS (or local) upload path accepts files

## Upload Flow

- [ ] PDF upload accepted and stored
- [ ] JPG upload accepted and stored
- [ ] PNG upload accepted and stored
- [ ] HEIC upload accepted and converted to JPEG (real iPhone photo tested)
- [ ] File size limit does not block normal dealer PDF (< 10 MB)

## Extraction

- [ ] Upload PDF → extraction returns ≥ 1 field
- [ ] Upload JPG VIN photo → extraction returns VIN
- [ ] Upload HEIC iPhone photo → extraction returns VIN or warning
- [ ] 16-char VIN → "VIN must be 17 characters" warning visible in packet
- [ ] Invalid VIN characters (I/O/Q) → warning visible

## Trusted Packet (Screen 4)

- [ ] VIN visible above fold
- [ ] Year / Make / Model visible above fold
- [ ] Customer name + phone + garaging ZIP visible above fold
- [ ] Source attribution shown per field ("from: [filename]")
- [ ] Warnings section visible before fields (expanded if any warning)
- [ ] Missing fields listed ("Lienholder: not found")
- [ ] Field label reads "Garaging ZIP" (not "Address" or "ZIP Code")

## Copy All

- [ ] "Copy All Fields" button works (clipboard filled)
- [ ] Paste into plain text produces readable field-label: value lines
- [ ] No JSON brackets or raw object output in clipboard

## End-to-End Smoke

- [ ] Intake form → upload 3 files → extract → packet → copy → total time < 3 minutes
- [ ] No console errors or UI crash during smoke run

## Pilot Handoff

- [ ] Chen Kui has the intake URL
- [ ] Wu Xiaojie has `P16_CHEN_KUI_3_CASE_SOFT_PILOT.md` instructions
- [ ] `docs/trial/P16_TIME_SAVINGS_TRACKER.md` ready to log CK-001
- [ ] Andy reachable during first 3 cases (same-day response)
- [ ] Escalation path confirmed: silent wrong VIN = STOP pilot immediately

---

**GO** = all boxes checked  
**NO-GO** = any unchecked item in Infrastructure, Upload Flow, Extraction, or Trusted Packet sections

*Authority: `docs/p16/P16_DECISION_FREEZE_V1.md`*
