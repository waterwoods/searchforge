# P19D-3.5 — Guided Workflow Best Practice Recon

**Date:** 2026-07-06  
**Type:** Industry UX / channel architecture recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19D implementation agents  
**Prerequisite:** P19D-2 (H5 single-slot VIN) ✅ · P19D-3 (WeCom Start Card → H5 VIN link) ✅ · P19B (Workbench attachment review) ✅  

**Core question:** Should customers **ping-pong between WeChat and H5** for each photo step — or **enter H5 once** and complete VIN → registration → insurance card → delivery date in one continuous guided flow?

**This loop:** No code. No deploy. No schema migration.

**Related SSOT:** `docs/p19d_core_step_by_step_evidence_capture_doctrine.md`  
**Prior recon:** `p19d15`, `p19d16`, `p19d05`, `p19_guided_workflow_start_end_card_recon.md`

---

## 0. Executive Summary

| Question | Answer |
|----------|--------|
| Industry norm for multi-step photo capture? | **One task shell** — stay inside app / H5 / 小程序 until photo steps complete |
| Ping-pong WeChat ↔ H5 per photo step? | **Avoid** — only acceptable as MVP bridge; not target UX |
| Recommended Add Vehicle photo path? | **One H5 entry → chain 2–3 photo slots in-browser → return WeChat once** |
| Text fields (date, ZIP, phone)? | **Stay in WeChat chat** after photo chain completes |
| H5 enough for pilot? | **Yes** — matches 微保/银行 H5+客服 pattern; 小程序 is polish layer |
| Mini program required now? | **No** — defer until H5 chain metrics justify 审核 cost |

**One-line recommendation:**

> WeCom chat = **router + trust + text + notify**. H5 = **continuous photo task shell** (enter once, finish all photo slots, exit once). Do **not** send a new chat link after every single photo unless customer explicitly abandons mid-flow.

---

## 1. Research Methodology

Sources reviewed (public docs, help centers, product recon — not live app instrumentation):

| Category | Products / vendors |
|----------|-------------------|
| US gig-driver native apps | Walmart Spark Driver, DoorDash Dasher, Amazon Flex, Instacart Shopper, Uber Driver |
| Identity / KYC SDKs | Jumio, Onfido, Persona (DoorDash partner) |
| China fintech / insurance | 支付宝实名、腾讯微保、平安好车主/车险小程序、微信支付「去报销」快赔 |
| Internal | P19D SSOT, P19D-2/3 evidence, H5 page implementation |

Scoring lens: how closely each product matches our constraints — **WeCom entry, broker-reviewed insurance intake, 3–4 evidence slots, no auto-quote/OCR promise in pilot**.

---

## 2. Cross-Industry Pattern Matrix

Answers to the 10 research questions across reference categories.

### 2.1 One entry vs. return-to-chat each step?

| Product | Model | Chat / messaging role |
|---------|-------|----------------------|
| **Spark Driver** | Single native app; onboarding + active delivery tasks never leave app shell | Push notifications only; no chat per step |
| **DoorDash Dasher** | App-native sequential ID verify (Persona): gov ID → selfie; signup has resumable checklist | SMS/email link only if device has no camera |
| **Amazon Flex** | App-only onboarding; guided prompts for license front → back → insurance → selfie | Email when done; no per-step chat |
| **Instacart Shopper** | Web form + app; license front/back inside app questionnaire | None during capture |
| **Uber Driver** | Documents hub in app; pick document type → capture one at a time | None during capture |
| **Jumio / Onfido KYC** | Embedded SDK wizard; session spans multiple scan parts | N/A — merchant app owns shell |
| **支付宝实名** | App pages: 信息 → 人脸 → 证件正反面; no chat between steps | 客服 only on failure |
| **微保理赔** | 小程序 wizard: 选保单 → 按材料清单逐步上传 → 提交 | 客服帮办入口; 支付后「去报销」= one deep link into wizard |
| **平安车险** | 好车主 App / 小程序: 报案 → 按提示拍照 → 材料页; stays in app | 查勘员 IM optional; not per-photo |

**Pattern:** Mature products **do not** return to a messaging thread between photo steps. Chat/SMS is **entry router, failure escalation, or completion notify** — not the step-to-step navigator.

**Implication for us:** P19D-3 (one H5 link per VIN only, next step via chat) is a **valid MVP slice** but **not** the industry end state. Target = **P19D-3.5+ continuous H5 photo chain**.

---

### 2.2 How are multi-step photos arranged?

| Pattern | Who | How |
|---------|-----|-----|
| **Sequential single-capture** | Spark, Flex, KYC SDKs | System prompts next object; one shutter action per screen |
| **Ordered sub-parts** | Amazon Flex license | "Front first, then back" — enforced order, separate captures |
| **Checklist hub** | Uber Documents | List of required docs; user taps each; incomplete items visible |
| **Material checklist wizard** | 微保/平安 | Dynamic list of required materials; each opens capture sub-screen |
| **Scene batch with per-photo confirm** | Claim photo flows (industry) | Multiple photos allowed in one *session* but **one confirm cycle each** — not one album pick |

**Universal rule:** **One active capture intent per screen.** Multi-page documents = **multiple steps**, not one multi-select.

**Add Vehicle mapping:**

```text
Step 1  VIN photo          (1 image, preview, confirm)
Step 2  Registration       (1 image; if front/back needed → 2a/2b, still sequential)
Step 3  Insurance card     (optional; 1 image; skip tap)
─── exit H5 ───
Step 4  delivery_date, zip (WeChat text)
```

---

### 2.3 One upload vs. multi-image per step?

| Context | Multi-image allowed? |
|---------|---------------------|
| Spark / Flex / Dasher onboarding | **No** per step — one document image per capture action |
| KYC SDK | **No** — one credential part per confirm cycle |
| 微保理赔 | **Batch upload** in some flows — but inside 小程序 with **AI classify + per-type slots**, not raw chat album |
| Claim accident photos | **Yes, multiple** — but sequential confirm or typed sub-batches (5+5), never unstructured dump |

**Default for structured intake:** **One image per step.**  
**Exception:** Claim-lite scene photos — multiple images in one **wizard session**, each with preview confirm (P19D SSOT claim batch rule).

**Add Vehicle:** **Never** multi-image per step. Insurance card optional = skip, not second image in same picker.

---

### 2.4 Preview confirm at every step?

| Product | Preview confirm |
|---------|-----------------|
| Spark Driver | Yes — "USE PHOTO" / retake before submit; ID scan review screen |
| DoorDash / Persona | Yes — retake on blur/glare; explicit resubmit |
| Amazon Flex | Yes — retake if blurry; tips before capture |
| Jumio / Onfido | **CONFIRMATION_VIEW** / **rejectView** — confirm or retake before part finishes |
| 支付宝证件 | Yes — 重拍 if 模糊 |
| 微保 | Yes — 材料不清晰会提示重传 |

**Industry default:** **Every photo step has preview → confirm or retake.** Auto-submit without customer ack is rare for compliance-sensitive docs.

**Our pilot:** H5 already has preview confirm (P19D-2). **Keep on every slot.**

---

### 2.5 How is progress shown?

| Product | Progress UI |
|---------|-------------|
| Spark Driver | Section headers (Auto Insurance, Identity); "Needs attention" banners; % implicit via checklist |
| DoorDash signup | Onboarding checklist on home screen after background check submitted |
| Amazon Flex | Step labels in onboarding; "upload front then back" inline |
| KYC SDK | Step indicator within SDK chrome |
| 微保 / 平安 | Material checklist with ✓/○; 案件进度时间轴 post-submit |
| Uber | Documents list with status per item |

**Best practices:**

1. **「第 X 步 / 共 Y 步」** at top of capture screen  
2. **Named current task** — "VIN 照片", not "上传资料"  
3. **Completed steps visible** (checkmarks or collapsed list)  
4. **Post-submit:** timeline in app/chat — "已收到 2/3 张照片"

**Chat-only progress** (text "第2步") is **supplement**, not substitute for on-page stepper.

---

### 2.6 Interruption, exit, resume later?

| Product | Resume behavior |
|---------|-----------------|
| Spark / Uber / Flex | Account state persisted; return to Documents → incomplete items |
| DoorDash Persona ID | **Cancel mid-verify = progress lost** for that sub-flow; must restart ID capture |
| DoorDash signup overall | Login resumes checklist at last incomplete **major** step |
| Jumio / Onfido | `applicant_id` / session token — resume same verification |
| 微保 / 平安 | Draft claim saved in 小程序; continue from material checklist |
| Our P19D design | `current_slot_id` + case JSON; 「继续」re-mints link for empty slot |

**Patterns:**

- **Task-level resume:** Yes — don't force full restart if 2/3 photos done  
- **Step-level resume:** Re-open **same slot** if upload failed; advance only on successful confirm  
- **Expired link:** Bot sends fresh link for **current** slot only  
- **Chat command:** 「继续」/「下一步」> hunting old URLs in history  

**Critical:** Resume should land customer in **H5 at first incomplete photo slot**, not back to Start Card.

---

### 2.7 Wrong upload, blur, skip, manual review?

| Failure | Industry handling |
|---------|-------------------|
| **Blur / glare** | In-flow retake (KYC rejectView); Spark "not accepted" → retry prompts |
| **Wrong doc type** | Slot-specific example image + title; KYC OCR mismatch → retry |
| **Wrong slot** | Prevented by sequential shell; Uber = separate document types |
| **Skip optional** | Explicit "Skip" / "暂无" button (insurance card) |
| **Skip required** | Block advance; checklist shows gap |
| **Manual review** | Spark/Flex: "pending verification" state; broker/carrier reviews async |
| **Chat fallback** | Customer sends image in chat → quarantine (our P19D-1) |

**Our stack:**

```text
H5:      prevent > preview > confirm
Chat:    P19D-1 quarantine (safety net)
Workbench: broker promote / re-prompt / manual slot assign
```

Never auto-OCR or auto-bind on quarantined images (SSOT A9–A10).

---

### 2.8 Avoiding user error (mis-tap, bulk, phishing)?

| Technique | Used by |
|-----------|---------|
| `count: 1` / single capture | H5, 小程序, native apps |
| Slot-specific example ("拍挡风玻璃 VIN 贴纸") | Spark tips, 平安车损测算 |
| Framing overlay / guide box | KYC SDK, 平安 AI 相机 |
| Confirm dialog on submit | Universal |
| Disable multi-select album | H5/MP only — chat cannot |
| Branded header + broker name | 微保, bank H5 — reduces phishing fear |
| Short TTL + bound token | Fintech deep links |
| 「请本人操作」+ masked name | KYC, our pilot mitigation |
| No generic "upload all documents" copy | SSOT rule |

---

### 2.9 Recommended Add Vehicle flow (synthesis)

**Recommended customer journey:**

```text
┌─────────────────────────────────────────────────────────────────┐
│ WECOM CHAT — entry, trust, text, notify, human                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Customer: 我要加车                                           │
│ 2. Start Card → tap「开始补资料」                                 │
│ 3. ONE view button: 「开始上传车辆照片」→ opens H5 task session    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ H5 TASK SHELL — continuous photo chain (no return to chat)      │
├─────────────────────────────────────────────────────────────────┤
│ Header: 加车资料 · 第 1/3 步 · 陈奎保险服务                        │
│ Step 1: VIN photo      → preview → confirm → auto-advance       │
│ Step 2: 行驶证          → preview → confirm → auto-advance       │
│ Step 3: 保险卡 (可选)   → upload OR tap「暂无，跳过」              │
│ Success screen: ✅ 照片已收齐 · 「返回微信」+ 说明下一步            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ WECOM CHAT — text fields + closure                                │
├─────────────────────────────────────────────────────────────────┤
│ 4. Bot (within 3s): 「VIN、行驶证已收到。请直接打字：提车日期、   │
│    邮编、联系电话。」                                              │
│ 5. Customer types delivery_date, zip, phone (no links)           │
│ 6. E1 End Card: 「资料已收齐，陈总会人工确认」                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ WORKBENCH — broker review                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Why this split:**

| Segment | Channel | Reason |
|---------|---------|--------|
| Photo evidence (3 slots) | **One H5 session** | Matches Spark/KYC/微保; minimizes 3× context switch |
| Text fields | **Chat** | Faster than mobile form; matches 客服+打字 industry pattern |
| Broker review | **Workbench** | Already shipped P19B |

**VIN text fallback:** If customer cannot photograph VIN, H5 offers「改为打字发 VIN」→ deep link instruction to return chat for text — **exception path**, not default.

---

### 2.10 H5 vs. 小程序 — is H5 enough?

| Dimension | H5 (WeChat WebView) | 微信小程序 |
|-----------|---------------------|-----------|
| Time to pilot | **Days–weeks** | Weeks–months (审核, 主体, 发布) |
| `chooseMedia` count:1 | ✅ with JSSDK | ✅ native, more reliable |
| Continuous multi-step | ✅ route/state in SPA or multi-page | ✅ better navigation stack |
| Return to WeCom KF | Manual swipe back | `openCustomerServiceChat` ✅ |
| Camera latency / offline | Weaker | Stronger |
| Customer trust | Medium (link anxiety) | Higher (official 小程序) |
| Chen Kui pilot scale | **Sufficient** | Overkill until volume proves need |

**China industry:** 微保、银行、险企普遍 **H5 或 小程序** 做材料采集；**纯客服聊天**仅作入口。H5 is explicitly used in fintech pilots before MP.

**Verdict:**

| Phase | Channel |
|-------|---------|
| **Now (pilot)** | H5 continuous photo chain |
| **After metrics** | 小程序 mirrors same state machine |
| **Never (pilot)** | Chat-only photo intake |

---

## 3. Deep Dives by Reference Product

### 3.1 Walmart Spark Driver

**Flow model:** Native app task shell. Onboarding sections: personal info → insurance upload → identity (license scan + selfie). Active delivery: arrive → scan → photo proof → confirm → next item.

| Question | Spark behavior |
|----------|----------------|
| Chat per step? | **No** — all in-app |
| Multi-step photos | Sequential; license front/back scanned separately |
| Multi-image | One per capture; PDF allowed for insurance |
| Preview confirm | **USE PHOTO** / retake; review before submit |
| Progress | Section-based; "Needs attention" for expired docs |
| Resume | Login → incomplete document banners |
| Errors | Rejected → in-app retry prompts; human support async |
| Mis-op prevention | Scan overlays, lighting tips, head-turn liveness |

**Borrow for Add Vehicle:** One task shell, one object per screen, confirm before submit, checklist for broker async review — **not** Spark's in-store scan UX.

---

### 3.2 DoorDash / Uber Eats / Instacart Shopper

**DoorDash:** Persona embedded in Dasher app — **gov ID upload → selfie match** as sequential steps. Cancel mid-Persona = **restart that flow** (strict). Overall signup = resumable checklist.

**Instacart:** Questionnaire → **Take photo** front/back license in app; web application can save/resume but photo steps in app.

**Uber Eats / Uber Driver:** Documents hub — select document → capture; common rejection reasons documented (blur, corners, wrong type).

| Shared pattern | Detail |
|----------------|--------|
| Entry | App download or deep link into app — not SMS per photo |
| Photo steps | 2–4 document types, one capture each |
| Text fields | Form fields in same app session, not separate channel |
| Quality | Published rejection reason taxonomy — we should mirror in broker re-prompt copy |

**Borrow:** Sequential ID capture; explicit retake reasons; checklist visibility.

---

### 3.3 Amazon Flex

**Flow model:** App-only. License **front then back** (order enforced). Insurance card photo. Selfie liveness. Onboarding <1 hour; **cannot edit after submit**.

| Highlight | Relevance |
|-----------|-----------|
| Ordered upload | Front/back = 2 steps — maps to registration 2a/2b if needed |
| Quality tips | Dark background, all corners, no glare — use as H5 helper copy |
| No mid-flow chat | Confirms single-shell norm |

---

### 3.4 Bank / KYC (Jumio, Onfido, Persona)

**Flow model:** SDK-driven state machine:

```text
prepare → scanView → imageTaken → confirmationView → confirm|retake
       → nextPart → … → canFinish
```

| Feature | Detail |
|---------|--------|
| Preview confirm | **CONFIRMATION_VIEW** mandatory |
| Reject path | **REJECT_VIEW** with reason (blur, glare) → retake |
| Multi-part | Passport, ID front, ID back = separate parts |
| Resume | Same `applicant_id` / session token |
| Chat | None |

**Borrow:** This is the **technical gold standard** for our H5 slot machine — each slot = one Jumio "scan part" with confirm/retake.

---

### 3.5 China: 支付宝、微保、平安

**支付宝实名：** App 内连续页 — 姓名身份证 → 人脸活体 → 证件照；失败提示重拍；客服仅在异常。

**微保理赔：**

- 入口：小程序「理赔服务」或微信支付成功页「去报销」→ **一次跳入**理赔 wizard
- 材料：按清单逐步上传；AI 分类辅助；**不是**客服聊天里一张一张收
- 进度：案件状态可查询；小额闪赔

**平安好车主：**

- 报案 → 按提示拍照（车损测算 AI 引导）→ 材料提交
- 小程序/App 内完成；查勘员联系是 **parallel human**, not step navigator

| China lesson | Application |
|--------------|-------------|
| 聊天 = 路由 | WeCom Start Card + **one** H5 entry |
| 结构化采集 = 小程序/H5 | Our H5 photo chain |
| 支付/聊天触点 deep link | Future: renewal notice → H5 premium review (not Add Vehicle) |
| AI QC post-upload | Post-pilot P19C+ — not MVP customer promise |

---

## 4. Current State vs. Target (P19D)

| Item | Shipped (P19D-3) | Target (P19D-3.5+) |
|------|------------------|---------------------|
| WeCom entry | ✅ Start Card → H5 VIN link | ✅ Keep |
| H5 scope | Single slot (`vin_photo` only) | **Multi-slot chain in one session** |
| Between photo steps | Chat notify + new link (planned) | **In-H5 auto-advance** |
| Text fields | Chat (design) | Chat (unchanged) |
| Workbench | ✅ Attachment review | ✅ + `source=h5_task` per slot |

**Gap:** P19D-3 intentionally stopped at VIN-only. Next increment is **not** "registration link in chat" — it is **extend H5 session** to slots 2–3 before returning to WeChat.

---

## 5. Anti-Patterns to Avoid

| Anti-pattern | Why industry avoids | Our risk |
|--------------|---------------------|----------|
| New chat link after every photo | 3× context switch; link fatigue | Customer abandons after step 1 |
| Generic「请上传车辆资料」| Invites album dump | P19D-1 quarantine storm |
| One H5 page accepting album multi-select | Defeats slot binding | Broker cleanup |
| All fields in H5 form | Feels like DMV website | Slower than chat for date/ZIP |
| Silent upload success | User re-uploads duplicates | GCS noise |
| OCR promise in copy | Regulatory + expectation | Pilot trust damage |
| Forcing 小程序 before H5 validation | Months delay | Miss Chen Kui trial window |

---

## 6. MVP vs. Later Version Split

### 6.1 MVP (P19D-3.5 — next build loop)

**Goal:** Continuous H5 photo chain for Add Vehicle; minimal chat ping-pong.

| # | Scope | Out of scope |
|---|-------|--------------|
| 1 | H5: VIN → registration → optional insurance_card in **one browser session** | OCR |
| 2 | Progress header「第 X/Y 步」+ slot title + example image | Full checklist sidebar |
| 3 | Preview confirm every slot (existing P19D-2 pattern) | AI blur detection |
| 4 | Skip button on insurance_card | DL photo slot |
| 5 | Success → chat notify within 3s + text field prompt | In-H5 date picker |
| 6 | Token: session-scoped or per-slot mint on server advance | OAuth |
| 7 | Resume: 「继续」→ H5 opens at first empty photo slot | 小程序 |
| 8 | P19D-1 chat guardrail unchanged | — |

**Acceptance:** Customer completes 2–3 photos with **≤2** WeChat↔H5 transitions total (enter + exit).

---

### 6.2 V1.1 (post-pilot polish)

| Feature | Value |
|---------|-------|
| Registration front/back as 2a/2b if broker requires | Carrier compliance |
| E2 partial End Card when customer exits mid-chain | Resume clarity |
| Chat checklist summary message「已完成：VIN ✓ 行驶证 ✓」 | Progress in chat |
| H5 `closeWindow` attempt + always chat ack | Return friction |
| Broker Workbench re-prompt → mint resume link for one slot | Exception path |

---

### 6.3 V2 (volume justification)

| Feature | Trigger |
|---------|---------|
| 微信小程序 | >N cases/week + link-trust complaints |
| `openCustomerServiceChat` after H5 complete | MP only |
| Post-upload blur heuristic (client-side) | Broker retake rate > threshold |
| OCR draft on promoted slots only | P19C+ with broker confirm |
| Premium Review / Claim Lite chains | Lane expansion |

---

## 7. Decision Table — Ping-Pong vs. Continuous H5

| Approach | Context switches (3 photos) | Industry alignment | Broker cleanup | Pilot fit |
|----------|:---------------------------:|:------------------:|:--------------:|:---------:|
| **A. Chat link per photo** | 6+ (chat→H5→chat ×3) | ⭐ Poor | Medium | P19D-3 slice only |
| **B. Continuous H5 photo chain** | **2** (enter + exit) | ⭐⭐⭐⭐⭐ | Low | **✅ Recommended** |
| **C. Pure WeCom chat** | 0 | ⭐ (photo control) | High | Demo only |
| **D. 小程序 chain** | 2 + better return | ⭐⭐⭐⭐⭐ | Lowest | Post-pilot |

**Decision:** **B for P19D-3.5.** A was acceptable to ship VIN-only fast; do not extend A to registration/insurance.

---

## 8. Final Recommendations

### 8.1 Most recommended user flow

```text
WeCom Start Card (once)
    → H5 photo chain: VIN → 行驶证 → [保险卡 skip OK]
    → return WeChat (once)
    → chat text: 提车日期 + 邮编 + 电话
    → E1 End Card
    → Workbench broker review
```

### 8.2 Should customer complete 3–4 steps in one H5 entry?

| Step type | One H5 entry? |
|-----------|:-------------:|
| Photo steps (VIN, reg, insurance) | **Yes** — continuous chain |
| Text steps (date, ZIP, phone) | **No** — stay in WeChat chat |
| Broker review | Workbench — async |

**Photo steps = one H5 entry. Text steps = chat. Total customer "missions" = 2, not 5.**

### 8.3 Should we avoid WeChat/H5 ping-pong?

**Yes.** Limit to:

1. **Enter:** chat → H5 (Start Card button)  
2. **Exit:** H5 success → chat (manual swipe + bot message)  

Optional third switch only for **exception** (customer chose「改为打字发 VIN」).

### 8.4 Add Vehicle recommended steps

| Order | Step | Channel | Required |
|------:|------|---------|:--------:|
| 0 | Start Card 开始补资料 | WeCom | — |
| 1 | VIN photo | H5 chain | Yes |
| 2 | 行驶证 photo | H5 chain | Yes |
| 3 | 保险卡 photo | H5 chain | Optional (skip) |
| 4 | 提车日期 | WeCom text | Yes |
| 5 | 邮编 | WeCom text | Yes |
| 6 | 联系电话 | WeCom text | If missing |
| 7 | E1 资料已收齐 | WeCom | — |
| 8 | Broker confirm | Workbench | — |

### 8.5 H5 vs 小程序

| Verdict | Detail |
|---------|--------|
| **H5 for pilot** | ✅ GO — sufficient for 75–85% Spark-like discipline |
| **小程序 now** | HOLD — after H5 chain validated with real customers |
| **Chat-only photos** | HOLD — P19D-1 safety net only |

---

## 9. GO / HOLD Summary

| Gate | Verdict |
|------|---------|
| P19D-3.5 recon complete | **GO** |
| Extend P19D-3 with per-step chat links for reg/insurance | **HOLD** — prefer continuous H5 chain |
| P19D-3.5 build: H5 multi-slot photo chain | **GO** (next implementation loop) |
| 小程序 before H5 chain smoke | **HOLD** |
| Code / deploy this loop | **No** |

---

## 10. Constraints This Loop

| Item | Status |
|------|--------|
| Code changed | **No** |
| Deploy | **No** |
| Schema migration | **No** |

---

## Appendix A — Source Links

| Source | URL |
|--------|-----|
| Spark Driver enrollment | https://sparkdriverapp-walmart.helpdocs.io/l/en/article/efmc0vj5p3-enrolling-on-the-spark-driver-platform |
| Spark identity verification | https://sparkdriverapp-walmart.helpdocs.io/l/en/article/sam6qhz3gb-real-time-identity-verification-bvw |
| DoorDash Dasher ID verification (Persona) | https://help.doordash.com/en-us/dashers/article/dasher-identification-verification-faq |
| Amazon Flex FAQ | https://flex.amazon.com/faq |
| Uber document upload | https://help.uber.com/en/driving-and-delivering/article/uploading-documents |
| Jumio SDK scan steps | https://documentation.jumio.ai/docs/developer-resources/SDKs/mobile-sdk/ |
| Onfido iOS SDK | https://github.com/onfido/onfido-ios-sdk |
| 微保理赔 / 微信快赔 | https://news.qq.com/rain/a/20250305A03BR500 |
| 平安车险理赔指引 | https://property.pingan.com/kehufuwu/chexian/lipeizhiyin_6.shtml |

---

*End P19D-3.5 — guided workflow best practice recon. No code. No deploy. STOP.*
