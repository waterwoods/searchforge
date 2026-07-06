# P19D-1.5 — H5 Guided Task Page UX Simulation / Best Practice Recon

**Date:** 2026-07-06  
**Revision:** 2026-07-06 — aligned to P19D step-by-step evidence capture SSOT  
**Type:** UX simulation + channel best-practice recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19D implementation agents  
**Prerequisite:** P19A (media intake) ✅ · P19B (Workbench attachments) ✅ · P19D-1 (strict chat guardrail) ✅ · P19D-0 / P19D-0.5 channel recon ✅

**SSOT:** `docs/p19d_core_step_by_step_evidence_capture_doctrine.md` — product doctrine. This doc = H5 UX simulation and channel split.

**Core question:** Can **WeCom chat entry + H5 single-slot guided task page + Workbench** deliver DoorDash/KYC-style **one-step-one-evidence** capture for Chen Kui pilot — without a mini program first?

**This loop:** No code. No deploy. No schema migration.

---

## 0. Executive Summary

**Product framing (SSOT):** H5 is the **primary photo surface** — not “optional upload page.” Chat (P19D-1 guardrail) is the **fallback** when customers ignore links and bulk-send in WeCom.

**Simulated verdict:** The three-layer pattern **can reach ~75–85% of Spark/KYC upload discipline** for photo-proof steps. It will **not** match native-app fluidity on camera latency, offline, or zero-context-switch — but it is **good enough for paid pilot** if H5 is **required** for every photo step (not optional).

| Layer | Spark-like score (1–5) | Role |
|-------|:----------------------:|------|
| WeCom chat | 4 entry / 1 upload control | Intent, Start, text fields, notify, trust |
| H5 guided task | 4 | One slot, one image, preview, confirm |
| Workbench | 5 broker console | Review, quarantine, re-prompt |
| **Combined pilot** | **~4** | Viable MVP; mini program later for polish |

**Recommendation:**

| Question | Answer |
|----------|--------|
| H5 as pilot MVP? | **Yes** — fastest path to proactive upload control |
| Max experience risk | **Context switch + link trust + JSSDK fragility** |
| Minimal viable improvement | Signed one-slot links + preview confirm + auto-return notify in chat |
| H5 before mini program? | **Yes for pilot**; MP when adoption + volume justify 审核 cost |
| Code / deploy this loop? | **No** |

---

## 1. Reference Flow — Add Vehicle (Simulated Walkthrough)

This section simulates the **happy path** the product team asked to validate.

### 1.1 End-to-end journey (customer lens)

```text
[WeCom KF chat]
  Customer: 我要加车
      ↓
  Bot: Start Card — 「开始补资料」按钮 + 说明陈总人工确认
      ↓
  Customer taps: 开始
      ↓
  Bot: 「第一步：请拍 VIN 照片」+ H5 链接（signed token, slot=vin_photo）
      ↓
[WeChat built-in browser — H5]
  Page: 第 1 步 / 共 4 步 · VIN 照片 · 示例图
  Customer taps: 拍照 / 从相册选择（count=1）
  Full-screen preview → 「确认上传」 / 「重拍」
      ↓
  POST upload → GCS → case slot_vin_photo = received
      ↓
  H5: 「已收到，请返回微信查看下一步」+ optional 「继续下一步」按钮
      ↓
[WeCom KF chat]
  Bot: 「VIN 照片已收到。请点链接上传行驶证。」+ link (slot=registration)
      ↓
[H5 — registration]
  Same pattern: 1 image · preview · confirm
      ↓
[WeCom KF chat]
  Bot: 「行驶证已收到。请点链接上传保险卡（如有）。」
      ↓
[H5 — insurance_card, optional]
  Customer skips OR uploads 1 image
      ↓
[WeCom KF chat]
  Bot: E1 — 「资料已收齐，已转陈总人工确认」
      ↓
[Broker Workbench]
  Chen Kui: case checklist green · 3 promoted attachments · source=h5_task · no quarantine
```

### 1.2 Spark Driver parallel

| Spark step | Add Vehicle + H5 equivalent |
|------------|---------------------------|
| Arrive at store | Customer already in WeCom chat (trust established) |
| Start task | Start Card tap → draft case |
| Next item prompt | Chat text + H5 link for current slot only |
| Scan / photo proof | H5 camera with `count: 1` |
| Verify correct | Preview screen — customer confirms before upload |
| Add to basket | Attachment promoted to slot; checklist advances |
| Repeat | Next slot link in chat |
| Final review | Broker Workbench (not customer) |
| Complete | E1 End Card in chat |

**Gap vs Spark:** Each photo step requires **leave chat → open browser → return chat**. Spark never leaves the task shell.

---

## 2. Friction Analysis — Where Experience May Not Feel Smooth

### 2.1 Context-switch tax (highest structural friction)

| Moment | Friction | Severity |
|--------|----------|:--------:|
| Chat → tap link → H5 loads | 1–3 s load; user leaves familiar chat UI | **High** |
| H5 → upload → return WeChat manually | WeChat does not auto-close browser; user must swipe back | **High** |
| Chat → second link for next slot | Feels like "again?" if copy doesn't explain progress | Medium |
| Broker review (async) | Customer waits without in-app progress bar in chat | Medium |

**Simulation note:** A customer who expects "everything in chat" will feel the **first link jump** most sharply. After 2 successful cycles, friction drops if chat messages clearly show **第 2 步 / 共 4 步**.

### 2.2 Link presentation in chat

| Pattern | Smoothness | Pilot fit |
|---------|:----------:|:---------:|
| Plain URL text | Low — looks spammy / untrusted | Avoid |
| Template card「开始上传 VIN」| High — thumb-sized, branded | Best when API available |
| `msgmenu` button opening URL | Medium-high | Good MVP fallback |
| Long explanatory text + link at bottom | Low — link buried | Avoid |

### 2.3 Camera / picker UX inside H5

| Issue | When | Mitigation |
|-------|------|------------|
| JSSDK `wx.config` fail | Wrong domain, HTTP, signature expiry | Pre-flight domain whitelist; retry banner |
| Android vs iOS picker差异 | Some Android WebViews ignore `count:1` | Server-side reject multi; show error |
| Album multi-select anyway | User selects 9 photos | H5 UI: take first only + warn |
| Low light / blur | Real garage photos | Preview + 「不太清楚？重拍」; no OCR promise |
| Permission denied | First camera use | Inline copy + 「去设置开启相机」 |

### 2.4 Text fields vs H5 (intentional split)

Add Vehicle also needs `delivery_date`, `zip`, `phone` — **better in chat** than H5 forms.

| Risk | Cause |
|------|-------|
| User confused why some steps are links, some are typing | Mixed modality without explanation |
| User sends VIN as text while on photo step | Duplicate paths — need chat to accept text fallback on vin slot |
| User uploads registration photo in chat instead of H5 | P19D-1 quarantine — feels punitive if not warned upfront |

**Mitigation copy:** 「照片请点链接上传（一次一张，减少传错）；日期、邮编、电话可以直接在微信里打字发给我们。」

### 2.5 Timing and session

| Scenario | Friction |
|----------|----------|
| Link expires (30–60 min TTL) | Customer returns tomorrow → dead link → frustration |
| Customer closes H5 mid-upload | Slot stays `prompted`; needs resume link |
| 48h KF session limit | Old chat buried; customer can't find link |

---

## 3. Where Users May Get Lost

### 3.1 Lost-in-journey map

```text
                    ┌─────────────────────────────────────┐
                    │  "I'm in chat — why open a webpage?" │
                    └──────────────────┬──────────────────┘
                                       │ no trust copy on card
                    ┌──────────────────▼──────────────────┐
                    │  H5 loaded — which car / which case? │
                    └──────────────────┬──────────────────┘
                                       │ token ok but no case label
                    ┌──────────────────▼──────────────────┐
                    │  Uploaded — now what? Stay or go back?│
                    └──────────────────┬──────────────────┘
                                       │ no explicit "返回微信"
                    ┌──────────────────▼──────────────────┐
                    │  Back in chat — no new message yet   │
                    └──────────────────┬──────────────────┘
                                       │ notify delay >5s
                    ┌──────────────────▼──────────────────┐
                    │  Next link looks same as last link   │
                    └──────────────────┬──────────────────┘
                                       │ URL not humanized; slot name in copy only
                    ┌──────────────────▼──────────────────┐
                    │  "I'm done" but broker still needs phone│
                    └─────────────────────────────────────┘
```

### 3.2 Confusion by persona

| Persona | Likely confusion | Design response |
|---------|------------------|-----------------|
| 年长客户 | Fear of phishing links | Chen Kui name + 「陈奎保险服务」header on H5; short TTL explained |
| 着急提车客户 | Skips steps, bulk sends in chat | Start message: 「请按顺序一步一步来，比一次性发图更快」 |
| 英文为主客户 | Bilingual clutter | H5: ZH primary, EN subtitle one line |
| 多事项客户 | Add car + claim in parallel | B0 one-flow rule; secondary topic deferred in chat |
| 转发链接的家人 | Wrong person uploads | Token bound to `external_userid`; show 「请本人操作」 |

### 3.3 Navigation anti-patterns to avoid

| Anti-pattern | Why users get lost |
|--------------|-------------------|
| H5 multi-tab wizard without chat sync | User doesn't know chat is still "home" |
| H5 shows full 8-field form | Breaks one-step-one-evidence; feels like DMV website |
| Silent upload success (no chat ping) | User uploads 3x thinking it failed |
| Same link for all slots | User re-uploads VIN to registration URL |
| Workbench-only progress | Customer has no visible checklist in chat |

---

## 4. Technical Risk Matrix — H5 in WeChat Ecosystem

### 4.1 Loading

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Cold start on Cloud Run | Medium | 2–4 s white screen | Warm instance; skeleton UI; inline CSS |
| Vercel/CDN blocked in corp WeChat | Low | Total fail | Use same domain as existing QA UI |
| Large JS bundle | Medium | Slow first paint | Minimal H5 — no React app shell; 1 page = 1 slot |
| Mixed content HTTP asset | Low | JSSDK break | HTTPS only |

### 4.2 Login / identity

| Approach | Pilot recommendation |
|----------|---------------------|
| **Signed token in URL (no login)** | ✅ MVP — `case_id + slot_id + external_userid + exp` |
| WeChat OAuth openid | Optional phase 2 |
| SMS OTP | Too heavy for photo step |
| Customer account/password | ❌ Never for this product |

**Binding chain:**

```text
WeCom KF callback → external_userid (anchor)
       ↓
Server mints token when sending link (binds user + case + slot)
       ↓
H5 upload POST validates token → same case as chat session
       ↓
Workbench shows attachment with source=h5_task, slot_assignment set
```

**Leak risk:** Customer forwards link → another WeChat user opens → upload attaches to wrong customer if token not bound to opener.

**Pilot mitigation:** Short TTL + single-use token per slot attempt + H5 shows masked customer label 「张先生，请确认是您本人」.

### 4.3 Return to WeChat

| Method | Works? | Notes |
|--------|:------:|-------|
| User manual swipe back | ✅ | Default; must design for it |
| `WeixinJSBridge.invoke('closeWindow')` | ⚠️ | Sometimes blocked; don't rely solely |
| Mini program `openCustomerServiceChat` | N/A on H5 | MP-only |
| Chat push after upload | ✅ **Required** | KF `send_msg` within 3s of upload |

**Best practice:** H5 success screen = large 「返回微信」instruction + checkmark; backend **always** sends chat ack before user returns.

### 4.4 Resume / breakpoint (断点续传)

| State | Customer experience | System behavior |
|-------|---------------------|-----------------|
| Completed slot 1, closed H5 | Chat already has next link OR bot sends on return | `current_slot_id` advanced |
| Expired token mid-slot | 「链接已过期，请在微信回复"继续"」 | Bot re-mints same slot link |
| Upload failed (network) | H5 retry button; same token if not consumed | Idempotent `upload_session_id` |
| Partial case (2/4 slots) | E2 partial End Card listing gaps | `guided_workflow_state = needs_customer_input` |
| Customer resumes days later | New links for empty slots only | Checklist-driven, not full restart |

**Critical:** Resume must be **chat-commanded** («继续」/「下一步」) — customer should not hunt old links in history.

---

## 5. Is One-Image-Per-Step Too Slow?

### 5.1 Honest assessment

| Dimension | Verdict |
|-----------|---------|
| For **correctness** (broker CA insurance) | **Not too slow** — mis-upload cleanup costs more than extra taps |
| For **impatient提车客户** | **Feels slow** if 4 photo slots = 4 link jumps |
| vs **chat album dump** | One-step is **faster for broker**; ambiguous for customer until educated |

### 5.2 Optimization without breaking guardrail

| Technique | Keeps one-evidence discipline? | Effect |
|-----------|:------------------------------:|--------|
| **「继续下一步」on H5 success** — next slot opens in same browser session | ✅ if still 1 image per page | Removes chat round-trip between slots 2→3 |
| Text fields bundled in chat between photo steps | ✅ | Reduces total "missions" |
| Optional slots skipped with one tap | ✅ | Shorter path for insurance_card |
| Widened slot as **sub-steps** (registration page 1/2) | ✅ | Multi-page notice without multi-select |
| Claim batch wizard (5 photos **inside one H5 session** with per-photo confirm) | ✅ | One link; 5 confirm cycles — not one album dump |
| Chat-side multi-upload | ❌ | Reintroduces P19D-1 quarantine pain |

**Recommended pilot compromise for Add Vehicle:**

```text
Photo path:  vin → registration → [optional insurance_card]
             3 links max, or 2 links if H5 chains slots 2→3 in-browser

Text path:   delivery_date, zip, phone — all in chat, no links
```

**Target:** 2–3 H5 opens total for Add Vehicle, not 7.

---

## 6. Preventing Bulk Upload — Layered Defense

| Layer | Mechanism | Effectiveness |
|-------|-----------|:-------------:|
| **H5 UI** | Single upload button; `chooseImage({ count: 1 })` | **High** (proactive) |
| **H5 preview** | Must tap confirm; no auto-upload | **High** |
| **Server** | Reject >1 file per token consume | **High** |
| **Chat copy** | 「请点链接，不要直接在聊天发多张图」 | Medium |
| **P19D-1 guardrail** | Quarantine chat floods | **Medium** (reactive safety net) |
| **Workbench** | Quarantined section visible to broker | Ops safety |

**Principle:** H5 is **primary prevention**; chat guardrail is **backup** for customers who ignore links.

**Claim Lite exception:** H5 **batch wizard** — customer takes 5 photos sequentially with confirm each time; after batch, screen 「本批已提交，请确认同一次事故后再开始下一批」— mirrors P19D-1 claim batch rule inside controlled UI.

---

## 7. China Industry Practice — Chat + H5 vs Mini Program

### 7.1 What big players actually do

| Player / pattern | Entry | Structured capture | Notify |
|------------------|-------|-------------------|--------|
| **腾讯微保** | 小程序 + 客服 | 小程序分步理赔/投保 | 小程序订阅 + 客服 |
| **平安/人保理赔** | 小程序为主 | 拍照定损 wizard | 小程序消息 |
| **银行/证券开户** | App 或 H5 卡片 | H5 实名/视频见证 | SMS + App push |
| **京东/美团骑手** | Native App | In-app task loop | In-app |
| **中小经纪/SAAS** | 企微客服 + H5 | **H5 链接收资料** | 企微消息 |

**For Chen Kui (US Chinese-speaking auto insurance broker):**

- Customers already use **WeCom 微信客服** — matches 企微+客服 pattern.
- Volume does not yet justify 小程序审核 + 独立获客.
- **H5 is the standard "80% solution"** for broker-led pilots in China fintech before MP.

### 7.2 Chat + H5 vs 小程序 — decision table

| Criterion | 客服 + H5 | 小程序 |
|-----------|:---------:|:------:|
| Time to pilot | **Weeks** | Months |
| Upload control | ~80% | ~100% |
| Customer trust (link) | Medium — needs branding | High — official capsule |
| Identity | Token | openid + unionid |
| Return to chat | Manual / message | `openCustomerServiceChat` |
| Offline / re-open task | Weak | Strong |
| Audit / 类目 | Light | Insurance类目 scrutiny |
| Chen Kui N (est. <200 active) | **Sufficient** | Overkill initially |

---

## 8. When Is H5 Enough? When Must You Upgrade to Mini Program?

### 8.1 H5 is enough when

| Signal | Threshold |
|--------|-------------|
| Pilot customers | < ~500 active; broker can hand-hold |
| Photo steps per case | ≤ 5 per session |
| Text-heavy intake | ≥ 50% fields in chat |
| Team capacity | No dedicated WeChat MP engineer |
| Compliance | Broker confirms all facts anyway |
| Metric | ≥ 70% photo uploads via H5 link (not chat quarantine) |

### 8.2 Upgrade to mini program when

| Signal | Threshold |
|--------|-------------|
| H5 link distrust | > 30% customers refuse to open |
| JSSDK incident rate | > 5% failed uploads due to WebView |
| Resume friction | > 25% abandon mid-checklist |
| Claim photo volume | > 10 photos per case regularly |
| Product maturity | OCR + slot editor + customer self-serve status |
| Business | Branded 「陈奎保险」capsule in WeChat search |
| Regulatory | Insurer partner requires MP filing |

**Sequencing:** H5 validates **slot UX and broker workflow** → MP copies same state machine with better shell.

---

## 9. Per-Lane H5 Design — Smoothest Path

### 9.1 Add Vehicle (`add_car`) — **best fit for H5 pilot**

| Step | Channel | Slot | Notes |
|:----:|---------|------|-------|
| 1 | Chat | Start Card | Create draft case |
| 2 | **H5** | `slot_vin_photo` | Text VIN fallback in chat |
| 3 | **H5** | `slot_registration` | Chain from step 2 success optional |
| 4 | Chat | `field_delivery_date`, `field_garaging_zip` | Faster than form |
| 5 | **H5** (optional) | `slot_insurance_card` | Skip button prominent |
| 6 | Chat | `field_phone` | Confirm gate |
| 7 | Chat | E1 End Card | |
| 8 | Workbench | Broker confirm | |

**Why smoothest:** Fixed sequence, 2–3 photos, high mis-upload cost (wrong VIN/reg).

### 9.2 Premium Review (`policy_review`)

| Step | Channel | Slot | Notes |
|:----:|---------|------|-------|
| 1 | Chat | Start Card | No-quote copy |
| 2 | **H5** | `slot_renewal_notice` OR `slot_dec_page` | Widened: page 1/2 sub-steps if multi-page |
| 3 | Chat | `field_renewal_date`, `current_premium` text | |
| 4 | Chat (optional) | `field_vin_or_vehicle` | |
| 5 | Chat | E1 | |

**Friction risk:** Customer doesn't have renewal notice handy — H5 needs 「暂时没有？先跳过，稍后补发」+ chat nudge.

**Smoother than chat-only:** Multi-page PDF/notice is where album dumps happen; H5 sub-steps help.

### 9.3 Claim Lite (`claim_lite`)

| Step | Channel | Slot | Notes |
|:----:|---------|------|-------|
| 1 | Chat | Safety Start Card | Urgent branch if injury |
| 2 | Chat | `field_accident_time`, `field_location` | Emotional — stay in chat |
| 3 | **H5 batch wizard** | `slot_accident_photos` | 1..5 per batch, confirm batch |
| 4 | Chat | `field_injury_status` | |
| 5 | Chat | E5 safe close | Never claim advice |

**Special H5:** One link opens **in-session multi-photo wizard** (not one link per photo). Each photo: capture → preview → confirm → next. After 5: batch confirm screen.

**Why not pure one-link-per-photo:** Accident stress + many angles; batch wizard matches P19D-1 claim exception without chat album.

### 9.4 Coverage Risk (`coverage_risk`)

| Step | Channel | Slot | Notes |
|:----:|---------|------|-------|
| 1 | Chat | High-risk Start Card | No driving advice |
| 2 | **H5** | `slot_dmv_notice` OR `slot_cancellation_notice` | One notice at a time |
| 3 | Chat | `field_policy_number`, `field_notice_date` | |
| 4 | Chat | E4 safe close | `manual_handle` if "能开车吗" |

**Smoothest:** Single urgent document; H5 prevents wrong photo type. Any driving question → immediate human flag, pause checklist.

---

## 10. MVP Page Structure + User Copy

### 10.1 H5 page anatomy (one slot per page — default)

```text
┌────────────────────────────────────────┐
│ 陈奎保险服务 · 加车资料                    │  ← brand header
│ 张先生 · 请确认本人操作                    │  ← masked identity
├────────────────────────────────────────┤
│ 第 2 步 / 共 4 步                         │  ← progress
│ ● ○ ○ ○   VIN ✓  行驶证  保险卡  完成      │  ← mini stepper
├────────────────────────────────────────┤
│ [ 示例图：行驶证该怎么拍 ]                  │
│                                         │
│ 请上传 行驶证 或 临时牌照                   │  ← slot title ZH
│ Registration or temp plate — 1 photo    │  ← EN one-liner
│                                         │
│ ┌─────────────────────────────────┐    │
│ │     [ 拍照 / 从相册选择 ]          │    │  ← single CTA
│ └─────────────────────────────────┘    │
│                                         │
│ 一次只传一张，上传前可以预览确认              │
│ 经纪人陈总会人工查看，不会自动改保单           │
├────────────────────────────────────────┤
│ 拍不清楚？点此联系陈总                      │  ← exception → manual_handle
│ 隐私说明 · 链接 30 分钟内有效               │
└────────────────────────────────────────┘
```

### 10.2 H5 states + copy

| State | UI | Copy (ZH) |
|-------|-----|-----------|
| **Landing** | Step header + CTA | 请上传 {slot_label}（只需 1 张） |
| **Preview** | Full-bleed image | 请确认照片是否清晰、内容完整 |
| **Preview actions** | Two buttons | 「确认上传」 / 「重拍」 |
| **Uploading** | Spinner | 正在上传，请稍候… |
| **Success** | Checkmark | 已收到。请返回微信，我们会发下一步消息。 |
| **Success + chain** | Second button | 「继续下一步（行驶证）」— optional in-page advance |
| **Error network** | Retry | 上传失败，请检查网络后重试 |
| **Error token** | — | 链接已过期。请在微信回复「继续」，我们会发新链接。 |
| **Wrong file type** | — | 请上传照片（JPG/PNG），PDF 请通过微信发给陈总 |

### 10.3 Chat copy — link send pattern

**After Start (VIN step):**

```text
好的，我们开始加车资料（第 1 步 / 共 4 步）。

请点下面按钮上传 VIN 照片（挡风玻璃或车门上的 17 位车架号）。
一次只传一张，上传前可以先预览确认。

[ 上传 VIN 照片 ]  ← msgmenu or template card

如果您暂时拍不到，也可以直接打字把 VIN 发给我。
经纪人陈总会人工确认，不会自动修改您的保单。
```

**After VIN success (chat notify):**

```text
VIN 照片已收到（第 1 步完成 ✓）。

第 2 步：请点链接上传行驶证或临时牌照。
[ 上传行驶证 ]

还缺：提车日期、邮编、联系电话 — 您也可以直接在聊天里打字发给我。
```

**Materials complete (E1):**

```text
您这份加车资料我们已经收齐了（第 4 步完成），已转给陈总人工确认。
我们会尽快跟进，请留意微信消息。

线上不能报价或确认加车完成，陈总会电话联系您。
```

**Nudge away from chat photos:**

```text
为避免资料放错，照片请尽量点链接上传（一次一张）。
如果您在聊天里发图，系统可能只处理第一张，其余需要人工确认。
```

### 10.4 Workbench (broker) — no customer-facing change

| Panel | Shows |
|-------|-------|
| Checklist | Slot states: prompted / received |
| Attachments | `source: h5_task` · Accepted · slot label |
| Quarantine | Chat-origin bulk only (should shrink with H5 adoption) |
| Action | 「复制任务链接」for re-prompt |

---

## 11. Simulated Scenario Results

| Scenario | Smooth? | Notes |
|----------|:-------:|-------|
| A. Happy path Add Vehicle (3 H5 + chat text) | **4/5** | Works if chaining slot 2→3 in browser |
| B. Customer ignores link, sends 3 chat images | **2/5** | P19D-1 quarantine — educate upfront |
| C. Link expired, replies「继续」 | **3/5** | OK if bot re-mints within 10s |
| D. Claim 8 accident photos | **4/5** | H5 batch wizard + 2 batches; not chat |
| E. Coverage + "能开车吗" mid-flow | **3/5** | Must hard-stop to manual_handle |
| F. Family member opens forwarded link | **2/5** | Token binding + 「本人确认」screen |
| G. Broker Workbench review | **5/5** | P19B already supports; add `h5_task` source badge |

---

## 12. Comparison to Spark Driver — Honest Scorecard

| Capability | Spark native | WeCom+H5 pilot | Gap |
|------------|:------------:|:--------------:|-----|
| One task shell | ✅ | ❌ chat+H5 split | Context switch |
| One action per step | ✅ | ✅ H5 | — |
| Preview before submit | ✅ | ✅ H5 | — |
| Block bulk select | ✅ | ✅ H5 (mostly) | Android edge cases |
| Progress visibility | ✅ | ⚠️ chat text stepper | No persistent bar in chat |
| Exception branch | ✅ | ⚠️ manual_handle | Less structured |
| Offline | Partial | ❌ | Network required |
| Broker dispatch console | ✅ | ✅ Workbench | — |
| **Overall** | 5 | **~4** | Acceptable for pilot |

---

## 13. Final Recommendations

### 13.1 H5 as pilot MVP?

**Yes.** Chen Kui pilot can ship **WeCom entry + signed H5 task pages + existing Workbench** without mini program. P19D-1 chat guardrail remains the safety net until H5 adoption is high.

### 13.2 Maximum experience risk

**「跳出聊天 → 不信任链接 → 上传后不知道是否成功 → 不愿再点第二次」**

Compound risk: customer reverts to chat album upload → quarantine → feels broken.

**Mitigation priority:**

1. Template card / branded button (not raw URL)
2. Sub-3s chat ack after every upload
3. Visible progress「第 X 步 / 共 Y 步」in chat and H5
4. In-browser chain for consecutive photo slots (Add Vehicle reg → insurance card)

### 13.3 Minimum viable improvements (before calling it "Spark-like enough")

| # | Improvement | Effort |
|---|-------------|:------:|
| 1 | Signed single-slot token + no login | M |
| 2 | H5 preview confirm + `count:1` | M |
| 3 | Chat notify on every upload success | S |
| 4 | Progress copy in chat + H5 | S |
| 5 | Optional in-H5 next-slot chain (2 photo steps) | M |
| 6 | 「继续」re-mint expired token | S |
| 7 | `source: h5_task` in Workbench badge | S (P19D-2) |
| 8 | Claim batch wizard (special H5 page) | L |

**Do not build for MVP:** OCR on H5, customer login, full MP, PDF upload, slot editor.

### 13.4 H5 first vs mini program first?

| | H5 first | MP first |
|---|:--------:|:--------:|
| Time to validated learning | **Fast** | Slow |
| Upload control | Good enough | Best |
| Chen Kui pilot fit | **Recommended** | Premature |
| Reuse path | MP can copy H5 slot machine | — |

**Recommendation: H5 first.** Plan MP as **P19D-3+** when pilot metrics justify it.

### 13.5 Suggested implementation sequence (SSOT §F — future loops)

```text
P19D-1   ✅ Chat strict guardrail (deployed QA) — fallback only
P19D-2   Single-slot H5: signed token + VIN photo page ONLY (NOT multi-image upload page)
         · count=1 · preview · confirm · submit · slot metadata · chat notify
P19D-2.5 Registration single-slot page + optional in-H5 step chain
P19D-3   Template card links + consecutive slot chain without chat between photo steps
P19D-4   Claim batch H5 wizard (5 + confirm per batch)
P19D-5+  Mini program (optional — NOT pilot blocker)
```

**P19D-2 explicit non-goals:** multi-image upload UI, album-first page, OCR on H5, customer login, slot editor, broker confirm facts.

---

## 14. Constraints This Loop

| Item | Status |
|------|--------|
| Code changed | **No** |
| Deploy | **No** |
| Schema migration | **No** |
| OCR / LLM on H5 | **Not proposed** |

---

## 15. GO / HOLD

| Gate | Verdict |
|------|---------|
| **Doctrine SSOT adopted** | **GO** — `docs/p19d_core_step_by_step_evidence_capture_doctrine.md` |
| **H5 single-slot guided capture as pilot MVP** | **GO** — proceed to P19D-2 (VIN first) |
| **P19D-2 multi-image upload page** | **HOLD / REJECT** |
| **Skip H5, chat-only** | **HOLD** — P19D-1 guardrail necessary but insufficient |
| **Build mini program now** | **HOLD** — validate H5 with Chen Kui first |
| **This recon loop** | **COMPLETE** — STOP |

---

*End P19D-1.5 — no code, no deploy.*
