# P16 Pilot Demo Blueprint V2

**Date:** 2026-06-18  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Purpose:** Complete pilot readiness document — customer journey, broker journey, trust checklist, demo script, deploy readiness, Top 20 UI fixes, TurboTax benchmark.  
**Audience:** Andy (founder) pre-pilot review. Chen Kui and Wu Xiaojie pilot actors.

---

## Part 1 — Ideal Customer Journey

### The moment the customer arrives

Chen Kui sends a customer a link: `https://[domain]/add-car`  
Customer: Wu Xiaojie's customer, phone in hand, just picked up a new car from the dealer.  
Mental state: "I need to add this car to my policy fast. I don't want to dig through WeChat again."

### Step-by-step ideal flow

```
[Customer opens link on iPhone]
↓
Screen 1 — Entry Gate
  "Add Car to Your Insurance — 加险加车"
  ☑ No account needed    ☑ No password    ☑ Return anytime with phone
  → Enter phone number → Enter name (optional) → Continue
  Time: < 30 seconds

↓
Screen 2 — Your Information
  Name / Phone / Garaging ZIP
  ZIP tooltip: "ZIP where the car sleeps at night — affects your rate"
  → Next — Upload Documents
  Time: < 60 seconds

↓
Screen 3 — Upload Your Car Paperwork
  "Upload any of these from your phone:"
  • Purchase Agreement · 购车合同
  • Window Sticker · 车窗贴纸
  • VIN photo (door jamb) · VIN照片
  Tap to select from Photos or Files → 1–3 files added
  → Continue (3 files)
  Time: < 90 seconds (including photo selection)

↓
Screen 4 — Reading Your Documents (10–30 seconds)
  ✦ Reading Purchase Agreement…
  ✦ Finding VIN, year, make, model…
  ✦ Checking garaging ZIP…
  [Animated steps with pulse]
  Time: 10–30 seconds (system)

↓
Screen 5 — Done. Your information is with the broker.
  A green confirmation card appears.
  Case reference number shown.
  "The office will contact you. No need to re-send anything."
  Time: 2 seconds to read
```

**Total ideal time: 3–4 minutes from link-open to confirmation.**

### What the customer should NEVER see

- The word "MOCK" anywhere
- `model_used: gemini-1.5-flash` on any screen
- A blank white screen with a spinner for > 5 seconds without text
- JSON objects or raw field names (`still_needed_fields`, `quote_ready_status`)
- An error that leaves the customer stranded without a recovery path

---

## Part 2 — Ideal Broker Journey

### Wu Xiaojie (office operator) receives the packet

Wu Xiaojie works at Chen Kui's brokerage. She handles 5–15 add-car requests per week.  
Her current process: read WeChat thread, re-read VIN photo, copy into AMS, call customer for garaging ZIP.  
Target state: open packet, scan 5 fields, copy all, paste into AMS — done in 2 minutes.

### Broker Workbench ideal flow

```
[Wu Xiaojie opens workbench]
↓
Queue panel — sees "New: Li Hua — Add Car — 2025 Toyota Camry"
Case entered at 2:47 PM. Status: Ready for review.
↓
Clicks case → Trusted Packet loads:

┌────────────────────────────────────────────────────────────┐
│  ✅ Trusted Packet   CK-001  ·  Jun 18 2026 2:51 PM        │
│  Li Hua  ·  (626) 555-0100  ·  Garaging ZIP: 91101        │
├────────────────────────────────────────────────────────────┤
│  ⚠️  No warnings — all fields extracted cleanly            │
├────────────────────────────────────────────────────────────┤
│  VIN    1HGCM82633A004352    ✅ VIN Valid                  │
│         from: purchase_agreement.pdf                       │
│  Year   2025                from: window_sticker.pdf       │
│  Make   Toyota              from: window_sticker.pdf       │
│  Model  Camry               from: window_sticker.pdf       │
├────────────────────────────────────────────────────────────┤
│  Missing: None — all required fields found                  │
├────────────────────────────────────────────────────────────┤
│  [  COPY ALL FIELDS  ]  ← 52px primary button             │
└────────────────────────────────────────────────────────────┘

↓
Wu Xiaojie clicks "Copy All Fields"
→ Pastes into AMS / carrier portal
→ Done. No WeChat reading required.
Time from opening workbench to copied: < 90 seconds.
```

### What the broker should NEVER see

- `model_used` technical tag on the packet header
- Mock mode orange warning banner
- Source attribution only in a collapsed "Show details" toggle (it must be visible by default)
- Warnings buried below the fields they warn about
- Case ID absent (must know which customer this is)

---

## Part 3 — Ideal Packet Review Screen

The Trusted Packet is the product. It must be scannable in 5 seconds.

### Required above-fold layout (no scroll)

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Trusted Packet          CK-001  ·  Jun 18 2:51 PM       │
│  Li Hua  ·  (626) 555-0100  ·  Garaging ZIP: 91101         │
├─────────────────────────────────────────────────────────────┤
│  ⚠️  WARNINGS (expanded if present / "None" if clean)       │
├─────────────────────────────────────────────────────────────┤
│  VIN    1HGCM82633A004352   ✅    from: purchase_agmt.pdf   │
│  Year   2025                       from: window_sticker.pdf │
│  Make   Toyota                     from: window_sticker.pdf │
│  Model  Camry                      from: window_sticker.pdf │
│  ZIP    91101 (entered by customer)                         │
├─────────────────────────────────────────────────────────────┤
│  Missing: None                                              │
├─────────────────────────────────────────────────────────────┤
│  [    COPY ALL FIELDS    ]  ← PRIMARY CTA                  │
└─────────────────────────────────────────────────────────────┘
```

### Order of elements (strict)

1. Header: "Trusted Packet" + case ID + timestamp
2. Customer identity: name, phone, garaging ZIP
3. Warnings section (expanded if any; compact "No warnings" if clean)
4. VIN with inline VIN status pill AND inline source file
5. Year / Make / Model with inline source files
6. Missing fields (if any) with clear "ask customer for X" language
7. `COPY ALL FIELDS` primary button
8. Expandable "View full field details" for confidence + all extracted fields
9. "Start New Case" secondary at bottom

### What must NOT appear on the packet

- `model_used` tag (internal; meaningless to broker)
- "MOCK" tags or banners (must never fire in pilot)
- JSON keys or field names (`still_needed_fields`, etc.)
- Confidence percentages (broker does not know what 0.83 means; use high/medium/low labels only when needed)

---

## Part 4 — First Impression Checklist

For Wu Xiaojie and Chen Kui — the first 10 seconds of seeing the product.

**Before Chen Kui shows the product to Wu Xiaojie, verify every item:**

- [ ] The page title in the browser tab reads something meaningful, not "React App" or "Vite + React"
- [ ] No "MOCK" or "DEMO MODE" banners visible anywhere
- [ ] Screen 1 shows a welcoming message, not a blank form
- [ ] The green gradient welcome box on Screen 1 is visible on first load
- [ ] Screen 2 asks for "Your Information," not "Customer Information"
- [ ] The upload icon on Screen 3 is a cloud/upload icon, not an email inbox
- [ ] Screen 4 shows animated loading steps, not a bare spinner
- [ ] Screen 5 (Trusted Packet) has a case ID + timestamp in the header
- [ ] VIN source attribution ("from: purchase_agreement.pdf") is visible without clicking
- [ ] Warnings section is ABOVE vehicle fields in the packet
- [ ] "Copy All Fields" button is prominent (52px, primary color, block width)
- [ ] No `model_used` technical tag on the packet header
- [ ] `Start Over` is present but below the primary CTA (not competing with it)

---

## Part 5 — Trust Checklist

**Five trust requirements from Decision Freeze §3 — verify before pilot:**

| # | Trust Requirement | Current State | Target State |
|---|-------------------|---------------|--------------|
| T1 | Source attribution — each field links to originating file | Hidden behind "Show details" toggle | Visible inline with VIN and vehicle fields by default |
| T2 | VIN validation — invalid/short VIN shows visible warning | Working in `VinStatusPill` component | Also confirm: 16-char VIN fires "must be 17" warning |
| T3 | No silent wrong data — warnings visible before fields | Warnings render AFTER vehicle info in current code | Reorder: warnings FIRST, then fields |
| T4 | Missing fields identified — broker knows what to ask | Alert `type="error"` shows missing fields | Confirm "ask customer for X" language is human-readable |
| T5 | Copy text is clean — paste into AMS is ready to use | `buildCopyText()` generates field-label: value format | Test: paste into Google Docs, confirm no JSON artifacts |

---

## Part 6 — Demo Walkthrough Script

### Context
Andy walks Chen Kui and Wu Xiaojie through the product. 15 minutes. Use a real (or realistic) add-car case.

### Walkthrough

**[Andy opens link on phone — shows to Wu Xiaojie]**

> "This is the link your customers will use. They get it from you via WeChat or text. No login, no account — they just enter their phone number and their name."

**[Enters phone: 6265550001, name: Li Hua — Continue]**

> "Phone is how they return to the same case. If they start filling this out and stop, they can come back anytime."

**[Moves to Screen 2 — fills name, phone, garaging ZIP: 91101]**

> "Garaging ZIP is the ZIP code where the car sleeps at night. The system will flag if the customer-entered ZIP doesn't match what's on the documents."

**[Moves to Screen 3 — uploads 2–3 files: purchase agreement + window sticker]**

> "Customer uploads whatever they have from the dealer — the purchase agreement, window sticker, a photo of the VIN plate. iPhone photos work, PDFs work. They just share from their camera roll."

**[Clicks Continue — moves to Screen 4]**

> "The AI reads the documents — Gemini Flash from Google. Takes about 15–20 seconds."

**[Screen 5 appears — pause for 5 seconds of silence]**

> "This is what you see. [Gesture to VIN pill] VIN is valid. [Gesture to source] It came from the purchase agreement. [Gesture to year/make/model] 2025 Toyota Camry. [Gesture to ZIP] Garaging ZIP matches. No warnings."

**[Click Copy All Fields — gesture to open Notes or Google Docs — paste]**

> "One click. You paste this into your AMS or carrier portal. No reading WeChat, no calling the customer for the VIN."

**[Show paste result]**

> "That's 2 minutes instead of 10. For one case. For 5 cases a week, that's 40 minutes. For a 3-person office, that's 2 hours a week. That's the first invoice."

### Handling questions

| Question | Answer |
|----------|--------|
| "What if the VIN is wrong?" | "It will show a warning — red pill at the top. You don't miss it. And you can see which file it came from." |
| "What if the customer only sends a photo?" | "Photos work — JPG, PNG, iPhone HEIC files all work." |
| "What about the lienholder for financed cars?" | "If it's in the document, it gets extracted. If not, the packet shows it as missing and tells you to ask the customer." |
| "Is this secure?" | "Files go to Google Cloud Storage — same infrastructure used by major carriers." |

---

## Part 7 — Top 20 UI Improvements

### Classification

| Priority | Definition |
|----------|------------|
| **P0** | Must be done before Chen Kui pilot. Blocks trust, accuracy, or professionalism. |
| **P1** | Should be done if under 2 hours total. Improves experience without risk. |
| **P2** | Future improvements. Post-10-case gate. |

---

### P0 — Must be done before Chen Kui pilot

**UI-01 — Remove `model_used` tag from Trusted Packet header**  
Screen: 5 (PacketStep)  
Fix: Remove `<Tag color={mock_mode ? 'volcano' : 'default'}>{mock_mode ? 'MOCK' : model_used}</Tag>` from the packet header. Move to a collapsed "debug info" section only visible in dev.  
File: `ui/src/pages/AddCarPage.tsx` — `PacketStep` component, line ~463  
Ant Design: just delete the Tag; no replacement needed above fold  

**UI-02 — Source attribution inline on VIN and vehicle fields (above fold)**  
Screen: 5 (PacketStep)  
Fix: Show `from: [source_file]` as a small secondary line directly beneath VIN value and Year/Make/Model — visible by default, before any toggle.  
Pattern: `<Text type="secondary" style={{ fontSize: 11 }}>from: {packet.vin?.source_file}</Text>`  
File: `ui/src/pages/AddCarPage.tsx` — `PacketStep`, inside the VIN block (line ~468–484) and vehicle identity block  

**UI-03 — Move warnings ABOVE vehicle fields in Trusted Packet**  
Screen: 5 (PacketStep)  
Fix: Reorder the `PacketStep` card so the warnings `Alert` renders immediately after the VIN pill row — before the vehicle identity block. Current code renders: VIN pill → vehicle label → ZIP → warnings → missing fields → copy.  
Target order: VIN pill → warnings (if any) → vehicle label + ZIP → missing fields → copy  
File: `ui/src/pages/AddCarPage.tsx` — `PacketStep`, reorder JSX in the main Card  

**UI-04 — Guard mock mode banner — never show in production/demo**  
Screen: 5 (PacketStep)  
Fix: Wrap the mock mode Alert in `process.env.NODE_ENV === 'development'` check, OR move it to a collapsed "debug" section. A broker should never see "MOCK extraction only — no real AI was used."  
File: `ui/src/pages/AddCarPage.tsx` — PacketStep, line ~443–451  

**UI-05 — Add case ID + timestamp to Trusted Packet header**  
Screen: 5 (PacketStep)  
Fix: Pass `case_id` from `PacketResponse` (if returned by API) or generate a display timestamp client-side. Display as small secondary text in the header row next to "Trusted Packet."  
Pattern: `<Text type="secondary" style={{ fontSize: 12 }}>Jun 18, 2026 · 2:51 PM</Text>` using `new Date().toLocaleString()`  
File: `ui/src/pages/AddCarPage.tsx` — `PacketStep` header block, `PacketResponse` type  

---

### P1 — Should be done if under 2 hours

**UI-06 — Change "Customer Information" title to "Your Information"**  
Screen: 2 (InfoStep)  
Fix: Change `<Title level={3}>Customer Information</Title>` → `<Title level={3}>Your Information / 您的基本信息</Title>`  
File: `ui/src/pages/AddCarPage.tsx` — `InfoStep`, line ~208  

**UI-07 — Replace InboxOutlined with CloudUploadOutlined on Upload dragger**  
Screen: 3 (UploadStep)  
Fix: Replace `<InboxOutlined />` in the `<Dragger>` body with `<CloudUploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />`. Import `CloudUploadOutlined` from `@ant-design/icons`.  
File: `ui/src/pages/AddCarPage.tsx` — `UploadStep`, `Dragger` body, line ~329  

**UI-08 — Change "Read Documents" CTA to "Continue →"**  
Screen: 3 (UploadStep)  
Fix: Change button text from `Read Documents ({fileList.length} file{...})` to `Continue → ({fileList.length} file{...} ready)`  
File: `ui/src/pages/AddCarPage.tsx` — `UploadStep`, line ~349–353  

**UI-09 — Add animated loading steps to ExtractingStep**  
Screen: 4 (ExtractingStep)  
Fix: Add 3 rotating step hints beneath the Spin using a `useEffect` timer or `Steps` component with animated `status="process"`. Steps: "Reading your documents…" → "Finding VIN and vehicle details…" → "Assembling your packet…"  
File: `ui/src/pages/AddCarPage.tsx` — `ExtractingStep`, replace bare Spin card  

**UI-10 — Add customer name + garaging ZIP to Trusted Packet header**  
Screen: 5 (PacketStep)  
Fix: Add customer name, phone, and garaging ZIP as a visible sub-header row in the main packet card — above fold, before VIN. Currently these are only visible in "field details."  
File: `ui/src/pages/AddCarPage.tsx` — `PacketStep`, add a new row after the header Space block  

**UI-11 — Rename CTA from "Copy Packet" to "Copy All Fields"**  
Screen: 5 (PacketStep)  
Fix: `<Button>Copy Packet / 复制数据包</Button>` → `<Button>Copy All Fields / 复制全部字段</Button>`. "Fields" aligns with what the broker pastes into AMS.  
File: `ui/src/pages/AddCarPage.tsx` — `PacketStep`, line ~534–542  

**UI-12 — Normalize card maxWidth to 560 across Screens 2 and 3**  
Screen: 2, 3  
Fix: InfoStep card uses `maxWidth: 480`; UploadStep uses `maxWidth: 560`. Normalize both to `maxWidth: 560` for layout consistency. The Steps progress bar already uses `maxWidth: 640`.  
File: `ui/src/pages/AddCarPage.tsx` — `InfoStep` card style  

**UI-13 — Add "secure upload" micro-copy to UploadStep**  
Screen: 3  
Fix: Add a one-line note beneath the file type list: `"Files are uploaded securely to your broker's system. / 文件安全上传到您的经纪人系统。"`  
File: `ui/src/pages/AddCarPage.tsx` — `UploadStep`, after the `<ul>` document list  

**UI-14 — Add success count confirmation when files are added**  
Screen: 3  
Fix: When `fileList.length > 0`, show a compact `Alert type="success"` or inline text: `"2 files ready ✓ — documents will be read when you continue. / 2 个文件已就绪"`  
File: `ui/src/pages/AddCarPage.tsx` — `UploadStep`, replace the "Upload at least one document" info alert  

**UI-15 — Suppress `description: '客户信息'` on Steps bar (use English consistently)**  
Screen: All (Steps bar)  
Fix: The Steps bar descriptions are Chinese-only: `'客户信息'`, `'上传文件'`, `'读取中'`, `'数据包'`. For a broker-facing screen, use English: `'Info'`, `'Upload'`, `'Reading'`, `'Packet'` — or remove descriptions entirely for a cleaner Steps bar.  
File: `ui/src/pages/AddCarPage.tsx` — main wizard `Steps` items, line ~721–728  

---

### P2 — Future improvements

**UI-16 — Case ID numbering (CK-001 style) in Trusted Packet**  
Rationale: The 72-hour plan explicitly references "CK-001" in the above-fold design. Requires backend to return `case_id` in packet response and display logic.  
Complexity: Backend API change + frontend display  

**UI-17 — Loading progress bar during extraction (animated % complete)**  
Rationale: Shows the system is working. Reduces abandonment on slow networks.  
Complexity: Backend would need to stream progress events; medium complexity  

**UI-18 — Mobile-first HEIC hint on UploadStep**  
Rationale: "iPhone users: tap the + button and select from Photos or Files app" is absent  
Complexity: Simple copy addition  

**UI-19 — Packet print layout (broker can print or save to PDF)**  
Rationale: Some brokers want a paper record. Low priority for Chen Kui pilot.  
Complexity: CSS print media query on PacketStep  

**UI-20 — Branding / brokerage identity on Screen 1**  
Rationale: "Powered by Chen Kui Insurance" or brokerage name on entry screen builds trust  
Complexity: uiCopy config addition — medium  

---

## Part 8 — TurboTax Benchmark

### What TurboTax, Stripe Checkout, and modern fintech do

| Design Pattern | TurboTax | Stripe Checkout | Modern Fintech | Current Add-Car |
|----------------|----------|-----------------|----------------|-----------------|
| Step count visible | ✅ "Step 3 of 8" always shown | ✅ progress bar | ✅ pill steps | ⚠️ Steps bar exists but descriptions are Chinese-only |
| Why we need this field | ✅ Every field has an explanation | ✅ Inline tooltips | ✅ Contextual help | ⚠️ Only ZIP has a tooltip |
| Loading state | ✅ Animated progress with named stages | ✅ Animated spinner with status | ✅ Skeleton UI or stage labels | ❌ Bare Ant Design Spin |
| Confirmation screen | ✅ "You're done — here's what happens next" | ✅ Receipt + next steps | ✅ Green checkmark + timeline | ⚠️ Packet appears but no "you're done, what now" framing |
| Error recovery | ✅ Specific error + retry path | ✅ Specific error + retry | ✅ Try again button + contact | ⚠️ Error banner + stays on Upload screen; no retry instruction |
| Trust signals | ✅ "256-bit encryption" + logos | ✅ "Powered by Stripe" + lock icon | ✅ Security badge | ❌ No security signal, no company attribution |
| Progressive disclosure | ✅ Only shows what's needed per step | ✅ One action per screen | ✅ Minimal visible fields | ✅ Steps wizard is correct; field details are collapsed |
| Mobile-first | ✅ Large tap targets, autofocus | ✅ Built for mobile | ✅ Native-feeling | ⚠️ Functional but not mobile-first designed |
| CTA language | ✅ "Continue →" everywhere | ✅ "Pay now" — specific | ✅ Action-specific | ⚠️ "Read Documents" is internal language |
| Showing results | ✅ "You saved $2,340 — here's why" value framing | ✅ Clear receipt | ✅ Visual summary | ⚠️ Trusted Packet is correct but has no "here's the value" framing |

### Specific Ant Design solutions (no rebuild)

All of these are available in the existing `antd` import:

| TurboTax pattern | Ant Design solution | Apply to |
|------------------|--------------------|---------||
| Stage-labeled loading | `Steps` with `status="process"` + `useEffect` cycling through steps | Screen 4 ExtractingStep |
| Contextual "why" tooltips | `Form.Item tooltip` prop | Screen 2 — Name field, Phone field |
| Confirmation + next steps | `Result component` with `status="success"` | Screen 5 bottom — after copy |
| Security badge | `Space` with `LockOutlined` icon + "Securely submitted to broker" | Screen 3 bottom |
| "Here's what was saved" | `Descriptions bordered` above the copy button | Screen 5 — replace expandable with pinned summary |
| Better loading icon | `Spin indicator={<LoadingOutlined spin />}` with larger `fontSize` | Screen 4 |
| Upload icon | `CloudUploadOutlined` or `UploadOutlined` | Screen 3 Dragger |
| Progress feedback | `Progress percent={fileList.length * 10}` when files added | Screen 3 optional |

### What NOT to do (do not rebuild)

- Do not migrate to shadcn/ui — frozen per Decision Freeze §5
- Do not add authentication screens — frozen per Decision Freeze §4
- Do not add a customer confirmation screen — frozen per Decision Freeze §4
- Do not add PDF export — frozen per Decision Freeze §4
- Do not redesign the Ant Design component library — just use existing components better

---

## Part 9 — Deploy Readiness Review

### If Andy deploys today: Top 10 things Wu Xiaojie notices first

Ranked by visual impact in order of first encounter:

| # | What Wu Xiaojie Notices | Current State | Impact |
|---|------------------------|---------------|--------|
| 1 | The page title in her browser tab | "React App" or "Vite + React" — generic | **Negative** — first visual cue is developer template |
| 2 | The welcome card on Screen 1 | Green gradient, "No account required" bullets — actually good | **Positive** — this is the strongest first impression |
| 3 | The "Customer Information" title on Screen 2 | "Customer Information / 客户基本信息" — broker-voice on customer-facing screen | **Confusion** — customer thinks "am I the customer or is the broker?" |
| 4 | The InboxOutlined icon on the upload zone | Email inbox icon on file upload | **Negative** — subliminally wrong icon for the action |
| 5 | Screen 4 loading state | Plain `<Spin size="large" />` for up to 30 seconds | **Negative** — looks like the app crashed |
| 6 | The `model_used` tag on the Trusted Packet | "gemini-1.5-flash" or "gpt-4o" in a Tag next to "Trusted Packet" | **Negative** — broker does not know what this means; erodes professionalism |
| 7 | Source attribution hidden | "Show field details" toggle required to see which file each VIN came from | **Negative** — the broker cannot confirm trust without clicking a toggle |
| 8 | Warnings position in packet | Warnings appear AFTER vehicle fields, not before | **Negative** — broker sees "VIN valid" then scrolls and sees "WARNING: VIN mismatch" — wrong order |
| 9 | Copy button text | "Copy Packet / 复制数据包" | **Neutral** — "Packet" is slightly jargon-y but acceptable |
| 10 | "Start Over / 重新开始" button position | Correct — at bottom, below primary CTA | **Positive** — secondary action correctly subordinated |

### Summary: if deployed today

**What works:**
- Screen 1 welcome card is genuinely strong
- VIN status pill (valid/warning/missing) is production-quality
- Bilingual labels throughout are appropriate for this audience
- Steps progress bar orientation is correct
- Copy All text format is clean (field: value, line by line)
- Missing fields alert is honest and actionable

**What breaks trust:**
- Technical `model_used` tag on packet header
- Mock mode banner risk if Gemini key absent
- Source attribution hidden (Decision Freeze §3 violation)
- Warnings in wrong order (after vehicle info, not before)
- Loading screen looks unfinished

**Go/No-Go verdict for today:** `CONDITIONAL GO`  
- Fix UI-01 (model_used), UI-02 (source attribution), UI-03 (warnings order), UI-04 (mock guard) first  
- These are < 2 hours combined  
- After those 4 fixes: `GO` for Chen Kui 3-case soft pilot

---

*Authority: `docs/p16/P16_DECISION_FREEZE_V1.md`*  
*UI audit: `docs/p16/P16_PILOT_UI_REVIEW.md`*  
*Pilot operations: `docs/p16/P16_CHEN_KUI_3_CASE_SOFT_PILOT.md`*
