# P16 Andy Walkthrough — 5-Screen Personal Test

**Date:** 2026-06-18  
**Tester:** Andy Li  
**URL:** https://ui-gd6bzzx9v-andys-projects-1f411b73.vercel.app/add-car  
**Backend:** https://fiqa-api-1013093472160.us-west1.run.app  
**Purpose:** Andy personally tests all 5 screens before sending to Wu Xiaojie.

---

## How to Use This Doc

Walk through each screen. For each one, fill in:
- **What feels good?** — moments of confidence
- **What feels confusing?** — friction, unclear copy, unexpected behavior
- **What feels unfinished?** — things a professional product would have
- **What feels untrustworthy?** — things that would make Chen Kui / Wu Xiaojie hesitate

Fill in your answers in the OBSERVATIONS section for each screen.

---

## Screen 1 — Entry Gate / Add-Car Intake Header

**What you see:**  
The top of the page at `/add-car`. Page title: "Add-Car Intake". Subtitle: "上传客户文件 → Trusted Packet → 复制到运营商系统". A 4-step progress bar (Info · Upload · Reading · Packet) with Step 1 active. The InfoStep card is already visible.

**Designed to communicate:**  
- You are in the right place (add-car, not the broker workbench)
- There are exactly 4 steps
- The purpose is: upload documents → get a packet to copy

**OBSERVATIONS — Screen 1:**

| Question | Notes |
|----------|-------|
| What feels good? | |
| What feels confusing? | |
| What feels unfinished? | |
| What feels untrustworthy? | |

---

## Screen 2 — Customer Info (InfoStep)

**What you see:**  
Card with title "Your Information" / "客户基本信息". Three required fields: Full Name, Phone Number, Garaging ZIP. Garaging ZIP has a tooltip explaining it. CTA: "Next — Upload Documents →".

**Designed to communicate:**  
- We need 3 pieces of info before reading documents
- Garaging ZIP = where the car is parked at night (with tooltip)
- This is the customer's own screen (copy says "Your Information")

**Test it:**  
Enter: Full Name = `Andy Li`, Phone = `6265550000`, Garaging ZIP = `91101`. Press Next.

**OBSERVATIONS — Screen 2:**

| Question | Notes |
|----------|-------|
| What feels good? | |
| What feels confusing? | |
| What feels unfinished? | |
| What feels untrustworthy? | |

---

## Screen 3 — Upload Documents (UploadStep)

**What you see:**  
Card with title "Upload New Car Paperwork" / "上传新车资料". List of accepted document types (Purchase Agreement, Window Sticker, Registration, VIN photo, Insurance card). Drag-and-drop area. CloudUpload icon. Accepted: PDF · JPG · PNG · HEIC | Up to 10 files. After adding files: green "X file(s) ready" alert. CTA: "Continue →".

**Designed to communicate:**  
- Upload any combination of these 5 document types
- Files are accepted without uploading to server yet (client-only until you press Continue)
- Mobile camera roll / HEIC is supported

**Test it:**  
Upload the insurance card + smog report files you've previously tested.

**OBSERVATIONS — Screen 3:**

| Question | Notes |
|----------|-------|
| What feels good? | |
| What feels confusing? | |
| What feels unfinished? | |
| What feels untrustworthy? | |

---

## Screen 4 — Extracting (ExtractingStep)

**What you see:**  
Card with title "Reading your documents…" / "正在读取您的文件". An animated 4-step progress list with smooth transitions:  
1. Upload Complete — Done (green check)  
2. Reading Documents — In progress (blue spinner)  
3. Extracting Vehicle Data — pending (grey circle)  
4. Building Trusted Packet — pending (grey circle)  

Duration: 10–30 seconds. The Ant Design Steps bar shows step 3 of 4 active.

**Designed to communicate:**  
- Something real is happening (not a crash / infinite spinner)
- We know how far along we are
- Expected wait time is stated

**Test it:**  
Watch the animation sequence. Note actual elapsed time until packet appears.

**OBSERVATIONS — Screen 4:**

| Question | Notes |
|----------|-------|
| What feels good? | |
| What feels confusing? | |
| What feels unfinished? | |
| What feels untrustworthy? | |

---

## Screen 5 — Trusted Packet (PacketStep)

**What you see (above the fold):**  
- Green checkmark + "Trusted Packet" title + timestamp (e.g., "Jun 18, 2026, 3:04 PM")  
- Customer name (large)  
- VIN pill (green "VIN Valid" or yellow "VIN Warning" or red "VIN Missing") + VIN code + `from: <filename>`  
- Warnings (if any) — shown BEFORE vehicle fields  
- Missing fields callout (if applicable)  
- Divider  
- Vehicle label (e.g., "2011 BMW X5")  
- Garaging ZIP  
- **"Copy Packet / 复制数据包"** button (primary, full-width)  

**Below the fold:**  
- "Show field details (source & confidence)" toggle → expands to show Customer / Vehicle / Coverage Details tables with source file + confidence labels  
- "Start Over / 重新开始" button  

**Test it:**  
1. Read the packet. Is the data correct?  
2. Click "Copy Packet". Paste into a blank doc. Read the output.  
3. Click "Show field details". Check source attribution.  
4. Note: mock mode banner should NOT appear (only shows in DEV builds, not Vercel deploys).

**OBSERVATIONS — Screen 5:**

| Question | Notes |
|----------|-------|
| What feels good? | |
| What feels confusing? | |
| What feels unfinished? | |
| What feels untrustworthy? | |

---

## Copy Packet Output Template

After clicking "Copy Packet", you should see output like:

```
VIN: 5UXFE43529L000000
Vehicle: 2011 BMW X5
ZIP: 91101
Customer: Andy Li — 6265550000
Missing: Primary Driver, Effective Date
Warnings: None
Sources:
  insurance_card.jpg → vin, year, make, model
  smog_report.pdf → vin
```

**Questions to answer:**
- Is the VIN correct?
- Is the vehicle year/make/model correct?
- Is the garaging ZIP correct?
- Would you paste this directly into an AMS/carrier portal?
- Is there anything in the output that would confuse a non-technical broker?

---

## Overall Assessment

| Metric | Rating (1–10) | Notes |
|--------|--------------|-------|
| Screens 1–5 feel complete | | |
| Data is accurate | | |
| Copy Packet is usable | | |
| Flow is under 3 minutes | | |
| Trust level for broker | | |
| **Total** | | |

**GO / NO-GO for Wu Xiaojie test:** ___________

**Blockers before sending to Wu Xiaojie:**
- [ ]
- [ ]
- [ ]

**Nice-to-have (P1, not blocking):**
- [ ]
- [ ]

---

*Doc generated: 2026-06-18 | P16 Pilot Launch Sprint*
