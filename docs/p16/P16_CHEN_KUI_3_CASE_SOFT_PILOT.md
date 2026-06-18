# P16 — Chen Kui 3-Case Soft Pilot

**Date:** 2026-06-17  
**Sprint:** P16 Readiness Fix Sprint  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Pilot contact:** Chen Kui (broker), Wu Xiaojie (office operator)  
**Case IDs:** CK-001, CK-002, CK-003  

---

## 1. Pilot Goal

Confirm that P16 reduces add-car intake work from **~10 minutes to ~2–3 minutes** on real broker cases.

Three cases is enough to:
- Confirm the upload + extraction + packet flow works on real customer documents
- Give Wu Xiaojie a basis for judging time savings
- Identify any real-world failure patterns not caught in synthetic testing
- Build confidence for Chen Kui to continue to the 10-case gate

This is a **soft pilot** — no billing, no commitment, just logging and feedback.

---

## 2. How to Run Each Case

### Step 1 — Receive add-car request from customer

When a customer sends an add-car request (via WeChat, email, or text), before doing
any manual work, open the P16 intake flow.

### Step 2 — Open the intake flow

Go to the Add-Car page in the broker portal:

```
http://localhost:8001/add-car
```

(or production URL if deployed)

### Step 3 — Enter customer info (Step 1 of wizard)

Fill in:
- **Full Name** — customer's legal name
- **Phone Number** — customer's phone
- **Garaging ZIP** — where the new vehicle will be kept

Click "Next — Upload Documents".

### Step 4 — Upload documents (Step 2 of wizard)

Upload everything the customer sent:
- PDF purchase agreement (if provided)
- Window sticker photo (JPG/PNG/HEIC)
- Registration card (JPG/PDF)
- VIN photo from iPhone (HEIC/JPG)
- WeChat screenshots of VIN or delivery date
- Any other supporting documents

Drag or click to add files. Click "Extract Packet".

### Step 5 — Review the Trusted Packet (Step 3 of wizard)

The packet shows:
- Extracted VIN (with source file)
- Year / Make / Model
- Garaging ZIP
- Customer name and phone
- Warnings (if any)

**Check the warnings section first.** Any VIN issues appear there immediately.

### Step 6 — Copy and use

Click "Copy Packet" to copy all fields to clipboard.
Paste into AMS system or carrier portal.

### Step 7 — Log the case

Record in `docs/trial/P16_TIME_SAVINGS_TRACKER.md`:
- Case ID (CK-001, CK-002, CK-003)
- Time with P16 (from receiving request to copying packet)
- Estimated time without P16 (based on Wu Xiaojie's usual approach)
- Minutes saved
- Any issues encountered

---

## 3. What Chen Kui Should Test

Chen Kui is the broker — the person who reviews and acts on the packet.

For each case, Chen Kui should check:

| # | Check | What to look for |
|---|-------|-----------------|
| 1 | VIN accuracy | Does the VIN in the packet match the car? Cross-check against dealer paper or registration. |
| 2 | Year / Make / Model | Is the vehicle correct? No wrong model year? |
| 3 | Warnings visible | If VIN had issues, did the system flag it? |
| 4 | Source attribution | Does each field show which file it came from? |
| 5 | Copy to AMS | Did the Copy Packet text paste cleanly into the carrier portal / AMS? |
| 6 | Time | How long did it take vs. manually reading through WeChat? |

Chen Kui does **not** need to re-read WeChat threads. If the packet has warnings, resolve
them by asking the customer — not by digging through chat history.

---

## 4. What Wu Xiaojie Should Judge

Wu Xiaojie is the office operator — the person who normally hunts through WeChat for fields.

For each case, Wu Xiaojie should answer:

| Question | Scale |
|----------|-------|
| Was the intake packet usable without re-reading WeChat? | Yes / Mostly / No |
| Did you have to manually hunt for any field? | Which fields? |
| How many minutes did this case take WITH the tool? | __ min |
| How many minutes would this case take WITHOUT the tool? | __ min |
| Did the system surface anything you would have missed? | Yes / No |
| Would you use this for the next add-car request? | Yes / Maybe / No |

---

## 5. What Counts as Success

### Case-level success (each individual case):

- Packet generated in < 60 seconds after uploading files
- VIN extracted correctly OR VIN warning shown if extraction failed
- At least Year + Make + Model correct
- Wu Xiaojie can copy fields to AMS without re-reading customer's WeChat

### Pilot-level success (3 cases total):

- 2 of 3 cases: Wu Xiaojie says "usable without re-reading WeChat"
- 2 of 3 cases: at least 3 minutes saved vs. manual workflow
- Zero cases: wrong VIN silently appeared in packet without a warning
- Zero cases: system crashed or gave no output at all

If these conditions are met, proceed to the 10-case gate.

---

## 6. What Counts as Failure

| Failure type | Severity | Action |
|-------------|----------|--------|
| Wrong VIN in packet with NO warning | **Critical** — STOP pilot | File bug, fix warning, retest before continuing |
| Extraction returns completely empty packet | **High** — log and continue | Check API key; use manual fallback for this case |
| HEIC upload fails (iPhone photo rejected) | **Medium** | Ask customer to resend as JPG for this case |
| VIN warning shows but broker can still proceed | **Low** — expected | This is working as designed |
| Packet completeness < 100% due to missing optional fields | **Low** — expected | Optional fields (lienholder, primary driver) not always in docs |

---

## 7. Time Savings Log

Use this format for each case in `docs/trial/P16_TIME_SAVINGS_TRACKER.md`:

```
CK-001
  Date: ___________
  Customer docs submitted: ___________
  Doc types uploaded: ___________
  Time to packet (upload → copy): ___ min
  Estimated manual time: ___ min
  Minutes saved: ___ min
  VIN correct: YES / NO / WARNING SHOWN
  Issues encountered: ___________
  Wu Xiaojie: usable? YES / MOSTLY / NO

CK-002
  ...

CK-003
  ...
```

---

## 8. Broker Feedback Questions

After 3 cases, Chen Kui should answer:

**Product:**
1. Did the tool save you meaningful time compared to doing this manually?
2. Did you trust the extracted VIN enough to use it, or did you always double-check?
3. Were the warnings clear when something was wrong?
4. What was the most annoying part of using the tool?

**Workflow:**
5. Would you send a customer directly to the upload link, or do you prefer to upload documents yourself?
6. Is 2–3 minutes a meaningful improvement over your current process?
7. What document type caused the most trouble?

**Commercial:**
8. If this consistently saved 4–8 minutes per add-car request, would you pay $49/month?
9. What would make you confident enough to recommend this to another broker?

---

## 9. Escalation Path

If any Critical failure occurs (wrong VIN, no warning):

1. Stop the pilot immediately
2. Document the case (doc type, expected VIN, extracted VIN, what the system showed)
3. File as P16 blocking bug
4. Fix and re-verify before resuming

Do not continue the pilot if a wrong VIN was silently used.

---

## 10. After 3 Cases

If pilot success conditions are met:

- Proceed to 10-case gate (CK-004 … CK-010)
- Log all 10 cases in `docs/trial/P16_TIME_SAVINGS_TRACKER.md`
- If average ≥ 4 minutes saved across 10 cases: generate first $49 invoice

If pilot reveals issues:

- File specific bugs against P16 backlog
- Resolve blocking issues before expanding to 10 cases
- Do not invoice until 10-case gate is passed

---

*Pilot package authored 2026-06-17.*  
*SSOT: `docs/p16/P16_DECISION_FREEZE_V1.md`*  
*Revenue milestone chain: `docs/p16/P16_DECISION_FREEZE_V1.md §9`*
