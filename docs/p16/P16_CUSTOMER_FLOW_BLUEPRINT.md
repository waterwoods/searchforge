# P16 Customer Flow Blueprint

**Date:** 2026-06-20  
**Sprint:** P16 Documentation Freeze  
**Status:** Accepted  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md` · `docs/p16/P16_REQUEST_FRAMEWORK.md`

---

## Overview

7 screens. Less than 3 minutes for the customer.  
No login. No account. No insurance jargon.

```
Screen 0: Intent
Screen 1: Basic Info
Screen 2: Upload
Screen 3: Reading (Extract Progress)
Screen 4: Readiness
Screen 5: Fix Missing
Screen 6: Sent to Broker
```

---

## Screen 0 — Intent

**What the customer sees:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   What do you need help with?                               │
│   您需要什么帮助？                                           │
│                                                             │
│   [  I bought a new car and need to add it to insurance  ] │
│   [  我买了一辆新车，需要加到保险上                         ] │
│                                                             │
│   [  I replaced my old car with a new one                ] │
│   [  我换了一辆新车，需要更新保险                           ] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules:**
- Plain language. No "Add Vehicle Endorsement Request."
- No insurance jargon ("endorsement," "floater," "binder," "rider").
- Both English and Chinese. Customer's first language wins.
- No explanation required to pick an option.
- Time target: < 30 seconds.

---

## Screen 1 — Basic Info

**What the customer sees:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Your Information / 您的信息                               │
│                                                             │
│   Full Name / 姓名                                          │
│   [                                    ]                    │
│                                                             │
│   Phone Number / 电话                                       │
│   [                                    ]                    │
│                                                             │
│   Where does the car stay overnight?                        │
│   新车停在哪里？（邮编）                                     │
│   [          ]                                              │
│   This is used to calculate your rate.                      │
│   用于计算保险费率。                                         │
│                                                             │
│   [  Continue →  ]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules:**
- Title: "Your Information" — not "Customer Information" (that's broker-voice).
- Garaging ZIP field label: "Where does the car stay overnight?" — not "Address" or "ZIP Code."
- Explain why Garaging ZIP is needed: "used to calculate your rate."
- Time target: < 1 minute.
- No account creation. No email. No password.

---

## Screen 2 — Upload

**What the customer sees:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Upload your documents / 上传文件                          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │                                                     │  │
│   │         ☁  Drag files here or tap to upload        │  │
│   │            拖拽文件或点击上传                        │  │
│   │                                                     │  │
│   │         PDF · JPG · PNG · HEIC supported            │  │
│   │                                                     │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   Helpful documents to include:                             │
│   ✓ Purchase agreement / 购车合同（最重要）                  │
│   ✓ Vehicle registration / 车牌注册                         │
│   ✓ Current insurance card / 当前保险卡                     │
│                                                             │
│   You can upload photos taken on your phone.                │
│   可以直接上传手机拍的照片。                                  │
│                                                             │
│   [  Continue →  ]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules:**
- Upload icon: `CloudUploadOutlined` — not `InboxOutlined` (email icon).
- CTA: "Continue →" — not "Read Documents" (backend developer language).
- Support HEIC explicitly — most Chinese-speaking customers use iPhones.
- No minimum file count enforced. Customer uploads what they have.
- Time target: < 2 minutes (including phone camera capture).

---

## Screen 3 — Reading (Extract Progress)

**What the customer sees:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Reading your documents…                                   │
│   正在读取您的文件…                                          │
│                                                             │
│   ✓  Opening your files                                     │
│   ✓  Finding vehicle information                            │
│   ▸  Looking for VIN number…                                │
│   ○  Checking driver information                            │
│   ○  Preparing your summary                                 │
│                                                             │
│   This usually takes less than a minute.                    │
│   通常不超过一分钟。                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules:**
- Animated steps (not a bare spinner). Steps progress as extraction completes.
- No model names visible. Never show "gemini-1.5-flash" or any AI brand.
- No technical language ("parsing," "OCR," "LLM call," "prompt").
- Bilingual: English + Chinese side by side.
- If extraction takes > 30 seconds, show reassurance: "Still working — larger files take longer."
- Time target: < 60 seconds for extraction completion.

---

## Screen 4 — Readiness

**What the customer sees:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Here's what we found / 以下是我们找到的信息               │
│                                                             │
│   DRIVER / 驾驶员                                           │
│   ✅ Primary Driver:  Andy Li           (your name)         │
│                                                             │
│   VEHICLE / 车辆                                            │
│   ✅ VIN:             5UXZV4C56BL402905  from: contract.pdf │
│   ✅ Year:            2024                                  │
│   ✅ Make / Model:    Toyota Camry LE                       │
│   ⚠️ Delivery Date:   Please confirm                        │
│   ❌ Lienholder:      Not found — do you have a car loan?   │
│                                                             │
│   DETAILS / 保险信息                                        │
│   ✅ Garaging ZIP:    91101                                  │
│                                                             │
│   [  Everything looks right — Continue  ]                   │
│   [  Fix the missing information        ]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules:**
- Display in three buckets: Driver / Vehicle / Policy Details.
- Use ✅ / ⚠️ / ❌ at field level. No percentages.
- Show source file next to key fields: "from: purchase_agreement.pdf"
- For ⚠️ fields: show why confirmation is needed ("defaulted from your name — confirm").
- For ❌ fields: explain in plain language ("do you have a car loan?").
- Customer can proceed even if optional fields (lienholder) are missing.
- Customer cannot proceed if VIN is ❌.

---

## Screen 5 — Fix Missing / Review

**What the customer sees (only for ❌ or ⚠️ fields):**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Please provide a few more details                         │
│   请补充以下信息                                             │
│                                                             │
│   ❌ Lienholder (Car Loan / 贷款机构)                       │
│      Do you have a car loan?                                │
│      例如：Toyota Financial · Bank of America               │
│      [                                    ]  (text input)   │
│                                                             │
│   ❌ Delivery Date (交车日期)                                │
│      When did you receive / pick up the car?                │
│      [  Jun  ] [  20  ] [  2026  ]                          │
│                                                             │
│   ⚠️ Primary Driver (驾驶人)                               │
│      We used your name. Is this correct?                    │
│      [  Andy Li  ]  ✓  Yes  /  Edit                         │
│                                                             │
│   [  Submit →  ]                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules:**
- Only show fields that need fixing. Never redisplay the full form.
- For text-derivable fields (lienholder, name): inline text input.
- For document-derivable fields (VIN cannot be typed in): prompt re-upload of a better document.
- For ⚠️ fields: pre-fill with extracted value; customer confirms or corrects.
- No field is required if it's optional in the schema. Customer can skip lienholder.
- VIN cannot be manually typed in by the customer — must come from a document.

**Correction model:**
- Customer fixes ❌ optional fields → text input
- Customer fixes ⚠️ fields → confirm or override
- Customer fixes ❌ critical field (VIN) → re-upload a clearer document

**Re-upload model:**
- Button: "Upload a better photo / 重新上传文件"
- Goes back to Screen 2, retains all previously entered info
- Extraction reruns; readiness updates

---

## Screen 6 — Sent to Broker

**What the customer sees:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ✅  Your request was sent to your broker.                 │
│       您的请求已发送给您的保险经纪人。                        │
│                                                             │
│   Your broker will review the details and confirm           │
│   next steps with you.                                      │
│   您的经纪人将审核您的信息，并与您确认后续步骤。              │
│                                                             │
│   What you submitted:                                       │
│   ✓ Andy Li · 626-555-0000                                  │
│   ✓ 2024 Toyota Camry LE                                    │
│   ✓ VIN: 5UXZV4C56BL402905                                  │
│   ✓ Garaging ZIP: 91101                                     │
│                                                             │
│   Questions? Contact your broker directly.                  │
│   有问题请直接联系您的经纪人。                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design rules — language contract:**

| ✅ Use | ❌ Never Use |
|--------|------------|
| "Sent to your broker" | "Insurance updated" |
| "Broker will confirm" | "Policy changed" |
| "Broker will review" | "Your vehicle is now covered" |
| "Next steps with you" | "Submitted to carrier" |
| "Contact your broker" | "Done — you're all set" |

**Rationale:** P16 does not know when the carrier confirms. Telling the customer their policy is changed before the broker acts is a liability and a false promise. See ADR-003.

---

## Customer Confusion Risks

| Risk | Trigger | Prevention |
|------|---------|------------|
| "Did it work?" | Screen 6 doesn't feel conclusive | Show the summary of what was submitted; bilingual |
| "Why do they need so much just to add a car?" | Long upload screen | Explain each document in one line; make it feel familiar |
| "It crashed" | Bare spinner on Screen 3 | Animated steps with progress; reassurance text |
| "What is VIN?" | Technical acronym | Add tooltip: "VIN 是车辆识别码，通常在购车合同上" |
| "I don't have a purchase agreement" | Document prompt | Allow registration or VIN photo as alternative; don't block |
| "They asked me twice for the same thing" | Re-upload confusion | Retain all previously entered data through re-upload |
| "Is my insurance actually updated?" | Screen 6 language | Never say "updated" — always say "sent to broker" |

---

## Timing Targets

| Step | Customer Action | Target Time |
|------|----------------|-------------|
| Screen 0 | Intent selection | < 30 sec |
| Screen 1 | Basic info entry | < 1 min |
| Screen 2 | File upload | < 2 min |
| Screen 3 | Wait for extraction | < 60 sec (system) |
| Screen 4 | Review readiness | < 30 sec |
| Screen 5 | Fix missing (if any) | < 1 min |
| Screen 6 | Confirmation read | < 10 sec |
| **Total** | **Full submission** | **< 3 minutes** |

---

## Broker Experience (Reference)

The broker sees the Trusted Packet generated from this flow.  
Broker view is documented in `docs/p16/P16_REQUEST_FRAMEWORK.md` §2 and §4.  
Broker does NOT see Screens 0–6. Broker receives the packet via the workbench.

---

*Related: `docs/p16/P16_REQUEST_FRAMEWORK.md` · `docs/p16/adr/ADR_001_REQUEST_READINESS.md` · `docs/p16/adr/ADR_003_NO_CARRIER_API_V1.md`*
