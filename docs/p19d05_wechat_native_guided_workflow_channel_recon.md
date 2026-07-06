# P19D-0.5 — WeChat-native Guided Workflow Channel Recon

**Date:** 2026-07-05  
**Type:** Product / channel architecture recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19D implementation agents  
**Prerequisite:** P19A (media intake) ✅ · P19B (Workbench attachment UI) ✅ · P19D-0 (strict upload guardrail recon) ✅

**Core question:** Spark Driver is a native iOS/Android app with full UI control. We have WeCom / 微信客服 chat today, but chat is **weak** for:禁止多图上传、一步一图、当前 slot 验证、上传前预览确认. Which WeChat-ecosystem channel(s) can approach or exceed Spark-style guided mobile workflow?

**This loop:** No code. No deploy. No schema migration.

---

## 0. Executive Summary

**Verdict:** Pure WeCom/微信客服聊天 **cannot** reach Spark Driver-level upload discipline. Chat is the right **entry, intent, notify, and human handoff** layer — not the right **photo-proof** layer.

**Recommended pattern (industry-standard in China insurance / fintech):**

```text
WeCom 客服聊天          →  intent + Start Card + human trust + status notify
H5 guided task page     →  one slot / one image / preview / confirm  (short-term MVP)
Workbench               →  broker dispatch console (already P19B)
Mini Program            →  same task flow, better UX + identity  (medium-term)
```

**For Chen Kui pilot:** Keep WeCom chat. Add **signed H5 task links** from chat for any step that needs photo proof. P19D-1 implements **chat-side strict guardrail** (quarantine bulk) **and** defines the **H5 task-page contract**; H5 MVP can ship as P19D-1.5 without blocking guardrail work.

---

## 1. Why Chat Alone Hits a Ceiling

### 1.1 Spark Driver vs WeCom chat

| Capability | Spark Driver (native app) | WeCom / 微信客服 chat |
|------------|---------------------------|------------------------|
| UI ownership | App controls every screen | WeChat owns image picker, send UX |
| One step → one action | Enforced in app state machine | Customer can send 9+ album images in one action |
| Slot binding | App knows `current_slot_id` before shutter | Server infers slot **after** images arrive |
| Preview confirm | Built-in retake / confirm | No native pre-send confirm in chat |
| Bulk upload block | Not offered | **Cannot disable** album multi-select in chat |
| Exception branch | In-app buttons + scan fallback | `msgmenu` buttons help text/tap only |

P19D-0 strict guardrail (quarantine >3, promote one primary) is **necessary damage control** in chat — but it is **reactive triage**, not **proactive prevention**. The customer still experiences “I sent 12 photos and got a warning” instead of “the app only let me send one.”

### 1.2 What P19A/P19B already proved

| Layer | Status | Role |
|-------|--------|------|
| WeCom KF callback → `external_userid` | ✅ Live | Customer identity anchor |
| Media download → GCS → case bind | ✅ P19A | Attachment pipe |
| Workbench preview + metadata | ✅ P19B | Broker visibility |
| `msgmenu` Start Card + lane intent | ✅ Partial | Chat entry / tap transitions |
| Strict slot upload guardrail | ❌ P19D-1 | Chat-side quarantine |
| Dedicated guided upload surface | ❌ This recon | **Channel gap** |

---

## 2. China Big-Tech Best Practices (Applied)

Patterns observed across **腾讯微保、平安/头部险企小程序、京东/美团配送类任务 App、银行/证券 H5+客服混合** — adapted for broker-controlled insurance intake (not auto-claim).

### 2.1 How they turn chat into structured task flow

| Pattern | Who uses it | Mechanism |
|---------|-------------|-----------|
| **Chat = router** | 微保、银行客服、电商售后 | 客服会话做意图识别；复杂步骤 **跳出** 到小程序/H5 卡片 |
| **Template card → deep link** | 企业微信客服、保险经纪 | 模板卡片 `card_action.type=2` 或 `jump_list` 打开小程序/H5，带 `case_id` + `slot_id` 参数 |
| **Mini program task wizard** | 平安理赔、微保安心赔 | 分步页面：每页一个字段/一张图；进度条；提交后回聊天通知 |
| **Native app task loop** | Spark、美团骑手端、达达 | 一步一屏；扫码/拍照/确认；异常分支内置 |
| **Post-upload AI QC** | 微保（AI 材料分类/清晰度） | 批量上传在 **小程序内** 允许，但每批有 **实时质检+引导重拍** — not raw chat flood |

**Key lesson:** 大厂几乎不把“结构化拍照取证”放在 **纯聊天附件流** 里完成。聊天负责 **信任入口 + 通知回流**；结构化采集在 **可控 WebView / 小程序页面**。

### 2.2 When mini program vs customer service chat

| Use chat (客服) | Use mini program / H5 task page |
|-----------------|----------------------------------|
| 首次咨询、情绪安抚、意图判断 | 逐步填表、一步一图、预览确认 |
| 发 Start Card、`msgmenu` 按钮 | 相机/相册 `count: 1` 强制 |
| “联系陈总”、异常升级 | Slot 状态机 UI（第 2 步 / 共 6 步） |
| 状态通知（资料已收到） | 上传前预览、重拍、确认提交 |
| 低结构文本（VIN 打字） | PDF/多页文档分步（special slot widen） |

### 2.3 H5 task page / deep link / QR code

| Entry | Best for | Notes |
|-------|----------|-------|
| **Chat link** (template card / text URL) | Chen Kui pilot — customer already in WeCom KF | Signed token: `case_id`, `slot_id`, `external_userid` hash, TTL |
| **QR code** | 线下场景：经纪人展业、DMV 通知随信 | Same H5 URL; broker pre-creates case |
| **SMS/email fallback** | 客户不在微信、或 chat link 过期 | Same token URL; higher friction |
| **Official account menu** | 冷启动获客 | Poor for in-case slot flow — use as top funnel only |

### 2.4 Preventing bulk mis-upload

| Approach | Effectiveness in chat | Effectiveness in H5/小程序 |
|----------|----------------------|---------------------------|
| Copy “请只发一张” | Low — ignored under stress | Medium — reinforces UI |
| Server quarantine >3 (P19D-0) | Medium — reactive | N/A if UI blocks |
| `count: 1` in `wx.chooseMedia` | N/A | **High** |
| One upload button per screen | N/A | **High** |
| Preview → Confirm → Submit | N/A | **High** (Spark-like verify step) |
| Disable multi-select at picker | **Impossible in chat** | **Possible** in MP; H5 via JSSDK `count:1` |

### 2.5 One image per step / one task per action

**Spark pattern:** `prompt step → single action → verify → advance`.

**WeChat-ecosystem mapping:**

```text
Chat:     msgmenu tap OR text field  →  OK (one action per message type)
Photo:    H5/MP page state machine   →  OK (one shutter cycle per page)
Photo:    Chat image message         →  FAIL (multi-select album native)
```

### 2.6 Pre-upload preview confirm

| Channel | Preview before server receive |
|---------|--------------------------------|
| Chat | ❌ WeCom sends immediately on customer confirm in WeChat picker |
| H5 (JSSDK `chooseImage` + preview UI) | ✅ Full-screen preview + “确认上传 / 重拍” |
| Mini program | ✅ `wx.previewImage` + confirm button |
| Broker Workbench | ✅ Post-hoc (P19B) — too late for mis-upload prevention |

### 2.7 Exception reporting + human takeover

| Pattern | Implementation |
|---------|----------------|
| In-flow “联系陈总” button | H5/MP footer + chat `msgmenu` — sets `manual_handle` |
| Chat-side injury / coverage keywords | Existing P19 lanes → urgent ack (no auto-advice) |
| Quarantine bucket | P19D-0 — broker promotes/dismisses in Workbench |
| 48h KF session | Human agent can reply in 微信客服工作台; our bot pauses guided prompts when `manual_handle` |
| Template card status update | `response_code` update card to “已转人工” (enterprise WeCom API) |

### 2.8 Status notify + return to WeChat

| Mechanism | Direction |
|-----------|-----------|
| KF API `send_msg` text | H5 upload success → backend → WeCom “已收到行驶证，下一步请…” |
| Template card update | Step complete → update card subtitle |
| Mini program `openCustomerServiceChat` | MP finish → reopen same KF session |
| Subscription message (服务号/小程序) | Medium-term; KF text sufficient for pilot |

### 2.9 Insurance intake — best channel combo

| Lane | Chat role | Guided surface role |
|------|-----------|---------------------|
| **Add Vehicle** | Start Card, text fields (VIN/ZIP/date) | H5/MP for `slot_vin_photo`, `slot_registration` |
| **Premium Review** | Intent, no-quote copy | H5/MP for renewal notice / dec page (1–3 pages = widened slot steps) |
| **Claim Lite** | Safety first, urgent branch | H5/MP sub-batch confirm (5+5) — still better than chat album dump |
| **Coverage Risk** | Highest red-line copy | H5/MP for DMV/cancellation notice — **never** interpret in chat |

### 2.10 Impact on P19A/P19B architecture

| Component | Change |
|-----------|--------|
| `external_userid` + case bind | **Keep** — chat remains identity anchor |
| GCS attachment path | **Extend** — H5 uploads use same `append_wecom_gcs_attachment_metadata` with `source: h5_task` |
| Workbench preview | **No change** — same auth proxy; show `source` + `slot_id` |
| `msg_id` dedup | Chat only; H5 uses `upload_session_id` + idempotency key |
| P19D-0 quarantine | **Still required** for chat-origin images |
| New | `task_token` issuer, H5 upload API, slot state reader for task page |

**Additive only** — no schema migration; JSON fields `last_task_link`, `upload_source` on attachment meta.

---

## A. Optional Channel Matrix

| Channel | What it is | Customer journey | Control over upload | Fits P19 today |
|---------|------------|------------------|----------------------|----------------|
| **WeCom chat / 微信客服** | Current KF session (`wecom_kf`, `external_userid`) | Text → Start Card → send images in chat | **Low** | ✅ Primary entry |
| **企业微信客户联系** | Broker adds customer via 联系我; same `external_userid` | Customer messages broker corp WeChat | **Low** (same chat UX) | ✅ Chen Kui uses KF variant |
| **微信客服 (standalone)** | Same stack as above if corp uses 微信客服 | Identical | **Low** | ✅ Current |
| **公众号服务号菜单** | Service account custom menu → URL/MP | Customer must follow OA first | Medium (if menu → H5) | ❌ Not in pilot |
| **Mini Program 小程序** | Dedicated 拍照取证 wizard | Chat card → open MP → step pages | **High** | ❌ Not built |
| **H5 mobile task page** | Signed URL in WeChat built-in browser | Chat link → one-slot upload → return | **High** (with JSSDK) | ❌ Not built — **recommended MVP** |
| **QR code / deep link** | Same H5/MP URL encoded | Scan → task page | **High** | Optional broker tool |
| **小程序 + 客服混合** | MP for upload; `openCustomerServiceChat` return | Industry standard | **High** | Medium-term target |
| **企微侧边栏 / broker panel** | `single_chat_tools` H5 for broker | Broker-side only | N/A (not customer) | Future — case context for broker |
| **SMS / email fallback** | Twilio/SendGrid link | Outside WeChat | Medium | Pilot optional |

---

## B. Channel Scoring (1 = poor, 5 = excellent)

### B.1 Score table

| Channel | 用户摩擦 | Guided workflow 控制力 | 一步一图 | 禁止 bulk upload | 开发成本 (5=低) | 合规/隐私 | Workbench 集成 | Chen Kui pilot 适合度 |
|---------|:--------:|:--------------------:|:--------:|:----------------:|:---------------:|:---------:|:----------------:|:----------------------:|
| WeCom / 微信客服 chat | **5** | 2 | 1 | 1 | **5** | 4 | **5** | 4 (entry only) |
| 企业微信客户联系 (direct) | 4 | 2 | 1 | 1 | 5 | 4 | 5 | 3 (less common for US insurance customers) |
| 公众号服务号菜单 | 3 | 3 | 2 | 2 | 3 | 4 | 3 | 2 (extra follow step) |
| **Mini Program** | 4 | **5** | **5** | **5** | 2 | 4 | 4 | 4 (after审核) |
| **H5 task page** | 4 | **4** | **4** | **4** | **4** | 3 | 4 | **5** (fastest controlled upload) |
| QR / deep link | 3 | 4 | 4 | 4 | 4 | 3 | 4 | 3 (offline scenarios) |
| 小程序 + 客服混合 | 4 | **5** | **5** | **5** | 2 | 4 | 4 | **5** (best long-term) |
| 企微 broker 侧边栏 | N/A | N/A | N/A | N/A | 3 | 4 | **5** | 3 (broker-only) |
| SMS/email fallback | 2 | 3 | 3 | 3 | 4 | 3 | 4 | 2 (backup) |

### B.2 Scoring notes

**WeCom chat (5 / 5 on friction & integration)** — Customer already there; zero new app; P19A/B pipe complete. **Fails** on upload control (1/1/1) — fundamental platform limit.

**H5 task page (recommended short-term)** — One-time jump friction (-1 vs chat). With **signed token** (no login), friction is acceptable for photo steps. JSSDK `chooseImage({ count: 1 })` + custom preview ≈ 80% of mini program control at ~40% cost. WeChat built-in browser quirks require JSSDK — raw `<input type="file">` is unreliable on Android.

**Mini Program** — Best control; 微保/平安理赔同款。Costs: 主体认证、类目审核、发版周期、openid ↔ `external_userid` binding. Worth it **after** H5 validates slot UX with Chen Kui.

**公众号菜单** — Good for “找到陈奎保险助手” cold start; poor for step 3 of an active add-car case.

**Broker side panel** — Complements Workbench (browser); shows case + send task link to customer. Not a customer guided surface.

---

## C. Recommended Architecture

### C.1 Adopt: Chat as entry + H5/MP as guided task flow + Workbench as broker console

```text
┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER (WeChat / WeCom KF)                                    │
│  ┌──────────────┐    link/card     ┌──────────────────────────┐ │
│  │ Chat entry   │ ───────────────► │ H5 or Mini Program       │ │
│  │ Start Card   │ ◄─────────────── │ one slot · one image     │ │
│  │ status notify│    success+next  │ preview · confirm        │ │
│  └──────────────┘                  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                                      │
         │ wecom callback                       │ POST /task-upload
         ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND (existing P19A pipe + P19D guardrail)                   │
│  case JSON · current_slot_id · promote/quarantine · GCS          │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  BROKER WORKBENCH (P19B)                                         │
│  checklist · attachments · quarantine · manual handle            │
└─────────────────────────────────────────────────────────────────┘
```

### C.2 Layer responsibilities

| Layer | Owns | Does not own |
|-------|------|--------------|
| **Chat** | Intent, Start/End Card, text fields, disambiguation, notify, human escalation | Forced single-image capture |
| **H5/MP task page** | Slot UI, `count:1` pick, preview, confirm, exception (“拍不清楚”) | Coverage/claim decisions |
| **Workbench** | Broker confirm, quarantine review, OCR draft (P19C), outbound re-prompt | Customer mobile UI |

### C.3 Chat vs task page — per action type

| Action | Channel |
|--------|---------|
| Tap Start / lane menu | Chat |
| Type VIN, ZIP, date, phone | Chat (low friction) |
| Photo proof for named slot | **H5/MP link** |
| Bulk accident photos (claim) | **H5/MP** sub-batch wizard |
| “发错了” recovery | Chat button + Workbench quarantine |
| Broker review | Workbench only |

---

## D. MVP Recommendation — H5 Guided Task Page First

### D.1 Can we ship H5 before full mini program?

**Yes.** This is the fastest path to Spark-like **verify-before-submit** without 小程序审核.

### D.2 H5 MVP flow

```text
1. Customer in WeCom KF chat receives guided prompt:
   「请点下面链接上传行驶证（只需 1 张）」
   + signed URL: /task/{token}

2. H5 page (WeChat built-in browser):
   - Shows: 第 2 步 · 行驶证 · 示例图
   - Single button: 「拍照 / 从相册选择」
   - JSSDK chooseImage count=1 (or chooseMedia in MP WebView later)
   - Full-screen preview + 「确认上传」 / 「重拍」

3. On confirm:
   - POST multipart → backend
   - Validate token → case_id + slot_id + external_userid
   - GCS + attachment metadata (source=h5_task, intake_status=promoted)
   - Advance current_slot_id

4. Backend sends WeCom KF text:
   「已收到行驶证。下一步请告诉我提车日期。」

5. Workbench: attachment visible immediately (P19B)
```

### D.3 H5 MVP scope (P19D-1.5 candidate)

| In | Out |
|----|-----|
| Token mint + validate (TTL 30–60 min, single-use optional) | Full mini program |
| One slot per page | Multi-language UI polish |
| `count: 1` image pick + preview | OCR on H5 |
| Promote to case + WeCom notify | Customer login/account |
| Workbench shows `source: h5_task` | PDF upload (phase 2) |

### D.4 Identity binding without login

```text
token payload (signed JWT or HMAC):
  case_id
  slot_id
  external_userid
  exp
  nonce

Customer does NOT log in.
Broker mints link from Workbench OR bot mints on guided prompt.
```

**WeCom `external_userid` binding:** Token created server-side when sending chat message — ties upload to same customer as chat session. No need for openid on H5 MVP if token is unguessable and short-lived.

**Optional hardening:** Require customer to tap link **from same KF session** (Referer/session heuristic weak) — sufficient for pilot; MP path adds openid later.

### D.5 When customer refuses to jump

P19D-0 chat guardrail remains fallback:

- Accept chat image → quarantine if bulk
- Reply: 「为避免传错，建议点链接一次传一张；如您坚持在聊天发图，请先只发 1 张」

---

## E. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **微信内置浏览器限制** | High | Use 公众号 JSSDK (`wx.config` + backend signature); avoid raw `input file`; test iOS + Android WeChat |
| **小程序审核 / 主体 / 类目** | Medium (timeline) | H5 first; MP when pilot proves value; insurance 类目 may need资质 |
| **H5 身份绑定** | Medium | Signed token with `external_userid`; short TTL; audit log |
| **隐私与图片权限** | Medium | Camera permission via JSSDK; privacy policy link on H5; GCS private + no public URL (existing P19) |
| **客户不愿跳转** | Medium | Copy emphasizes “30秒、只传1张、减少传错”; chat fallback with strict quarantine |
| **`external_userid` 与 openid 打通** | Low for H5 MVP; Medium for MP | H5: token binding enough; MP: `unionid` + 企业微信 conversion API when same 微信开放平台主体 |
| **Link forwarding / token leak** | Medium | Single-use token; slot-scoped; broker can invalidate |
| **JSSDK 配置复杂度** | Medium | Reuse domain already on Vercel/Cloud Run; one `jssdk_sign` endpoint |
| **48h KF session gap** | Low | Customer returns via chat history; new link if expired |
| **Compliance: 不在聊天决定保障** | High (existing) | H5 also must not show OCR/coverage conclusions — upload only |

---

## F. Final Recommendations

### F.1 短期怎么做？（2–4 weeks, Chen Kui pilot）

1. **Keep WeCom KF chat** as sole customer entry — no channel migration.
2. **Ship P19D-1 strict chat guardrail** per `p19d0` (quarantine, bulk pause, promote split).
3. **Design + ship H5 guided task page MVP (P19D-1.5)** for photo slots only:
   - Bot sends signed link when `current_slot` needs image proof.
   - Text fields stay in chat.
4. **Workbench:** optional “Copy task link” for broker manual resend.

### F.2 中期怎么做？（1–3 months post-pilot）

1. **Mini program** mirroring H5 slot wizard — better UX, `wx.chooseMedia({ count: 1 })`, `openCustomerServiceChat` return.
2. **Template cards** in KF (jump to MP/H5) instead of plain URL text.
3. **Broker 企微侧边栏** — case summary + send link + quarantine count (broker efficiency).
4. **P19C OCR** on promoted primaries only — never in chat/H5 customer UI.

### F.3 是否需要小程序？

| Timeframe | Answer |
|-----------|--------|
| **Pilot (now)** | **No** — H5 sufficient to prove guided upload value |
| **6+ months** | **Yes** — if Chen Kui customers adopt willingly; matches 微保/平安 industry pattern; better retention and notify |

### F.4 H5 task page 是否更快？

**Yes.**

| Dimension | H5 | Mini Program |
|-----------|-----|--------------|
| Time to MVP | 1–2 sprints | 4–8+ weeks (审核+开发) |
| Upload control | ~80% of MP | 100% |
| Identity | Token-based | openid + binding |
| Existing stack fit | Vercel + Cloud Run | New deployable + 微信后台 |

### F.5 是否仍保留 WeCom chat？

**Yes — non-negotiable.**

| Reason | Detail |
|--------|--------|
| Customer habit | Chinese insurance customers expect 微信沟通 |
| Trust | “陈总会人工确认” lives in chat |
| Low-friction text | VIN/ZIP/date faster in chat than opening pages |
| Notify | KF push brings customer back |
| P19A/B investment | Sunk and correct — chat is the nervous system |

Remove chat photo acceptance entirely would **increase** friction without removing need for human dialogue.

### F.6 P19D-1 应该做什么？

Align P19D-1 with **two tracks** (documentation split; implementation can sequence):

#### Track A — P19D-1 (chat guardrail, per P19D-0)

| # | Deliverable |
|---|-------------|
| 1 | `upload_guardrail.py` — slot limits, bulk detector, promote/quarantine |
| 2 | `current_slot_id` + `slot_max_primary` on case JSON |
| 3 | Attachment `intake_status`: `promoted` \| `quarantined` \| `superseded` |
| 4 | Strict customer copy + claim sub-batch confirm |
| 5 | Workbench quarantine badge (read-only expander) |
| 6 | Tests: 1→promote; 4→pause; claim 5+5 |

#### Track B — P19D-1.5 spec (channel — from this recon)

| # | Deliverable |
|---|-------------|
| 1 | `task_token` mint/validate API contract |
| 2 | H5 page spec: one slot, preview, confirm (wireframe + copy) |
| 3 | Upload endpoint → same GCS metadata shape as P19A (`source: h5_task`) |
| 4 | Post-upload WeCom notify hook |
| 5 | Chat message template: link card text for each slot type |

**P19D-1 does NOT require mini program.**  
**P19D-1 SHOULD NOT block on H5** — guardrail ships first; H5 follows immediately after.

#### Deferred (P19D-2+)

- Start Card + upload-intent buttons that **open H5** instead of “please send image in chat”
- Slot checklist UI write path in Workbench
- Mini program
- Broker side panel

---

## G. Reference Architecture — End-to-End (Add Vehicle example)

```text
Customer: 「明天提新车」
  → Chat: Start Card [开始]
  → Chat: 「第一步请打字发 VIN，或点链接拍 VIN 照」
       ├─ Text VIN ──────────────────────► slot filled (chat)
       └─ Tap link ─► H5 slot_vin_photo ─► preview ─► confirm ─► GCS
  → Chat: 「收到。请点链接上传行驶证」
       └─ H5 slot_registration (max 1 primary; widen to 2 via second link)
  → Chat: 「提车日期？」 (text)
  → Chat: E1 End Card when checklist complete
  → Workbench: broker Confirm
```

---

## H. Recon Verdict

| Question | Answer |
|----------|--------|
| Can WeChat chat alone match Spark Driver upload discipline? | **No** — platform picker allows bulk |
| Best channel combo for insurance intake? | **Chat entry + H5/MP task page + Workbench** |
| Fastest path to one-image + preview? | **H5 task page with JSSDK** |
| Keep WeCom chat? | **Yes** — entry, text, notify, trust |
| Need mini program for pilot? | **No** |
| Need mini program medium-term? | **Yes** — if pilot validates link-jump UX |
| P19A/P19B impact? | **Additive** — new upload source; same GCS/Workbench |
| P19D-1 scope? | **Chat guardrail first** + H5 token/spec in parallel |
| Code / deploy this loop? | **No** |

### Strongest insight

> **聊天是信任入口，不是取证控件。**  
> Spark wins on **controlled capture surfaces**, not on chat messages. In WeChat ecosystem, that surface is **H5 or 小程序** — chat sends the link and the receipt, Workbench dispatches the case.

---

## Related Documents

| Doc | Role |
|-----|------|
| `docs/p19d0_upload_guardrail_guided_photo_capture_recon.md` | Strict chat guardrail (P19D-1 Track A) |
| `docs/p19_guided_workflow_start_end_card_recon.md` | Slots, states, Start/End Cards |
| `docs/p19_mobile_task_workflow_recon.md` | Spark Driver pattern mapping |
| `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` | P19 technical authority |
| `docs/evidence/p19b_deploy_live_ui_smoke_2026_07_05.md` | P19B live baseline |

### External references (channel capabilities)

| Source | Topic |
|--------|-------|
| [企业微信 — 客户联系「联系我」](https://developer.work.weixin.qq.com/document/path/95724) | QR / MP entry to broker |
| [企业微信 — 模板卡片 jump_list / card_action](https://developer.work.weixin.qq.com/document/path/91770) | Chat → H5/MP jump |
| [企业微信 — 微信小程序打开微信客服](https://developer.work.weixin.qq.com/document/path/97013) | MP ↔ KF return path |
| [微信开放文档 — wx.chooseMedia](https://developers.weixin.qq.com/miniprogram/dev/api/media/video/wx.chooseMedia.html) | `count: 1` single image |
| [微信开放文档 — 客服消息 / 小程序卡片](https://developers.weixin.qq.com/miniprogram/introduction/custom) | Chat message types |

---

*P19D-0.5 channel recon — documentation only. STOP.*
