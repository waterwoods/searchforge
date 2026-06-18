# P16 First Broker Test Plan

**For:** Wu Xiaojie (office operator, Chen Kui brokerage)  
**Date:** 2026-06-18  
**Sprint:** P16 Pilot Launch  
**Purpose:** Wu Xiaojie's first hands-on test of the Add-Car intake system.

---

## What This Is

A simple tool that turns messy customer documents into a clean add-car packet.

The customer uploads their paperwork. The system reads it. You get a packet with the VIN, vehicle, ZIP, and all key fields — ready to copy into your AMS or carrier portal.

You don't need to read through WeChat. You don't need to re-ask the customer for their VIN.

---

## 1. What URL to Open

**Open this on your computer or phone:**

```
https://ui-gd6bzzx9v-andys-projects-1f411b73.vercel.app/add-car
```

This is the QA test link. Share it with the customer when they need to add a car.

---

## 2. What to Upload

For this test, use any real add-car case from your queue, or use this test case:

**Test Customer:** Andy Li  
**Vehicle:** 2011 BMW X5  
**Documents to upload:**
- Insurance card (PDF, JPG, or PNG)
- Smog check report (PDF or JPG)
- OR: any purchase agreement, window sticker, or registration

**Accepted file types:** PDF · JPG · PNG · HEIC (iPhone photos)  
**Maximum:** 10 files at once

**Steps:**
1. Open the URL above
2. Enter: Full Name, Phone Number, Garaging ZIP (where the car is kept at night)
3. Upload the documents
4. Click "Continue →"
5. Wait 10–30 seconds while the system reads the documents
6. Review the Trusted Packet

---

## 3. What to Verify

Check each of these when the Trusted Packet appears:

| Item | What to check | Pass condition |
|------|--------------|----------------|
| VIN | Shows VIN with green "VIN Valid" badge | VIN is correct — 17 characters, matches document |
| Vehicle | Year / Make / Model displayed | Matches the actual car |
| Garaging ZIP | Shows the ZIP you entered | Correct — same as what you typed |
| Customer name | Shown at top of packet | Correct |
| Source file | Shows `from: <filename>` next to VIN | You can see which document the VIN came from |
| Warnings | Any yellow warning boxes | If VIN warning shows, verify manually |
| Copy Packet | Click the blue "Copy Packet" button | Success message; paste into a doc to check |

**To check Copy Packet output:** Click "Copy Packet / 复制数据包", then paste into WeChat, Google Docs, or your AMS. The pasted text should show:
```
VIN: [17-character VIN]
Vehicle: [Year Make Model]
ZIP: [Garaging ZIP]
Customer: [Name] — [Phone]
Missing: [any missing fields, or "None"]
Warnings: [any warnings, or "None"]
Sources:
  [filename] → [fields extracted]
```

---

## 4. What Feedback to Collect

After testing, please share your answers to these questions with Andy:

**Must-answer (before we go live):**
1. Did the VIN extract correctly from your documents?
2. Was the Garaging ZIP correct? (This is the ZIP where the car is kept at night — critical for insurance rates)
3. Did the "Copy Packet" button work? Was the copied text usable?
4. Was there anything confusing or wrong on the packet screen?

**Nice to know:**
5. How long did the whole flow take? (from open URL to seeing the packet)
6. Is there any field you always need that's missing from the packet?
7. Would you show this to Chen Kui? What would you change first?

**If something went wrong:**
- Screenshot the error and send to Andy
- Note which screen it failed on (Info / Upload / Reading / Packet)
- Note what documents you uploaded

---

## 5. What Counts as Success

This test **passes** if:

| # | Criterion | Pass |
|---|-----------|------|
| 1 | URL opens and loads | Page loads without error |
| 2 | All 4 steps complete | Info → Upload → Reading → Packet |
| 3 | Packet is visible | Trusted Packet screen shows with customer name |
| 4 | VIN extracted | VIN field is populated (even if validation warning shows) |
| 5 | Copy Packet works | Button copies text to clipboard |
| 6 | Wu Xiaojie says "useful" | She would use this on a real case |

**Bonus pass (not required for first test):**
- Garaging ZIP matches document (if document had ZIP)
- Source attribution visible (which file the VIN came from)
- No mock-mode warning shown

---

## What Happens After Your Test

1. Andy reviews your feedback
2. Any critical issues get fixed same day
3. We schedule 3 real add-car cases (CK-001, CK-002, CK-003) to run through the system
4. After 10 cases: we measure average time saved vs. manual WeChat review
5. If average ≥ 4 minutes saved: first invoice ($49/month)

---

## Contact

Questions or issues: Contact Andy directly.

If the URL doesn't work: Try refreshing. If still broken, let Andy know.

---

*P16 Pilot Test Plan · 2026-06-18*
