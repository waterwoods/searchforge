# P16 — 72-Hour Pilot Demo Build Plan

**Date:** 2026-06-18  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Goal:** Pilot Demo ready for Chen Kui and Wu Xiaojie — not a production platform.  
**Pilot:** 3-case soft pilot (`docs/p16/P16_CHEN_KUI_3_CASE_SOFT_PILOT.md`)

---

## North Star

```
Customer Docs  →  Trusted Packet  →  Broker  →  Save Time  →  First Payment
```

Every hour of work this week maps to one of these five steps or it does not happen.

---

## Scope Decision

### MUST HAVE

| # | Item | Why |
|---|------|-----|
| M1 | HEIC real iPhone validation (end-to-end) | Top unresolved risk; iPhone is dominant upload device |
| M2 | Screen 4 Trusted Packet hierarchy (above-fold visible fields) | First thing Wu Xiaojie sees — must be scannable in 5 sec |
| M3 | VIN length warning visible in UI (16-char failure) | Already in backend; confirm frontend shows it clearly |
| M4 | Source attribution visible per field (file name shown) | Trust mechanism; required per Decision Freeze §3 |
| M5 | Copy Packet one-click works | Broker action; required per Decision Freeze §6 |
| M6 | Garaging ZIP wording correct ("Garaging ZIP" not "Address") | Correct field label for broker; avoids compliance confusion |
| M7 | Local demo runs clean (`run_demo_local.sh`) | Without this there is no demo |

### SHOULD HAVE

| # | Item | Why |
|---|------|-----|
| S1 | Copy All format verified (fields land cleanly in AMS/clipboard) | Wu Xiaojie's output step |
| S2 | Warnings section visible before fields section in packet | Warning-first design; catches bad VIN before broker proceeds |
| S3 | "Missing fields" section in packet (lienholder, delivery date) | Broker knows what to ask the customer |
| S4 | Trade-in multi-VIN flag fires (`second_vehicle_detected`) | Narrow risk; worth confirming before pilot |

### NICE TO HAVE

| # | Item | Why |
|---|------|-----|
| N1 | Packet print/email layout | Broker polish; not needed for 3 cases |
| N2 | Case numbering displayed in UI (CK-001 style) | Nice audit trail; manual log covers it |
| N3 | Status page showing extraction progress | Good UX; not blocking |

### DO NOT BUILD

| Item | Reason |
|------|--------|
| PDF export | Deferred per Decision Freeze §4; broker copies fields |
| Customer confirmation screen | Deferred per Decision Freeze §4 |
| WeChat integration | Deferred per Decision Freeze §4 |
| Trade-in automation | Deferred; flag only for V0 |
| Authentication system | Out of scope; API keys only |
| Multi-broker / multi-tenant | Out of scope for single pilot |
| CRM integration | Out of scope |
| Document AI / alternate extraction | Gemini Flash 2.5 frozen; switch only if Gemini fails |
| Status visibility polish (append/demo tab) | Out of Trust Layer Sprint per freeze |
| Any new screen not in Screens 1–4 | Scope boundary |

---

## Screen 4 — Trusted Packet Design

### Above the fold (first 5 seconds — Wu Xiaojie sees this before any scroll)

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ TRUSTED PACKET — CK-001                                  │
│  Customer: [Name] · [Phone] · Garaging ZIP: [ZIP]           │
│                                                              │
│  ⚠️  WARNINGS  (collapsed if zero, expanded if any)         │
│  → VIN needs confirmation (16 chars found — must be 17)     │
│                                                              │
│  VIN         [17-char VIN]         [source: pa_001.pdf]     │
│  Year        [YYYY]                [source: ws_001.pdf]     │
│  Make/Model  [Make Model]          [source: ws_001.pdf]     │
│                                                              │
│  [ COPY ALL FIELDS ]                                        │
└─────────────────────────────────────────────────────────────┘
```

**Default visible (above fold):**
- Case header with customer name + phone + garaging ZIP
- Warnings section (expanded if any warning, collapsed if clean)
- VIN / Year / Make / Model with source attribution
- Copy All button

**Default collapsed:**
- Lienholder (optional; most cases do not have it)
- Delivery / effective date
- Primary driver (separate from customer)
- Raw extraction JSON (debug only)

### Middle section (scroll — first 30 seconds)

- Missing fields list ("Lienholder: not found — ask customer if financed")
- All extracted fields with source file attribution
- Document type badge per uploaded file

### Bottom section (reference)

- Uploaded files list (name, type, page count)
- Extraction confidence signals (if field confidence < threshold)
- Case ID and timestamp

### Wu Xiaojie — first 5 seconds

She sees: customer name, garaging ZIP, VIN, Year/Make/Model, any warnings, Copy button.
She does **not** need to scroll to act. If there are no warnings, she copies and pastes immediately.

### Wu Xiaojie — first 30 seconds

She reviews missing fields, checks source attribution on VIN, confirms no conflict warnings.
If everything is clean she is done. If there is a VIN warning she flags it to Chen Kui.

---

## Day 1 — Wednesday Jun 18 (Hours 1–24)

**Theme: HEIC + Packet Hierarchy**

| # | Task | Priority | Done when |
|---|------|----------|-----------|
| 1.1 | Real iPhone HEIC upload test — photograph a physical VIN (door jamb or dashboard) | P0 | JPEG conversion verified; extraction returns VIN |
| 1.2 | Confirm HEIC → JPEG conversion log output (pillow-heif path) | P0 | `HEIC→JPEG` log line visible |
| 1.3 | Test HEIC extraction with live Gemini Flash 2.5 key (or gpt-4o fallback) | P0 | VIN extracted from real iPhone photo |
| 1.4 | Define HEIC PASS/FAIL/GO/NO-GO criteria (see below) | P0 | Criteria documented + tested |
| 1.5 | Screen 4 — implement above-fold layout per design above | P0 | Warnings visible before fields; Copy button above fold |
| 1.6 | Garaging ZIP label audit — confirm all UI text says "Garaging ZIP" not "Address" | P1 | Zero occurrences of wrong label in intake + packet |
| 1.7 | End-of-day smoke: upload 1 HEIC + 1 PDF + 1 JPG → packet generated | P0 | All 3 file types produce a packet |

**End of Day 1 acceptance:** HEIC GO/NO-GO decision made. Screen 4 above-fold complete.

---

## Day 2 — Thursday Jun 19 (Hours 25–48)

**Theme: Copy All + Warnings + Integration smoke**

| # | Task | Priority | Done when |
|---|------|----------|-----------|
| 2.1 | Copy All — verify clipboard format is clean (no JSON brackets; field-label: value lines) | P0 | Paste into Google Docs shows readable fields |
| 2.2 | VIN length warning — confirm 16-char VIN shows "VIN must be 17 chars" in packet warnings | P0 | Manual test with truncated VIN input |
| 2.3 | Source attribution — confirm each field shows "(from: [filename])" in Screen 4 | P0 | All core fields have source shown |
| 2.4 | Missing fields section — "Lienholder: not found" visible when lienholder absent | P1 | Missing items listed below extracted fields |
| 2.5 | Trade-in multi-VIN: upload `dw_002_buyers_order.pdf` + one other doc, confirm conflict flag | P1 | Warning fires; no silent second VIN |
| 2.6 | Full flow test: intake form → upload 3 docs → extract → packet → copy → paste | P0 | End-to-end under 3 minutes; no errors |
| 2.7 | End-of-day smoke: run `demo_quick_validate.sh` clean | P0 | Zero failures |

**End of Day 2 acceptance:** Copy All works clean. All warnings visible. Full flow < 3 min.

---

## Day 3 — Friday Jun 20 (Hours 49–72)

**Theme: Pilot readiness hardening + Chen Kui handoff**

| # | Task | Priority | Done when |
|---|------|----------|-----------|
| 3.1 | Run `trial_launch_check.sh` — fix any blocking failures | P0 | Script passes clean |
| 3.2 | Run `founder_pre_trial_checklist.sh` — resolve all P0 items | P0 | Checklist green |
| 3.3 | Dry-run CK-001 with a real (or simulated) case using real doc types | P0 | Packet generated; time < 3 min |
| 3.4 | Prepare handoff: intake URL ready, Chen Kui walkthrough doc ready | P0 | URL accessible; doc exists |
| 3.5 | Log dry-run in `docs/trial/P16_TIME_SAVINGS_TRACKER.md` as CK-DRY-01 | P1 | Entry exists with time recorded |
| 3.6 | Go/No-Go call: review PILOT_READINESS_SCORE (see below) | P0 | Score ≥ 8 → ship; < 8 → block and fix |
| 3.7 | If GO: send intake link to Chen Kui with case instructions | P0 | Chen Kui has URL + pilot doc |

**End of Day 3 acceptance:** Pilot launched or explicit NO-GO with blocking reason documented.

---

## HEIC Readiness — Pass/Fail/Go/No-Go Criteria

### What must be tested on a real iPhone

1. Take a photo of a real VIN plate (door jamb sticker or dashboard plaque) with iPhone camera
2. Upload the `.heic` file directly from iPhone camera roll via the intake UI
3. Observe: does the upload succeed? Does the packet return a VIN?

### PASS

- Upload accepted (no file type rejection)
- HEIC → JPEG conversion logged without error
- Gemini (or gpt-4o) returns a VIN string from the photo
- VIN string is 17 characters OR length warning fires correctly

### FAIL

- Upload rejected (MIME type error, 400 response)
- Conversion throws exception (pillow-heif failure)
- Extraction returns null/empty with no warning shown to broker
- VIN is 17 chars but visibly wrong (character misread) with no warning

### GO

- PASS criteria met on ≥ 1 real iPhone photo
- Manual fallback (re-send as JPG) documented and tested

### NO-GO

- Any FAIL on real iPhone where broker sees no warning and would proceed with bad data
- Upload error crashes the form (no graceful error message)

**If NO-GO:** Fix pillow-heif conversion, add graceful error message, retest before pilot.

---

## Pilot Success Definition — Per Case

### Case #1 (first real broker add-car)

| Outcome | Criteria |
|---------|----------|
| **Success** | Packet generated in < 60 sec; VIN correct or warning shown; Wu Xiaojie says "usable without re-reading WeChat" |
| **Warning** | Packet generated but 1 field missing or wrong with warning visible; Wu Xiaojie needed to re-check 1 field |
| **Failure** | Wrong VIN silently in packet with no warning; extraction returns empty; UI crashes |

### Case #2

| Outcome | Criteria |
|---------|----------|
| **Success** | Same as #1; time-saved ≥ 3 minutes vs manual |
| **Warning** | Time saved 1–2 min; 1 non-critical field missing |
| **Failure** | Any critical issue from Case #1 definition |

### Case #3

| Outcome | Criteria |
|---------|----------|
| **Success** | 2 of 3 cases "usable without WeChat" + average ≥ 3 min saved → proceed to 10-case gate |
| **Warning** | 1 of 3 "usable without WeChat" — investigate friction before proceeding |
| **Failure** | 0 of 3 usable, OR any silent wrong VIN in any case → STOP, fix, restart |

### Measurable metrics per case

| Metric | Target |
|--------|--------|
| Upload → packet time | < 60 seconds |
| Wu Xiaojie "usable without WeChat" | YES or MOSTLY |
| Time saved vs manual | ≥ 3 minutes |
| Silent wrong VIN occurrences | 0 |
| System crash / no output | 0 |

---

## Acceptance Criteria (end of 72 hours)

All six from Decision Freeze §8 must pass:

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 1 | Upload works | Customer uploads ≥1 file; stored in GCS (or local for demo) |
| 2 | Extraction works | Gemini (or gpt-4o) returns ≥1 structured field |
| 3 | Packet generated | Trusted Packet visible with required fields |
| 4 | Copy Fields works | Copy to clipboard works; paste is clean text |
| 5 | Source file shown | Each field shows originating filename |
| 6 | VIN warning shown | 16-char or invalid VIN shows visible warning |

Plus pilot-specific additions:

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 7 | HEIC works | Real iPhone photo → VIN extracted or warning shown |
| 8 | Screen 4 above-fold | Warnings + VIN + Copy button visible without scroll |
| 9 | Garaging ZIP label | "Garaging ZIP" — not "Address" or "ZIP Code" |
| 10 | Full flow < 3 min | Intake to copied packet in under 3 minutes |

---

## Stop Criteria

**Stop all work and escalate if:**

- Any path produces a silent wrong VIN (17-char but incorrect, no warning)
- HEIC upload crashes the UI with no error message (NO-GO condition)
- Extraction API (Gemini + gpt-4o) is completely unavailable with no fallback
- `trial_launch_check.sh` has P0 failures that cannot be resolved in < 2 hours

---

## Pilot Handoff Checklist

- [ ] Intake URL accessible from Chen Kui's phone and desktop
- [ ] `P16_CHEN_KUI_3_CASE_SOFT_PILOT.md` sent to Chen Kui and Wu Xiaojie
- [ ] Time savings tracker ready: `docs/trial/P16_TIME_SAVINGS_TRACKER.md`
- [ ] HEIC tested on real iPhone — GO confirmed
- [ ] VIN warning tested — shows on 16-char VIN
- [ ] Copy All tested — clean paste in Google Docs or AMS
- [ ] Source attribution visible for all core fields
- [ ] `trial_launch_check.sh` passes
- [ ] Andy reachable for first 3 cases (same-day response on issues)
- [ ] Escalation path documented: wrong VIN = STOP pilot immediately

---

*Authority: `docs/p16/P16_DECISION_FREEZE_V1.md`*  
*Pilot package: `docs/p16/P16_CHEN_KUI_3_CASE_SOFT_PILOT.md`*  
*Revenue milestone: Decision Freeze §9*
