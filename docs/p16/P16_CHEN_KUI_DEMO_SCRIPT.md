# P16 — Chen Kui Demo Script
# 4-Day Production Sprint · Add-Car Intake

**Date:** 2026-06-19  
**Audience:** Chen Kui (broker owner)  
**Goal:** Chen Kui immediately understands:  
> "No WeChat hunting. No repeat calls. No re-keying."  
**Duration:** 5 minutes  
**QA URL:** `https://ui-smoky-beta.vercel.app/add-car`  
**Broker inbox (Wu Xiaojie):** `https://ui-smoky-beta.vercel.app/workbench/document-intake`

---

## The Pain You Say First (before touching the product)

> "每次客户加车，吴小姐是不是要在微信里找一圈 VIN 照片，然后再打电话问停放邮编，再手动输进系统？"
>
> *(Every time a customer adds a car, Wu Xiaojie has to hunt through WeChat for the VIN photo, then call to ask for the garaging ZIP, then type it all in manually?)*

Wait for Chen Kui to say yes.

> "这个工具的目标就是让这个流程从 10 分钟变成 2 分钟。让我来演示一下。"
>
> *(This tool's goal is to take that process from 10 minutes to 2. Let me show you.)*

---

## 5-Minute Demo Flow

### MINUTE 1 — Customer side (30 seconds of setup)

Open the QA URL on your phone or show it in browser:
`https://ui-gd6bzzx9v-andys-projects-1f411b73.vercel.app/add-car`

> "这是你发给客户的链接 — 微信发，短信发都行。不用登录，不用注册账号。"
>
> *(This is the link you send to the customer — WeChat or text, whatever. No login, no account needed.)*

Tap through Screen 1 (Entry) → Screen 2 (Info).

Fill in:
- Name: `Li Hua` (or use Chen Kui's customer name if you have one)
- Phone: `6265550100`
- Garaging ZIP: `91101`

> "客户就填这三个：姓名、电话、停车邮编。30 秒搞定。"

---

### MINUTE 2 — Upload (60 seconds)

Use **Case A** documents (see below) or real documents from your phone.

> "然后上传资料 — 购车合同、车窗贴纸、VIN 照片 — iPhone 直接选 Photos 或 Files 里的就行。"
>
> *(Then upload the paperwork — purchase agreement, window sticker, VIN photo — iPhone can just pick from Photos or Files.)*

Upload 2–3 files, click **Continue →**.

---

### MINUTE 3 — Extraction (20–30 seconds, system works)

Screen 4 shows animated progress steps.

> "AI 在读文件 — 大概 15 到 20 秒。"

**Do not rush. Let the system finish. Silence here is fine.**

---

### MINUTE 4 — Office inbox (Wu Xiaojie receives the case)

Open the broker queue on laptop (same browser, second tab):

`https://ui-smoky-beta.vercel.app/workbench/document-intake`

> "客户提交后，吴小姐在这里看到案件 — 不用去微信里找。"
>
> *(After the customer submits, Wu Xiaojie sees the case here — no WeChat hunting.)*

Point to the row: customer name, lane (Add Car / Policy Review), READY/NEED_INFO status, vehicle summary.

Click **Open** → show full packet, **Copy Report**, **Copy Portal Format**.

> "一键复制，贴进 EZLynx 或 carrier portal。字段带来源，不用重新问客户。"

---

### MINUTE 5 — The Packet (broker detail — optional live wizard view)

If showing the live wizard broker packet (dev/demo only), Screen 5 appears after extraction. **Pause for 5 seconds of silence before speaking.**

Point to the green banner:

> "你看这里：READY FOR BROKER。意思是所有关键字段都齐了，可以直接报价。"
>
> *(See this: READY FOR BROKER. Means all critical fields are complete, ready to quote.)*

Walk through the three sections:

**Driver section:**
> "这里是驾驶人信息 — 客户姓名、电话、主要驾驶人。"

**Vehicle section:**
> "这里是车辆信息 — VIN 号已经验证，✅ VIN Valid。来源：purchase_agreement.pdf。年份品牌型号，来源：window_sticker.pdf。不用再问客户了。"
>
> *(Here's the vehicle — VIN verified ✅. Source: purchase_agreement.pdf. Year/Make/Model, source: window_sticker.pdf. No need to ask the customer again.)*

**Finance & Timing section:**
> "这里是时间和贷款信息。如果有 lienholder 也会自动显示。"

Click **Copy Packet** button:

> "一键复制。我们贴到 Google Docs 里看一下。"

Paste into Notes or Google Docs. Show the result.

> "看 — 客户姓名、VIN、车型、邮编、来源文件，全部整理好了。吴小姐直接粘贴进系统就行。"
>
> *(See — customer name, VIN, vehicle, ZIP, source files, all organized. Wu Xiaojie just pastes into the system.)*

---

### MINUTE 5 — Case B (Missing Items, if time allows)

Switch to **Case B** documents (missing VIN).

> "如果客户漏了什么，系统会自动告诉你 — 而且还帮你写好了追单信息。"
>
> *(If the customer missed something, the system tells you — and it even writes the follow-up message for you.)*

Point to the red banner: **NEEDS CUSTOMER INFO**

Point to the Auto Follow-Up section:

> "这里是自动生成的追单信息 — 中文的。经纪人看一眼，觉得没问题就复制发给客户。不用自己写了。"
>
> *(This is the auto-generated follow-up message — in Chinese. The broker reviews it, and if it looks right, just copy and send to the customer. No need to write it yourself.)*

Click **Copy Message / 复制信息**.

---

## Closing Question

After the demo, ask:

> "如果这个能让吴小姐每个 case 少翻微信、少打电话、少手输资料，你愿意用 10 个真实 case 试一下吗？"
>
> *(If this saves Wu Xiaojie from hunting WeChat, repeat calls, and manual re-entry on every case — would you be willing to try it on 10 real cases?)*

---

## What to Say — NOT Say

| SAY | DO NOT SAY |
|-----|------------|
| "客户不用登录，不用账号" | "我们用 Gemini Flash 2.5 做 OCR" |
| "一键复制，直接粘贴进系统" | "这是一个 RAG 系统" |
| "VIN 来自哪个文件，这里显示" | "我们做了一个 trust layer" |
| "如果有错系统会警告你" | "这还在 beta 阶段" |
| "你发给客户链接，他上传，你收数据包" | "这是一个 MVP" |

---

## Demo Cases

### Case A — Success (READY FOR BROKER)

**Customer:** Li Hua  
**Phone:** 6265550100  
**Garaging ZIP:** 91101  
**Documents:** Upload any of:
- `insurance_card.png` (VIN, year, effective date)
- `smog_check_vir.png` (make, model)
- Any real purchase agreement or window sticker PDF

**Expected result:**
- ✅ VIN Valid with source attribution
- READY FOR BROKER banner (green)
- All Driver / Vehicle fields ✅
- Copy Packet produces clean broker text
- No follow-up message (or only minor ⚠️ on primary driver confirm)

**Demo purpose:** Show the clean success path. Wu Xiaojie copies and is done in 90 seconds.

---

### Case B — Missing Items (NEEDS CUSTOMER INFO)

**Customer:** Chen Wei  
**Phone:** 6265550200  
**Garaging ZIP:** 91103  
**Documents:** Upload ONLY:
- A photo of the vehicle (no VIN visible)
- OR upload any image that would NOT contain a VIN (e.g., a photo of the car exterior)

**Expected result:**
- ❌ VIN Missing
- NEEDS CUSTOMER INFO banner (red)
- Auto Follow-Up message appears in Chinese:
  ```
  您好，为了继续处理您的加车申请，还需要您补充以下资料：
  
  1. 车辆 VIN 或 Registration 照片
  ...
  ```
- Copy Message button ready to copy Chinese text

**Demo purpose:** Show what happens when the customer didn't upload everything. The broker doesn't need to write the follow-up — it's already drafted.

---

### Case C (Optional) — VIN Conflict (BROKER REVIEW REQUIRED)

**Customer:** Wang Fang  
**Phone:** 6265550300  
**Garaging ZIP:** 91105  
**Documents:** Upload documents that contain two different VINs OR a VIN with only 16 characters

**Expected result:**
- ⚠️ VIN Warning (invalid checksum or length)
- BROKER REVIEW REQUIRED banner (orange/amber)
- Warnings section expanded at top of packet
- Fields still visible but broker must verify

**Demo purpose:** Show the system doesn't silently pass bad data. The broker always sees a warning before proceeding.

---

## What NOT to Show

| Don't show | Why |
|------------|-----|
| Show field details (confidence) | Not meaningful to broker; looks like a debug screen |
| Model_used tag | Already removed — confirm it's gone |
| Mock mode banner | Should only appear in DEV; confirm not showing |
| JSON or raw field names | Already cleaned up |
| Timeline | Not built; not needed for Chen Kui pilot |
| Percentage readiness | Not built; not needed |
| "Start Over" prominently | It's there but below the CTA — fine |

---

## Recovery Lines

| Situation | What to say |
|-----------|-------------|
| API slow (> 30 sec) | "有时候如果文件比较复杂，AI 读得慢一点。通常 15–20 秒。" |
| VIN doesn't extract | "看 — VIN 没找到，系统直接告诉你，让你跟客户确认。不会悄悄放错的。" |
| Upload fails | "文件格式不对 — 支持 PDF、JPG、PNG、iPhone HEIC。让我换一个试。" |
| Chen Kui asks about WeChat | "暂时还是通过链接，客户直接上传。WeChat 直发是后面的功能。" |
| Chen Kui asks about price | "第一批是免费试用 — 10 个真实 case 之后我们再谈。" |

---

## QA URL for Pilot

Frontend: `https://ui-gd6bzzx9v-andys-projects-1f411b73.vercel.app/add-car`  
Backend: `https://fiqa-api-1013093472160.us-west1.run.app`

---

*Authority: `docs/p16/P16_DECISION_FREEZE_V1.md`*  
*Demo Blueprint: `docs/p16/P16_PILOT_DEMO_BLUEPRINT_V2.md`*  
*Pilot operations: `docs/p16/P16_CHEN_KUI_3_CASE_SOFT_PILOT.md`*
