# P16 Upload-First Customer Flow

**Date:** 2026-06-17  
**Sprint:** P16 Add-Car Packet Builder — Product Definition Sprint  
**Authority:** Master spec: `P16_ADD_CAR_PACKET_BUILDER_MASTER_SPEC.md`

---

## Design Principles

- **Upload-first**: customer's first primary action is to upload documents, not type text
- **Big and obvious**: large tap targets, minimal clutter, visible progress
- **Chinese-friendly**: all placeholder text and prompts available in Chinese
- **Familiar patterns**: Expensify (receipt upload), TurboTax (document pre-fill), Stripe onboarding (clear steps)
- **No jargon**: zero insurance vocabulary in customer-facing screens

---

## Flow Overview

```
Screen 1: Identity
    ↓
Screen 2: Upload
    ↓
Screen 3: Extracting (auto-advance)
    ↓
Screen 4: Review & Confirm
    ↓
Screen 5: Submitted (customer view)
    
    → (parallel) →  Screen 5b: Quote-Ready Packet (office view)
```

---

## Screen 1: Identity

**Purpose:** Capture phone number and name with zero friction. No login. No password.

### Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│   Add a Car to Your Insurance               │
│   为您的保险添加车辆                           │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │ 📱 Phone number / 手机号              │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │ Your name / 姓名                     │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │        Continue →                   │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   Your information is only shared with      │
│   your insurance broker.                   │
│                                             │
└─────────────────────────────────────────────┘
```

### Rules

- Phone field is required and validated (US 10-digit, with formatting)
- Name field is required
- No account creation, no password, no email
- Broker-specific branding (logo, name) at top
- Privacy statement at bottom (one line)
- "Continue" button disabled until both fields are valid

### Edge States

- Invalid phone → inline error "Please enter a 10-digit US phone number"
- Empty name → inline error "Please enter your name"
- No submit until valid

---

## Screen 2: Upload

**Purpose:** Customer uploads up to 5 document files. They upload what they already have. They are not required to have everything.

### Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│   Upload Your Car Documents                 │
│   上传您的车辆资料                             │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │                                     │   │
│   │   Drop files here, or tap to select │   │
│   │   拖拽文件或点击上传                   │   │
│   │                                     │   │
│   │   PDF, JPG, PNG, HEIC · Max 5 files │   │
│   │   每个文件最大 10 MB                  │   │
│   │                                     │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   What can I upload? / 可以上传什么？         │
│   ✓ Dealer paperwork / 经销商文件             │
│   ✓ Purchase contract / 购车合同              │
│   ✓ VIN photo / 车架号照片                    │
│   ✓ Registration / 车辆登记证                 │
│   ✓ Insurance card / 保险卡                  │
│   ✓ Email screenshot / 邮件截图               │
│                                             │
│   [File 1: dealer_contract.pdf  ✓ ]         │
│   [File 2: vin_photo.jpg        ✓ ]         │
│   [File 3: insurance_card.png   ✓ ]         │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │   Analyze My Documents →            │   │
│   │   开始分析我的文件 →                  │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   Don't have all documents? Upload what     │
│   you have. We'll tell you what's missing.  │
│   没有全部文件？上传现有文件，我们告诉您缺什么。  │
│                                             │
└─────────────────────────────────────────────┘
```

### Rules

- Max 5 files per request
- Max 10 MB per file
- Accepted types: PDF, JPG, JPEG, PNG, HEIC, WEBP
- Each file shows: filename, size, type icon, upload status (uploading → ready → error)
- Reject unsupported file types immediately with "This file type is not supported (ZIP, DOCX, etc.)"
- "Analyze My Documents" button shows after at least 1 file is uploaded
- No-doc path: "I don't have documents yet" link → guides to contact broker

### Edge States

- File too large (>10 MB) → "File too large. Max 10 MB per file."
- Unsupported type → "This file type is not supported."
- Upload failure → "Upload failed. Please try again."
- 5 files reached → "Maximum 5 files reached."
- No files uploaded → primary button says "Skip for now (contact broker)"

---

## Screen 3: Extracting

**Purpose:** Customer waits while AI processes documents. 3–15 second wait. Auto-advances when complete.

### Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│   Reading Your Documents                    │
│   正在读取您的文件                             │
│                                             │
│   ████████████████░░░░░░  67%              │
│                                             │
│   ✓ Dealer paperwork — done                 │
│   ✓ VIN photo — done                        │
│   ⟳ Insurance card — reading…              │
│                                             │
│   This usually takes 10–15 seconds.        │
│   通常需要 10–15 秒。                          │
│                                             │
└─────────────────────────────────────────────┘
```

### Rules

- Per-file progress indicators
- Friendly, non-technical copy
- Auto-advances to Screen 4 when complete
- On failure: "We couldn't read one of your files. Please try uploading it again."
- Timeout at 60 seconds → "This is taking longer than expected. Please wait or try again."

---

## Screen 4: Review and Confirm

**Purpose:** Customer sees what was extracted. Reviews, confirms, or corrects. Must confirm before submission.

### Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│   Please Review Your Information            │
│   请确认您的信息                               │
│                                             │
│   We found this from your documents.        │
│   Please check and fix anything wrong.     │
│   我们从您的文件中提取了以下信息，请核对并纠正。   │
│                                             │
│   ── VEHICLE ─────────────────────────── ─ │
│                                             │
│   Year          [2024          ] ✓ confirmed│
│   Make/Model    [Toyota Camry  ] ✓ confirmed│
│   VIN           [1HGBH41...    ] ✓ confirmed│
│   Purchase price [32,500       ] (optional) │
│                                             │
│   ── LOCATION ────────────────────────── ─ │
│                                             │
│   Garaging ZIP  [____________  ] ⚠ STILL NEEDED│
│                                             │
│   ── DRIVER ──────────────────────────── ─ │
│                                             │
│   Primary driver [____________  ] ⚠ STILL NEEDED│
│                                             │
│   ── DATES ───────────────────────────── ─ │
│                                             │
│   Effective date [2024-08-01   ] ✓ confirmed│
│                                             │
│   ── POLICY (OPTIONAL) ─────────────────── │
│                                             │
│   Current insurer [State Farm  ] ✓ found   │
│   Policy number   [SF-9293-XX  ] ✓ found   │
│                                             │
│   ⚠ You have 2 items still needed.         │
│   Please fill them in to submit.           │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │   Submit My Request →               │   │
│   │   提交我的请求 →                      │   │
│   └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Field Display States

| State | Visual | Copy |
|-------|--------|------|
| Extracted + confirmed | White field, green checkmark | "✓ confirmed" |
| Low confidence | Yellow border, warning icon | "Please confirm — we're not sure about this" |
| Conflict | Red border | "Conflict: Source A says X, Source B says Y. Which is correct?" |
| Missing required | Red empty field, red label | "⚠ Still Needed" |
| Missing optional | Grey empty field | "(optional)" |

### Conflict Resolution Widget

When two sources disagree on a field (e.g. VIN):

```
VIN — CONFLICT DETECTED / 车架号冲突
──────────────────────────────────────
From dealer contract:   1HGBH41JXMN109186
From VIN photo:         1HGBH41JXMN109187
                                       ↑ difference

Which is correct? / 哪个是正确的？
  ○ 1HGBH41JXMN109186 (from dealer contract)
  ○ 1HGBH41JXMN109187 (from VIN photo)
  ○ Neither — I'll type the correct one: [___________]
```

### Second Vehicle Block

If AI detects references to a second vehicle:

```
⛔ Two vehicles detected / 检测到两辆车
──────────────────────────────────────
Your documents seem to reference two different vehicles.
您的文件中似乎包含两辆不同车辆的信息。

Each car must be submitted as a separate request.
每辆车需要单独提交一个请求。

[ Submit for Vehicle 1 only ]
[ Start a new request for Vehicle 2 ]
[ Contact my broker directly ]
```

### Rules

- Customer cannot submit until all required fields have values
- Every field that was AI-extracted shows the source document
- Customer can edit any field inline
- "Submit My Request" only enabled when all required fields filled
- Optional fields do not block submission

---

## Screen 5a: Customer Confirmation (Post-Submit)

**Purpose:** Customer receives confirmation that their request was sent.

```
┌─────────────────────────────────────────────┐
│                                             │
│   ✓ Request Submitted                       │
│   ✓ 请求已提交                                │
│                                             │
│   Your broker has received your add-car     │
│   request for:                              │
│   您的经纪人已收到您的加车请求：               │
│                                             │
│   2024 Toyota Camry                         │
│   VIN: 1HGBH41JXMN109186                   │
│                                             │
│   What happens next? / 接下来会发生什么？     │
│   Your broker will review and contact you   │
│   within 1–2 business days.                │
│   您的经纪人将在 1–2 个工作日内联系您。         │
│                                             │
│   Request ID: #REQ-20240801-4821            │
│                                             │
│   [ Save or screenshot this page ]         │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Screen 5b: Quote-Ready Packet (Office View)

**Purpose:** Wu Xiaojie sees the complete packet in the broker workbench. She should understand readiness in 10 seconds.

### Top strip (10-second test)

```
┌─────────────────────────────────────────────────────────────────┐
│  STATUS: ● QUOTE-READY   |  No conflicts   |  No missing fields │
│  ─────────────────────────────────────────────────────────────── │
│  Customer: Li Wei · 415-555-0193  ·  Submitted: 2024-08-01 9:14am│
└─────────────────────────────────────────────────────────────────┘
```

See `P16_ADD_CAR_PACKET_BUILDER_MASTER_SPEC.md` Section 10 for full packet format.

---

## No-Document Flow

If customer has no documents:

Screen 2 shows:
```
Don't have your documents handy?
没有随手可用的文件？

You can:
1. Upload later — your progress is saved  [Save progress]
2. Contact your broker directly:          [Call / WeChat Chen Kui]
3. Submit what you know (no docs)        [Continue without documents]
```

"Continue without documents" leads to a simplified Screen 4 where all fields are empty and customer fills manually.

---

## Mobile UX Notes

- All screens designed for iPhone-width first (375px)
- Upload via camera roll or camera capture supported (HEIC + JPG)
- Large tap targets (min 44px)
- Chinese input keyboard supported on phone number and name fields
- No horizontal scroll
- No modals over content on mobile

---

## UI Component Recommendations

| Component | Library | Notes |
|-----------|---------|-------|
| Drag-and-drop upload | React Dropzone | Lightweight, battle-tested, no UI opinions |
| File list with progress | React Dropzone + custom | Simple status icons |
| Form fields with inline validation | shadcn/ui Input + Form | Consistent styling |
| Confirmation checkboxes | shadcn/ui Checkbox | Accessible |
| Conflict chooser | shadcn/ui RadioGroup | Structured choice |
| Progress bar | shadcn/ui Progress | Simple |
| Pill/badge status | shadcn/ui Badge | Required / optional / conflict states |
| Layout + responsive | Tailwind CSS | No config required |

---

*End of P16 Upload-First Customer Flow*
