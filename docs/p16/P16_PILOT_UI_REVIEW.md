# P16 Pilot UI Review — Add-Car Flow (5 Screens)

**Date:** 2026-06-18  
**Reviewer:** Cursor Agent (P16 Polish Sprint)  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Source files audited:** `ui/src/features/intake/components/CustomerFirstEntryScreen.tsx`, `ui/src/pages/AddCarPage.tsx`, `ui/src/features/intake/components/CustomerEntryTab.tsx`  
**Goal:** Broker-facing pilot demo readiness — Chen Kui and Wu Xiaojie as primary audience.

---

## Scoring Method

Each screen scored 0–10 across four dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Clarity** | Does the user immediately know what to do and why? |
| **Trust** | Does the screen feel safe, real, and official? |
| **Professionalism** | Does it look like a paid product or an engineer demo? |
| **Mobile Usability** | Would a customer on an iPhone complete this without friction? |

---

## Screen 1 — CustomerFirstEntryScreen (Entry Gate)

**Route:** UnifiedIntakePage → CustomerEntryTab  
**Component:** `CustomerFirstEntryScreen.tsx`  
**What it does:** First touchpoint. Customer enters phone + optional name. System checks for existing active cases. "Return key" identity model.

### Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Clarity | **8 / 10** | "No account required. No password required. Return anytime using your phone number." is crystal clear. Purpose is obvious. |
| Trust | **8 / 10** | The 3-bullet trust list inside a soft gradient card (green→blue) actively reassures. "No login" is exactly the right message for this audience. |
| Professionalism | **6 / 10** | Title "Add-Car Request" reads like internal jargon, not a customer product. No logo, no company name, no product identity. |
| Mobile Usability | **8 / 10** | Single-column card, large `size="large"` inputs, phone `inputMode="tel"`, `autoFocus` on phone field. Strong mobile UX. |

**Overall Screen 1: 7.5 / 10**

### What creates trust
- Explicit "No account required" and "No password required" bullets eliminate a major barrier for Chinese-American customers unfamiliar with online insurance intake
- Gradient card (f6ffed → e6f4ff) is calm and professional, not alarming
- "Return anytime using your phone number" reduces risk of abandonment

### What creates confusion
- "Add-Car Request / 加车申请" is the title — sounds like a form, not a service entry
- No context for *why* phone is the return key ("your case number will always be your phone number")
- Name is marked optional but then appears again as required on Screen 2 — creates duplicate entry perception

### What feels unfinished
- No product name, no logo, no "Powered by [brokerage]" attribution
- No "what happens next" preview ("You'll upload your car documents and we'll read them automatically")
- Placeholder phone format `(626) 555-0100` assumes US area code knowledge

### What looks like an engineer demo
- The internal term "Return key: [phone]" appearing later in the ActiveCaseCard is backend language surfaced to customer
- Phase labels (`active_exists`, `blocked_second_vehicle`) are internal and would leak if displayed accidentally

### What looks professional
- The gradient welcome box is the most polished element in the entire flow
- Bilingual labels throughout feel thoughtful, not thrown in
- The `no_active` sub-state ("Start New Add-Car Request") flows cleanly

---

## Screen 2 — InfoStep (Customer Information Form)

**Route:** `/add-car` (AddCarPage wizard, step 0)  
**Component:** `AddCarPage.tsx` → `InfoStep`  
**What it does:** Collects customer name, phone, and garaging ZIP before upload.

### Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Clarity | **7 / 10** | Fields are unambiguous. Garaging ZIP has tooltip explaining insurance relevance. ZIP label is long but accurate. |
| Trust | **5 / 10** | Looks like a generic government form. No explanation of what this data is used for. No security/privacy signal. |
| Professionalism | **6 / 10** | Clean Ant Design card but anonymous — no logo, no "submitted to [brokerage] office" attribution. |
| Mobile Usability | **7 / 10** | `maxWidth: 480` works on mobile. `size="large"` inputs. ZIP `maxLength={10}` prevents runaway input. |

**Overall Screen 2: 6.25 / 10**

### What creates trust
- ZIP tooltip explains "affects insurance rates" — this is actually excellent; it explains *why* the system needs the field
- Bilingual labels show the product was built for this community
- `requiredMark={false}` keeps the form clean (no red asterisks cluttering labels)

### What creates confusion
- Title "Customer Information / 客户基本信息" is in the *broker's voice*, not the customer's. To the customer, this is "Your Information."
- If customer came through CustomerFirstEntryScreen, they already entered phone on Screen 1. They now see it again as a required field on Screen 2. This creates "wait, did I already do this?" doubt.
- ZIP label: "ZIP code where the car stays at night / 车辆晚上停放的邮编" — the English is casual but the Chinese is accurate. The label is awkward for a US customer who just bought a car.

### What feels unfinished
- No "why we need this" micro-copy beneath the form
- No back button visible on Screen 2 (no `← Back` to CustomerFirstEntryScreen)
- Placeholder "e.g. Chen Kui" should not use the broker's own name (use a neutral example like "e.g. Li Hua")

### What looks like an engineer demo
- The Steps bar still shows `description: '客户信息'` — this description is visible only in English context but was left as Chinese
- `autoComplete="name"` and `autoComplete="tel"` are correct but the form reads as a database intake form, not a product

### What looks professional
- The "Next — Upload Documents →" CTA text is the best CTA in the flow — directional, clear, action-first
- Form validation messages are brief and helpful

---

## Screen 3 — UploadStep (Upload New Car Paperwork)

**Route:** `/add-car` (AddCarPage wizard, step 1)  
**Component:** `AddCarPage.tsx` → `UploadStep`  
**What it does:** Customer uploads PDFs, photos, HEIC from their car purchase.

### Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Clarity | **7 / 10** | Document type list (Purchase Agreement, Window Sticker, Registration, VIN photo, Insurance card) is genuinely helpful. Upload area is clear. |
| Trust | **5 / 10** | Nothing explains what happens to the uploaded files ("uploaded securely to your broker's system" would help). |
| Professionalism | **5 / 10** | `InboxOutlined` icon (email inbox) is wrong for file upload. "Read Documents" CTA is engineer language. |
| Mobile Usability | **6 / 10** | Dragger area works but drag-and-drop is desktop UX; mobile tap works. HEIC listed in accept but visual prominence of iPhone-first flow is weak. |

**Overall Screen 3: 5.75 / 10**

### What creates trust
- "Upload any of the following:" with a structured list tells the customer exactly what's needed
- Bilingual document type labels show cultural awareness
- File count limit (10) and type validation with clear error messages are good guardrails

### What creates confusion
- `InboxOutlined` icon (📥 email inbox shape) sends the wrong signal — this is a file upload, not email
- "Read Documents (2 files)" on the CTA button — "Read" is the system's internal verb, not the customer's mental model. "Analyze" or "Process" or simply "Continue" is clearer.
- The info alert "Upload at least one document to read vehicle fields" uses "read vehicle fields" — this is backend language
- `maxWidth: 560` on Screen 3 vs `maxWidth: 480` on Screen 2 creates layout inconsistency

### What feels unfinished
- No confidence message when files are added ("2 files ready ✓ — good to go")
- No "what happens to my documents" micro-copy
- No mobile-specific hint ("iPhone users: share directly from Photos or Files app")
- Extraction steps are invisible to customer during this screen

### What looks like an engineer demo
- Error messages use file extension names in technical format (`unsupported type. Use PDF, JPG, PNG, or HEIC.`) — a production product would say "Please use a supported photo or document format"
- The placeholder text "Click or drag files here / 点击或拖拽文件" is functional but generic

### What looks professional
- The `← Back` / `Read Documents (N files)` button pair is clean — the disabled state on the CTA until files are present is correct UX
- The bilingual document list with parenthetical Chinese is genuinely production-quality

---

## Screen 4 — ExtractingStep (Reading Your Documents)

**Route:** `/add-car` (AddCarPage wizard, step 2 — "Reading")  
**Component:** `AddCarPage.tsx` → `ExtractingStep`  
**What it does:** System reads uploaded files with Gemini Flash 2.5. 10–30 seconds. Customer waits.

### Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Clarity | **7 / 10** | "Reading your documents…" is correct language. "10–30 seconds" sets expectation. "Finding VIN, year, make, model…" is exactly right. |
| Trust | **4 / 10** | Bare Ant Design spinner with no visual substance makes the product feel like it might have crashed. Nothing signals "AI is actively working." |
| Professionalism | **3 / 10** | This is the weakest screen in the flow. It looks like a loading state from a college project. Competitors show animated progress steps. |
| Mobile Usability | **8 / 10** | Centered single-column, minimal content — technically fine on mobile. |

**Overall Screen 4: 5.5 / 10**

### What creates trust
- "Finding VIN, year, make, model…" is the right language — it tells the customer what the system is extracting
- "This usually takes 10–30 seconds" prevents premature abandonment

### What creates confusion
- No progress signal whatsoever — a 30-second blank spinner with "Loading" is indistinguishable from a network error
- Nothing tells the customer what to do if it takes longer ("If it takes more than 60 seconds, the page will show an error — you can try again")

### What feels unfinished
- No animated step indicators ("Reading Purchase Agreement… Reading VIN photo…")
- No progress bar or step count
- The card has `padding: '40px 24px'` explicitly — the padding feels like it was guessed, not designed

### What looks like an engineer demo
- `<Spin size="large" />` alone is literally the default loading state from every tutorial
- No typography hierarchy within the card — the three text lines all have the same secondary color weight

### What looks professional
- The bilingual copy ("正在读取您的文件…") is consistent with the rest of the flow

---

## Screen 5 — PacketStep (Trusted Packet)

**Route:** `/add-car` (AddCarPage wizard, step 3 — "Packet")  
**Component:** `AddCarPage.tsx` → `PacketStep`  
**What it does:** Displays the completed Trusted Packet — VIN status, vehicle identity, garaging ZIP, source attribution, copy button. This is what Wu Xiaojie and Chen Kui act on.

### Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Clarity | **7 / 10** | VIN pill is visually excellent. Vehicle / ZIP are labeled with micro-headers. Copy button is 52px and prominent. But source attribution is hidden. |
| Trust | **6 / 10** | `✅ Trusted Packet` header with green check is strong. BUT source attribution is behind a toggle — it should be visible by default on VIN at minimum. |
| Professionalism | **5 / 10** | `model_used` tag next to "Trusted Packet" header surfaces internal technical detail to broker. Mock mode orange banner is alarming. |
| Mobile Usability | **5 / 10** | `maxWidth: 640` is fine but the Descriptions table for field details is dense on small screens. |

**Overall Screen 5: 5.75 / 10**

### What creates trust
- `✅ CheckCircleOutlined` green icon next to "Trusted Packet" is the right visual anchor
- VIN Status Pill (VIN Valid / VIN Warning / VIN Missing) is the single most useful trust signal in the product
- Missing fields callout (`Alert type="error"`) is honest and actionable
- Copy button at 52px height with clear bilingual label is production-quality CTA

### What creates confusion
- `Tag color={mock_mode ? 'volcano' : 'default'}` next to the "Trusted Packet" title — in real use the model name tag (e.g. "gemini-1.5-flash") is meaningless to Wu Xiaojie and breaks the professional impression
- Source attribution is hidden behind "Show field details (source & confidence)" toggle — but source attribution is explicitly in the Decision Freeze §3 as a trust requirement. Wu Xiaojie should see "from: purchase_agreement.pdf" next to the VIN without clicking
- Warnings section appears AFTER vehicle info in the card — P16_72_HOUR_BUILD_PLAN.md explicitly requires warnings BEFORE fields, but the current code renders vehicle/ZIP first, then warnings

### What feels unfinished
- No case ID displayed in packet (P16_72_HOUR_BUILD_PLAN.md references "CK-001" in the above-fold design, but no case numbering exists in PacketStep)
- No timestamp ("Packet generated: Jun 18, 2026 2:47 PM")
- `buildCopyText()` includes "Sources:" section — this is correct, but the visual Trusted Packet card doesn't prominently show sources until "field details" is expanded

### What looks like an engineer demo
- `Tag color="default"` showing model name (`gemini-1.5-flash` or similar) directly on the packet header
- When `mock_mode=true`, the orange `"MOCK extraction only — no real AI was used"` banner is alarming and would destroy confidence in any demo
- `MOCK` red tag on individual fields in the detail view would also appear in a demo if Gemini key is not set

### What looks professional
- The `VinStatusPill` with `CheckCircleOutlined / WarningOutlined / CloseCircleOutlined` is the most polished component in the product
- `buildCopyText()` format (field: value, line-by-line) is exactly what Wu Xiaojie needs to paste into AMS
- The "Show field details" expandable is the right pattern for progressive disclosure — it just needs source attribution promoted to above-fold

---

## Summary Score Card

| Screen | Clarity | Trust | Professionalism | Mobile | **Avg** |
|--------|---------|-------|-----------------|--------|---------|
| Screen 1 — Entry Gate | 8 | 8 | 6 | 8 | **7.5** |
| Screen 2 — Customer Info | 7 | 5 | 6 | 7 | **6.25** |
| Screen 3 — Upload | 7 | 5 | 5 | 6 | **5.75** |
| Screen 4 — Extracting | 7 | 4 | 3 | 8 | **5.5** |
| Screen 5 — Trusted Packet | 7 | 6 | 5 | 5 | **5.75** |
| **Flow Average** | **7.2** | **5.6** | **5.0** | **6.8** | **6.2** |

---

## Critical Gaps Before Chen Kui Pilot

These are not style issues — they are trust and accuracy issues:

| # | Gap | Screen | Severity |
|---|-----|--------|----------|
| 1 | `model_used` tag visible to broker on Trusted Packet | Screen 5 | P0 |
| 2 | Mock mode banner fires in demo if Gemini key absent | Screen 5 | P0 |
| 3 | Source attribution hidden behind toggle (Decision Freeze §3 violation) | Screen 5 | P0 |
| 4 | Warnings render AFTER vehicle fields (should be before — per 72hr plan) | Screen 5 | P0 |
| 5 | No VIN source file visible above fold | Screen 5 | P0 |
| 6 | Screen 4 loading screen looks like a crashed app | Screen 4 | P1 |
| 7 | "Read Documents" CTA language is backend-developer voice | Screen 3 | P1 |
| 8 | Duplicate phone entry (Screen 1 and Screen 2) | Screen 1→2 | P1 |
| 9 | InboxOutlined icon on upload dragger | Screen 3 | P1 |
| 10 | "Customer Information" title in broker-voice on customer-facing screen | Screen 2 | P1 |

---

*Authority: `docs/p16/P16_DECISION_FREEZE_V1.md`*  
*Next doc: `docs/p16/P16_PILOT_DEMO_BLUEPRINT_V2.md`*
