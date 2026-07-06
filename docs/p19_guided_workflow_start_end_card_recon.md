# P19B-0 — Guided Workflow / Start-End Card / Attachment State Recon

**Date:** 2026-07-05  
**Revision:** 2026-07-06 — aligned to P19D step-by-step evidence capture SSOT  
**Type:** Product design recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19B/P19C/P19D implementation agents  
**Prerequisite:** P19A Loop 1 (media intake foundation) + P19A Loop 2 (live WeCom image smoke **PASS**)

**SSOT:** `docs/p19d_core_step_by_step_evidence_capture_doctrine.md` — canonical product doctrine. This doc = Start/End Cards, slots, copy detail.

**Authority:** Extends `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` and `docs/p19_mobile_task_workflow_recon.md`. Does not supersede B0 contract (`docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`) or Constitution safety rules.

**This loop:** No code. No deploy. No schema changes.

---

## 0. Executive Summary

P19A proved the **attachment foundation**: WeCom image → download → GCS → metadata → case bind or unassigned holding case → safe customer ack.

P19B-0 designs the **DoorDash / KYC / Spark Driver-style guided workflow** layer on top:

> **Start Card → one slot / one action at a time → preview confirm (H5) → submit evidence → next step → broker review → End Card**

The customer is not in a free-form chat and is **not** asked to「上传资料」. They are told **what to capture now** — e.g.「现在请拍 VIN」— one evidence at a time. P19D-1 chat guardrail is a **fallback** when they ignore links and dump photos in chat.

**Core insight (carry forward):**

```text
KYC:       front of ID → confirm → back of ID → confirm
Spark:     arrive → scan barcode → verify item → next item → complete
Insurance: Start → slot_1 photo → confirm → slot_2 photo → confirm → text fields → broker → End
           NOT: album dump → system guesses slots
```

**What P19B-0 adds vs P19 UX recon:** concrete Start/End Card copy, `guided_workflow_state` enum, per-lane attachment slot matrix, multi-image rules, OCR draft boundary, Workbench panel layout, customer next-step catalog, and exception path table — all implementation-ready for P19B/D without schema migration.

---

## 1. Start Card Design

Start Cards are **WeCom `msgmenu` task cards** — thumb-first, bilingual, one lane per card. A Start Card **does not** create official case truth; it opens a **Draft** case (Add Vehicle) or a **minimal lane case** (other lanes) and sets `guided_workflow_state = draft_started`.

### 1.1 Shared Start Card anatomy

| Element | Purpose |
|---------|---------|
| **Head** | One-sentence task description + broker gate ("陈总会人工确认") |
| **Buttons** | Primary = Start; Secondary = Later / Talk to Broker |
| **Tail** | Safety / scope boundary (no auto-quote, no coverage decision) |
| **On Start click** | Create case → bind `external_userid` → set active flow → send **first guided prompt** (one item only) |
| **On Later** | No case; log intent only (B0 pattern) |
| **On Talk to Broker** | No case; flag `customer_requested_human`; broker notified via Workbench |

**Invariant (B0 Rule 8):** Only one active business flow per customer. Start Card for lane B is **blocked or deferred** if lane A flow is open — customer gets secondary-topic deferral copy instead.

---

### 1.2 Add Vehicle Start Card

**Trigger:** High-confidence `add_car` intent ("明天提新车", "加一台车", VIN + delivery context).

**Head:**
```
I can help you add a vehicle to your policy. Your broker reviews everything before anything changes.
我可以帮您把新车加到保单里。经纪人会先审核，任何变更前都会确认。
```

**Buttons:**

| id | Label | Action |
|----|-------|--------|
| `start_add_car` | Start / 开始 | Create Draft `add_car` case |
| `start_add_car_decline` | Later / 稍后 | No case |
| `start_add_car_broker` | Talk to Broker / 联系经纪人 | Human flag only |

**Tail:**
```
We'll ask for a few photos and details — no long forms.
我们会引导您上传几张照片和少量信息，不用填长表格。
```

**First guided prompt (immediately after Start):**
```
好的，我们开始加车资料。
第一步：请拍一张 **VIN 照片**（挡风玻璃或车门贴纸上的 17 位车架号）。
如果暂时拍不到，也可以直接打字发 VIN。
```

**Canonical 5-step flow (SSOT §B):** Start Card → (1) VIN photo → (2) registration photo → (3) insurance card optional → (4) delivery date text → (5) broker review → End Card「资料已收到，陈总会人工确认」.

**Interaction rule (SSOT §C):** Never ask「请上传车辆资料」— always name the **current** slot:「现在请拍 VIN」. Multi-sided docs = **multiple steps**, not one multi-image upload.

**Optional upload-intent buttons (P19D — after Start):**

| id | Label |
|----|-------|
| `upload_vin_photo` | 我上传 VIN 照片 |
| `upload_registration` | 我上传行驶证/临牌 |
| `upload_insurance_card` | 我上传保险卡 |

**First-step materials priority:** `vin_photo` → `registration` → `delivery_date` (text) → `zip` (text) → `insurance_card` (optional).

---

### 1.3 Premium Review Start Card

**Trigger:** `policy_review` intent ("保险又涨了", "续保太贵", renewal concern).

**Note:** Today minimal lane auto-creates case on first message. P19D should add explicit Start Card for consistency — or treat first intent message as implicit start with immediate guided prompt. **Design target:** explicit Start Card.

**Head:**
```
I can help organize your renewal / premium review for your broker. We do not quote online.
我可以帮您整理续保/保费检视资料给经纪人。线上不会直接报价。
```

**Buttons:**

| id | Label | Action |
|----|-------|--------|
| `start_premium_review` | Start / 开始 | Create `policy_review` case |
| `start_premium_decline` | Later / 稍后 | No case |
| `start_premium_broker` | Talk to Broker / 联系经纪人 | Human flag |

**Tail:**
```
Please have your renewal notice or declaration page ready to photograph.
请准备好续保通知或保单首页（declaration page）拍照上传。
```

**First guided prompt:**
```
我们开始整理保费检视资料。
请先发 **续保通知 (renewal notice)** 或 **保单首页 (dec page)** 的照片或 PDF。
```

**Upload-intent buttons (P19D):**

| id | Label |
|----|-------|
| `upload_renewal_notice` | 我上传续保通知 |
| `upload_dec_page` | 我上传保单首页 |
| `upload_premium_letter` | 我上传保费账单 |

---

### 1.4 Claim Lite Start Card

**Trigger:** `claim_intake` intent ("撞车了", "出事故了", accident report).

**Head:**
```
I'm sorry to hear about the accident. First — is everyone safe?
很抱歉听到您发生事故。请先确认大家是否安全。
```

**Buttons:**

| id | Label | Action |
|----|-------|--------|
| `start_claim_lite` | I'm safe — continue / 人都安全，继续 | Create `claim_lite` case |
| `start_claim_urgent` | Someone may be hurt / 可能有人受伤 | Create case + `manual_handle` + urgent flag |
| `start_claim_broker` | Talk to Broker / 联系经纪人 | Human flag |

**Tail:**
```
We collect photos and facts only. We cannot decide fault or whether to file a claim.
我们只收集照片和事实，不能判断责任或是否该报案。
```

**First guided prompt (safe path):**
```
请先确认安全。如果方便，请发 **事故现场照片**（车损、车牌、路况）。
也可以补充：事故时间、地点。
```

**Upload-intent buttons (P19D):**

| id | Label |
|----|-------|
| `upload_accident_photos` | 我上传事故照片 |
| `upload_police_report` | 我上传警方报告 |
| `upload_other_party_info` | 我上传对方信息 |

**Safety-first:** If injury markers detected in text, skip photo checklist → urgent ack + `manual_handle` immediately.

---

### 1.5 Coverage Risk Start Card

**Trigger:** `coverage_risk_intake` intent ("DMV 说我没保险", cancellation, lapse, "能开车吗").

**Head:**
```
This sounds like a coverage status concern. Your broker must verify — we cannot confirm coverage online.
这属于保单状态/停保类问题，需要经纪人核实。线上不能确认您是否有保障。
```

**Buttons:**

| id | Label | Action |
|----|-------|--------|
| `start_coverage_risk` | Start / 开始 | Create `coverage_risk` case + high-risk flags |
| `start_coverage_broker` | Talk to Broker now / 立即联系经纪人 | Human flag + urgent |
| `start_coverage_decline` | Later / 稍后 | No case |

**Tail:**
```
Do not drive until your broker confirms your status. We cannot advise whether you are covered or allowed to drive.
在经纪人确认前请勿自行判断是否可开车。我们不能告诉您是否有保障或是否可以上路。
```

**First guided prompt:**
```
请发 **DMV 通知** 或 **停保/取消通知** 的照片。
如果有保单号，也可以打字发给我们（经纪人会核实）。
```

**Upload-intent buttons (P19D):**

| id | Label |
|----|-------|
| `upload_dmv_notice` | 我上传 DMV 通知 |
| `upload_cancellation_notice` | 我上传停保/取消通知 |
| `upload_policy_docs` | 我上传保单相关文件 |

**No "I'm safe" button** — this lane is document-first, not safety-confirm like Claim Lite.

---

### 1.6 Start Card × lane summary

| Lane | Case type | First proof asked | Broker gate copy |
|------|-----------|-------------------|------------------|
| Add Vehicle | `add_car` Draft | VIN photo | 经纪人确认后才会处理加车 |
| Premium Review | `policy_review` | renewal notice / dec page | 不会线上报价 |
| Claim Lite | `claim_lite` | safety → accident photos | 不判断责任/是否报案 |
| Coverage Risk | `coverage_risk` | DMV / cancellation notice | 不确认保障/不建议开车 |

---

## 2. End Card Design

End Cards are **terminal customer messages** sent when a workflow phase completes. They are **not** policy confirmations. Tone: received → broker will follow up → what customer can expect next.

**Invariant:** End Card never implies coverage active/inactive, claim filed, quote approved, or policy changed.

### 2.1 End Card types

| Type | When sent | Customer message (ZH primary) |
|------|-----------|--------------------------------|
| **E1 — Materials complete** | Checklist materially complete; `guided_workflow_state → ready_for_broker_review` | 您这份资料我们已经收齐了，已转给陈总人工确认。我们会尽快跟进，请留意微信消息。 |
| **E2 — Partial complete** | Customer paused or broker marked waiting; still missing items | 目前已收到部分资料。还缺：**{missing_list_zh}**。您方便时请继续发照片或补充信息。陈总会人工确认已收到的内容。 |
| **E3 — Broker handoff** | Broker clicked Confirm / Mark manual handle / explicit handoff | 您的资料已转陈总人工处理。我们会通过电话或微信跟进，请保持手机畅通。 |
| **E4 — Coverage Risk safe close** | High-risk lane; intake complete or broker closed with safety copy | 您的通知我们已收到并转陈总核实保单状态。线上不能判断您是否有保障，也不能建议您是否可以开车。陈总会尽快联系您。 |
| **E5 — Claim Lite safe close** | Photos received; broker will call | 事故照片和资料我们已收到，已转陈总人工跟进。我们不能判断责任或是否该报案，陈总会电话联系您。请先确保人身安全。 |
| **E6 — Declined / Later** | Customer tapped Later on Start Card | 没关系，准备好时随时回复我们即可。 |
| **E7 — Add Vehicle broker confirmed** | B0 Done Card (existing) | 陈奎团队已收到您的请求，我们会跟进后续步骤。（B0 contract — not "policy updated"） |

### 2.2 End Card forbidden phrases

| Forbidden | Why |
|-----------|-----|
| "您的保险有效/无效" | Coverage decision |
| "可以/不可以开车" | Driving advice |
| "建议您报案/不要报案" | Claim advice |
| "保费是 $X" / "可以帮您省钱 $X" | Quote promise |
| "加车已完成" / "保单已更新" | Policy change claim |
| "OCR 已识别 VIN 为 …" | Exposes draft as truth |
| "理赔已通过" | Claim decision |

### 2.3 End Card trigger matrix

| Trigger | End Card type | `guided_workflow_state` after |
|---------|---------------|-------------------------------|
| Checklist all `received` or `confirmed` | E1 | `ready_for_broker_review` |
| Customer idle 24h+ with gaps | E2 (optional nudge) | `needs_customer_input` |
| Broker Confirm (B0) | E7 | `confirmed` |
| Broker Mark manual handle | E3 | `manual_handle` |
| Coverage Risk intake done | E4 | `ready_for_broker_review` |
| Claim Lite photos received | E5 | `ready_for_broker_review` |
| Broker closes case | E1 or E3 variant | `closed` |

---

## 3. Case Workflow State

### 3.1 Design principle

Use a **single additive JSON field** `guided_workflow_state` on case `extra` (or top-level case JSON) — no new DB tables, no `case_status` enum collision. Existing `case_status` (`new`, `reviewing`, `waiting_client`, `closed`, …) remains for broker queue semantics.

`guided_workflow_state` describes **customer-facing guided task progress**. `case_status` describes **broker queue position**. Both can be read together in Workbench.

### 3.2 State enum

| State | Meaning | Customer sees | Broker sees |
|-------|---------|---------------|-------------|
| `draft_started` | Start Card accepted; case exists; checklist initialized | First guided prompt | New case, empty slots |
| `collecting_documents` | Active guided loop; awaiting next proof | "请上传 {next_slot}" | Partial checklist, attachments arriving |
| `needs_customer_input` | Waiting on customer text or photo; may have sent E2 | "还缺 …" or upload button | `still_needed_fields` + missing slots |
| `ready_for_broker_review` | Checklist materially complete OR customer done uploading | E1 ack; "陈总会确认" | Review queue; all slots `received`+ |
| `broker_reviewing` | Broker opened case; may be requesting clearer photo | "陈总正在查看" (only if broker sends) | Active review |
| `confirmed` | Broker Confirm (B0 `broker_confirmed_at` set) | E7 Done Card | Active case |
| `closed` | Case archived / resolved | No further prompts | Archived |
| `manual_handle` | Urgent, emotional, complex, or safety lane escalation | E3 / E4 / E5 safe close | `manual_followup_needed` flag |
| `unassigned_document` | Attachment on holding case (`wecom_media_intake`) or unbound | Lane disambiguation menu | Unassigned queue |

### 3.3 State transition diagram

```text
                    ┌─────────────────┐
                    │  (no case yet)  │
                    └────────┬────────┘
                             │ Start Card tap
                             ▼
                    ┌─────────────────┐
         ┌─────────│  draft_started   │─────────┐
         │         └────────┬────────┘         │
         │                  │ first prompt     │
         │                  ▼                    │
         │         ┌─────────────────┐       │
         │    ┌───│collecting_docs   │───┐   │
         │    │   └────────┬────────┘   │   │
         │    │            │            │   │
         │  re-ask      slot filled   exception
         │    │            │            │   │
         │    └────────────┼────────────┘   │
         │                 ▼                │
         │         ┌─────────────────┐     │
         │         │needs_customer_  │     │
         │         │     input       │◄────┘
         │         └────────┬────────┘
         │                  │ checklist complete
         │                  ▼
         │         ┌─────────────────┐
         │         │ready_for_broker_│
         │         │    review       │
         │         └────────┬────────┘
         │                  │ broker opens
         │                  ▼
         │         ┌─────────────────┐
         │         │broker_reviewing │
         │         └────────┬────────┘
         │           ┌──────┼──────┐
         │           ▼      ▼      ▼
         │      confirmed closed manual_handle
         │
         └─ unassigned_document (parallel path for orphan media)
```

### 3.4 Mapping to existing fields

| Existing field | Relationship |
|----------------|--------------|
| `broker_confirmed_at` | When set → `guided_workflow_state = confirmed` |
| `still_needed_fields` | Drives `needs_customer_input` vs `collecting_documents` |
| `case_status` | Independent; broker can set `reviewing` while guided state is `ready_for_broker_review` |
| `manual_followup_needed` | Implies `manual_handle` or flags within `broker_reviewing` |
| `collection_stage` | Legacy; align `collecting` ↔ `collecting_documents` in UI only |

### 3.5 Checklist item state (per slot)

Each attachment slot has its own sub-state:

| Slot state | Meaning |
|------------|---------|
| `needed` | Required; not yet received |
| `prompted` | System asked customer for this slot |
| `received` | Attachment stored; not broker-confirmed |
| `needs_reshoot` | Blurry / wrong type; customer asked to re-upload |
| `confirmed` | Broker confirmed document + key fields |
| `waived` | Broker marked optional slot as not required |
| `missing` | Required but customer said unavailable |

Store as `document_checklist: { slot_id: { state, attachment_ids[], last_prompted_at } }` in case JSON — **additive, no migration**.

---

## 4. Checklist / Attachment Slot Design

An **attachment slot** is a named place in the checklist that accepts one or more attachments of a given document type. Slots drive guided prompts and Workbench gap display.

### 4.1 Add Vehicle (`add_car`)

| Slot ID | Document type(s) | Required | Field fallback (text) | Guided prompt (ZH) |
|---------|------------------|----------|----------------------|-------------------|
| `slot_vin_photo` | `vin_photo` | **Yes** | `vin` text | **现在请拍 VIN 照片**（一步一图） |
| `slot_registration` | `registration` | **Yes** | — | **现在请拍行驶证** — 正/反面分两步，不要一次传两张 |
| `slot_insurance_card` | `insurance_card` | Optional | — | **现在请拍保险卡（可跳过）** — 一步一图 |
| `slot_driver_license` | `driver_license` | Optional | — | 如有驾照照片也可以发 |
| `field_delivery_date` | — | **Yes** | `delivery_date` | 请告诉我提车日期 |
| `field_garaging_zip` | — | **Yes** | `zip` | 请发车辆停放地址邮编 |
| `field_primary_driver` | — | **Yes** | `primary_driver` | 请发主驾姓名 |
| `field_phone` | — | **Yes** (broker Confirm gate) | `phone` | 请发联系电话 |

**Guided order (canonical pilot):** `slot_vin_photo` → `slot_registration` → `slot_insurance_card` (opt, skippable) → `field_delivery_date` → broker review → End Card.

*Additional fields (`zip`, `phone`, etc.) remain in full checklist — see broker Confirm gate; pilot H5 MVP may defer non-photo fields to chat text.*

---

### 4.2 Premium Review (`policy_review`)

| Slot ID | Document type(s) | Required | Field fallback | Guided prompt (ZH) |
|---------|------------------|----------|----------------|-------------------|
| `slot_renewal_notice` | `renewal_notice` | **Yes** (one of pair) | — | 请发续保通知照片 |
| `slot_dec_page` | `renewal_notice`, PDF dec page | **Yes** (one of pair) | — | 或发保单首页 (declaration page) |
| `slot_current_premium` | `renewal_notice`, text | Recommended | `current_premium` | 如有当前保费金额，可以打字告诉我 |
| `field_renewal_date` | — | Recommended | `renewal_date` | 续保日期是什么时候？ |
| `field_vin_or_vehicle` | `vehicle_photo` | Recommended | `vin_or_vehicle` | 如有车辆信息/VIN 也请补充 |
| `slot_claim_history` | `claim_document` | Optional | `recent_claim_ticket` | 如近期有理赔，可发相关文件 |

**Rule:** `slot_renewal_notice` OR `slot_dec_page` satisfies document requirement — both preferred.

---

### 4.3 Claim Lite (`claim_lite`)

| Slot ID | Document type(s) | Required | Field fallback | Guided prompt (ZH) |
|---------|------------------|----------|----------------|-------------------|
| `field_safety_confirmed` | — | **Yes** | tap on Start Card | 请确认大家是否安全 |
| `slot_accident_photos` | `accident_photo`, `vehicle_photo` | **Yes** | — | 请发事故现场照片（可多张） |
| `field_accident_time` | — | **Yes** | `accident_time` | 事故大概什么时间？ |
| `field_location` | — | **Yes** | `location` | 事故地点在哪里？ |
| `field_other_party` | — | Recommended | `other_party_info` | 如有对方车牌/保险信息，请补充 |
| `slot_police_report` | `claim_document` | Optional | `police_report` | 如有警方报告可发照片 |
| `field_injury_status` | — | **Yes** | `injury_status` | 有人受伤吗？ |

**Multi-photo:** `slot_accident_photos` accepts **multiple** attachments (see §5).

---

### 4.4 Coverage Risk (`coverage_risk`)

| Slot ID | Document type(s) | Required | Field fallback | Guided prompt (ZH) |
|---------|------------------|----------|----------------|-------------------|
| `slot_dmv_notice` | `dmv_notice` | **Yes** (one of pair) | — | 请发 DMV 通知照片 |
| `slot_cancellation_notice` | `cancellation_notice` | **Yes** (one of pair) | — | 或发停保/取消通知 |
| `field_policy_number` | — | Recommended | `policy_number` | 如有保单号请打字发给我们 |
| `field_notice_date` | — | Recommended | `notice_date` | 通知上的日期是什么时候？ |
| `field_vehicle_info` | — | Optional | `vehicle` | 如有车辆信息也请补充 |

**Rule:** At least one notice document required. Driving questions in text → `manual_handle` immediately; do not proceed checklist until broker engages.

---

## 5. Multi-Image Handling

### 5.1 Scenarios and rules

| Scenario | System behavior | Customer message | Workbench |
|----------|-----------------|------------------|-----------|
| **Multi-image same message** | Process each `msg_id` independently; bind all to same active case; attempt slot assignment by prompt context | 收到 {N} 张图片，已放入您的 case。陈总会人工确认。 | N attachments, same `received_at` batch |
| **Out-of-order upload** | Attach to case; classify each; fill slots opportunistically; prompt for **next empty** required slot | 收到。还缺：{next_gap} | Slots fill non-sequentially; checklist shows what's still `needed` |
| **Duplicate upload (same image re-sent)** | Dedup by `msg_id` (P19A); if new `msg_id` but visually same session, attach but mark `duplicate_of` optional | 这张收到了（与之前一张类似）。陈总会一起查看。 | Show duplicate badge; broker can dismiss |
| **Blurry / unreadable** | Store attachment; slot stays `needs_reshoot`; do not auto-reject storage | 图片收到了，但不太清楚。能再拍一张更亮的 {slot_label} 吗？ | `quality_flag: blurry`; broker can confirm anyway |
| **Uncertain document type** | `document_type = unknown_document`; bind to case; use prompt context for hint | 收到了。请问这是续保通知、行驶证、还是其他资料？ | Low confidence badge; broker sets type |
| **Belongs to another case** | If binding confidence low → unassigned or ask customer | 收到。请问这是针对哪个事项的资料？（加车/保费/理赔/DMV） | Reassign action |
| **No active case** | P19A path: `wecom_media_intake` holding case OR lane disambiguation menu | 收到图片。请问这是加车资料、保单/续保资料、理赔照片，还是 DMV/停保通知？ | Unassigned queue |

### 5.2 Slot assignment priority (multi-image batch)

When multiple images arrive without upload-intent button:

1. Active prompted slot (highest)
2. Upload-intent button context (P19D)
3. Lane default next empty slot
4. Document type classifier (filename, lane, low-confidence vision later)
5. `unknown` → ask customer to label

### 5.3 Multi-image slot cardinality

| Slot | Cardinality |
|------|-------------|
| `slot_vin_photo` | 1 primary (+ extras ok) |
| `slot_registration` | 1 primary |
| `slot_accident_photos` | **1..N** |
| `slot_renewal_notice` | 1..N (multi-page) |
| Notice slots (DMV/cancellation) | 1 primary each |

### 5.4 Dedup layers

| Layer | Key | Scope |
|-------|-----|-------|
| WeCom message | `msg_id` | Never double-process same message |
| Attachment | `attachment_id` | One record per stored file |
| Semantic duplicate (P19D+) | `content_hash` optional | Warn broker; don't block storage |

---

## 6. OCR Draft Flow

### 6.1 Principles

| Principle | Implementation |
|-----------|----------------|
| OCR runs **async** | Queue job after GCS upload; never block WeCom reply |
| OCR result is **draft only** | `attachment.ocr_draft` + `ocr_status: draft` |
| **Broker confirm** → official facts | Selected fields merge to `known_facts` / `collected_fields` with audit |
| **Customer never waits** | No "正在识别…" blocking; no OCR values in customer chat |
| **Customer never sees OCR** | No VIN/policy/premium from OCR in WeCom replies |
| Failed OCR | `ocr_status: failed`; broker uses raw image |

### 6.2 OCR pipeline (P19C)

```text
attachment stored (P19A)
  → ocr_status = queued
  → background worker by document_type
  → ocr_draft = { field: { value, confidence } }
  → ocr_status = draft
  → Workbench shows draft panel
  → broker confirm / correct / ignore per field
  → ocr_status = confirmed (per attachment) OR fields promoted
```

### 6.3 OCR eligibility by document type

| Document type | OCR fields (draft) | Auto-promote |
|---------------|-------------------|--------------|
| `insurance_card` | carrier, policy #, VIN, named insured, dates | **Never** |
| `renewal_notice` | carrier, premium, term, vehicles | **Never** |
| `dmv_notice` | notice date, plate/VIN, action required | **Never** |
| `cancellation_notice` | carrier, policy #, cancel date | **Never** |
| `registration` | VIN, plate, year/make | **Never** |
| `vin_photo` | VIN string | **Never** |
| `accident_photo` | classify only — **no liability fields** | **Never** |

### 6.4 OCR ↔ checklist interaction

- OCR draft may **suggest** slot fill (e.g. VIN extracted → highlight `slot_vin_photo` as "draft match") but slot stays `received` until broker confirms.
- OCR must not auto-set `guided_workflow_state` to `ready_for_broker_review`.
- OCR confidence shown only in Workbench.

---

## 7. Workbench Display Design

### 7.1 Case detail — guided workflow panel (P19B+)

```
┌─ Guided Workflow ─────────────────────────────────────┐
│ State: collecting_documents                           │
│ Lane: Add Vehicle                                     │
│ Progress: 3/6 required slots received                 │
├─ Document Checklist ──────────────────────────────────┤
│ [✓] VIN photo          received   att_abc  [Confirm]  │
│ [✓] Registration       received   att_def  [Confirm]  │
│ [ ] Delivery date      needed     —        [Ask cust] │
│ [ ] Garaging ZIP       needed     —        [Ask cust] │
│ [○] Insurance card     waived     —                   │
├─ Attachments ─────────────────────────────────────────┤
│ ┌──────┐ att_abc  vin_photo   high   2026-07-05       │
│ │ thumb│ [Preview] [Reassign] [Set type] [Clearer?]   │
│ └──────┘ OCR: not_started                             │
│ ┌──────┐ att_def  registration med    2026-07-05       │
│ │ thumb│ [Preview] ...                                 │
│ └──────┘ OCR: draft → VIN: ...?? (0.72) [Confirm]   │
├─ Missing ─────────────────────────────────────────────┤
│ delivery_date, zip, phone                             │
├─ Risk flags ──────────────────────────────────────────┤
│ (none)                                                │
└───────────────────────────────────────────────────────┘
```

### 7.2 Per-attachment row fields

| Field | Display |
|-------|---------|
| Thumbnail | Signed URL / auth proxy — **no public URL** |
| `document_type` | Badge + confidence (`high`/`medium`/`low`) |
| `binding_confidence` | Bind quality indicator |
| `attachment_slot` | Which checklist slot |
| `ocr_status` | `not_started` \| `queued` \| `draft` \| `confirmed` \| `failed` |
| `ocr_draft` | Expandable field list with per-field confidence |
| `quality_flag` | `blurry` \| `cropped` \| `duplicate` (optional) |
| Customer | Masked label (`尾号 mxcw`) — **never full `external_userid`** |
| Source | WeCom + `received_at` |

### 7.3 Broker actions

| Action | Effect |
|--------|--------|
| **Confirm document** | Slot → `confirmed`; attachment `broker_confirmed: true` |
| **Confirm OCR field** | Field → `known_facts`; audit trail |
| **Edit field** | Broker override value → `known_facts` |
| **Reject OCR field** | Field stays draft; ignored |
| **Set document type** | Override classifier |
| **Reassign attachment** | Move to another case; update binding |
| **Ask clearer photo** | Slot → `needs_reshoot`; trigger outbound template |
| **Mark manual handle** | `guided_workflow_state → manual_handle` |
| **Waive slot** | Optional slot → `waived` |

### 7.4 Unassigned queue (existing P19A holding path)

```
Unassigned WeCom Attachments
├── customer (masked)
├── preview
├── suggested_lane (if classifier hint)
├── [Attach to case ▼]
├── [Create new case ▼]
└── [Ask customer — send disambiguation menu]
```

---

## 8. Client Guided Next Step

Customer always sees **one primary next action** — never a full checklist dump in chat.

### 8.1 Next-step catalog by phase

| Phase | Example customer message (ZH) |
|-------|--------------------------------|
| Start just tapped | 好的，我们开始。第一步：请发 **VIN 照片**。 |
| Next doc (Add Vehicle) | 收到。下一步请发 **行驶证或临牌** 照片。 |
| Next field (text) | 收到照片。请告诉我 **提车日期**（例如 7 月 10 日）。 |
| Next doc (Premium) | 收到。如有 **保单首页 (dec page)** 也请发一张。 |
| Next doc (Claim) | 收到。请补充 **事故时间** 和 **地点**。 |
| Next doc (Coverage) | 收到。通知上的 **日期** 和 **保单号**（如有）也请告诉我。 |
| Disambiguation | 请问这是 **加车 / 保费 / 理赔 / DMV** 哪类资料？ |
| Blurry re-ask | 图片收到了，但不太清楚。能再拍一张更亮的 **{slot}** 吗？ |
| Wrong type | 这张好像不是续保通知。请发 **续保通知或保单首页** 的照片。 |
| Partial complete | 目前已收到 {received}。还缺 **{missing}**。 |
| All received | 资料已收到，已转陈总人工确认。我们会尽快跟进。 |
| Manual handle | 已转陈总人工处理，我们会电话联系您。 |
| Secondary topic | 收到，我先记录您的问题。我们先完成 **{current_lane}**，陈总会跟进其他事项。 |

### 8.2 Next-step selection algorithm

```text
if unassigned_document:
  → disambiguation menu
elif manual_handle or urgent:
  → safe close (E3/E4/E5); no more checklist prompts
elif active prompted slot in needs_reshoot:
  → re-ask that slot
elif upload_intent_button just clicked:
  → ack + expect that slot type
else:
  → first required slot where state in (needed, prompted)
     order by lane slot priority table (§4)
```

### 8.3 Progress without overwhelming

Optional lightweight progress line (max once per session):

> 加车资料进度：已收到 VIN 照片、行驶证。还差提车日期和邮编。

Never show broker internals (confidence, OCR, case IDs).

---

## 9. Exception Paths

| Exception | Detection | Customer handling | Broker handling | State |
|-----------|-----------|-------------------|-----------------|-------|
| **No active case** | Media arrives; no open case for `external_userid` | Disambiguation menu (P19A template) | Unassigned queue; create or attach | `unassigned_document` |
| **Multiple open cases** | >1 open case same lane or cross-lane | "您有多个进行中的事项，这张是加车还是保费资料？" + menu | Show binding `low`; force reassign | stay on cases |
| **Duplicate image** | Same `msg_id` or semantic dup | Silent dedup or soft ack | Duplicate badge | no change |
| **Wrong document type** | Classifier mismatch or broker reject | "这张好像不是 {expected}，请发 {expected}。" | Set type; slot stays empty | `needs_reshoot` or re-prompt |
| **Blurry image** | Broker flag or future quality scorer | Re-ask clearer photo | `quality_flag: blurry` | `needs_reshoot` |
| **Storage/download failure** | GCS or WeCom API error | "消息收到了，系统正在处理。" (no false success) | Error badge; retry button | event logged; attachment `intake_status: failed` |
| **Coverage-risk safety** | "能开车吗" / DMV / lapse | E4 safe close; **never** answer driving/coverage | `manual_handle` + urgent | `manual_handle` |
| **Claim safety** | Injury markers / "严重" | Urgent ack; broker call; pause photo ask | `manual_handle` + critical urgency | `manual_handle` |
| **New topic mid-flow** | Different intent in open flow | B0 secondary-topic deferral | `claim_mentioned_at` or similar flag | current flow unchanged |
| **Customer idle** | No reply 24h+ | Optional E2 nudge (P19D+; not v1 required) | `needs_customer_input` | — |
| **Broker requests clearer photo** | Manual action | Outbound: "陈总请您补一张更清楚的 {slot}" | Slot `needs_reshoot` | `needs_customer_input` |
| **Attachment to wrong case** | Broker discovers | — (customer not told internals) | Reassign | fix binding |

---

## 10. Red Lines

Non-negotiable across P19B/C/D/E:

| # | Red line | Enforcement |
|---|----------|-------------|
| 1 | **No OCR auto-confirm** | OCR → `ocr_draft` only; broker action required |
| 2 | **No coverage decision** | Never say insured/uninsured in chat or End Card |
| 3 | **No driving advice** | Especially Coverage Risk; redirect to broker |
| 4 | **No claim/liability advice** | Store photos; no fault inference; no file/don't-file |
| 5 | **No quote promise** | Premium lane: organize only; no premium numbers from AI |
| 6 | **No public image URL** | GCS private; signed URL / proxy in Workbench only |
| 7 | **No full `external_userid` display** | Mask suffix in all UI |
| 8 | **No policy change claim** | End Cards say "received" not "updated" |
| 9 | **No customer-facing OCR** | Customer never sees extracted VIN/premium/policy # |
| 10 | **Raw file preserved** | No delete on OCR fail or reclassify |
| 11 | **One flow at a time** | B0 Rule 8; secondary topics deferred |
| 12 | **Broker Confirm gate** | `broker_confirmed_at` before Active case / Done Card |

---

## 11. Implementation Mapping (P19B / P19C / P19D)

### 11.1 What each loop owns

| Loop | Owns from this recon |
|------|---------------------|
| **P19B** | Workbench attachment panel (§7), slot display, checklist states, broker actions (confirm type, reassign, ask clearer, manual handle), unassigned queue UI |
| **P19D** | Start Cards for Premium/Claim/Coverage (§1), upload-intent buttons, `guided_workflow_state` transitions, customer next-step engine (§8), End Cards E1–E6, exception customer copy (§9) |
| **P19C** | OCR async pipeline (§6), draft panel in Workbench, per-field confirm |

### 11.2 Additive JSON fields (no schema migration)

```json
{
  "guided_workflow_state": "collecting_documents",
  "document_checklist": {
    "slot_vin_photo": {
      "state": "received",
      "attachment_ids": ["att_abc"],
      "last_prompted_at": "2026-07-05T..."
    }
  },
  "last_guided_prompt": {
    "slot_id": "slot_registration",
    "sent_at": "2026-07-05T..."
  }
}
```

Reuse existing `case_attachments[]`, `still_needed_fields`, `collected_fields`, `broker_confirmed_at`.

### 11.3 P19A baseline (already shipped)

| Capability | Status |
|------------|--------|
| WeCom image detect + download + GCS | ✅ Loop 2 PASS |
| Attachment metadata + dedup | ✅ |
| Case bind or `wecom_media_intake` unassigned | ✅ |
| Safe customer ack templates | ✅ |
| Workbench attachment preview UI | ❌ P19B |
| Guided next-step prompts | ❌ P19D |
| OCR draft | ❌ P19C |

---

## 12. Recon Verdict

| Question | Answer |
|----------|--------|
| **Document path** | `docs/p19_guided_workflow_start_end_card_recon.md` |
| **Most important workflow insight** | Insurance intake is a **finite slot-filling state machine**, not chat. Each image fills a **named slot** or triggers an **exception branch**; only the broker promotes evidence to truth. Customer sees **one next step**; Workbench sees **all slots + confidence**. |
| **Recommended loop order** | **P19B → P19D → P19C** (adjust from spec's B→C→D: broker attachment UI first, then customer guided flow, then OCR enhancement) |
| **Safe to proceed to P19B UI?** | **Yes** — P19A Loop 2 PASS; this recon completes P19B-0 design gate; no schema blockers |
| **Code changed** | **No** |
| **Deploy** | **No** |

### 12.1 Why P19B → P19D → P19C

```text
P19B  Broker sees attachments + assigns slots     ← ops visibility first (demo blocker today)
P19D  Customer guided loop + Start/End Cards     ← Spark Driver value prop
P19C  OCR draft on stored attachments            ← accelerant, not prerequisite
```

P19C before P19D would extract drafts brokers cannot yet confirm in a slot-aware UI. P19D before P19B would prompt customers for slots brokers cannot see. **B then D** is the critical path.

### 12.2 P19B entry checklist

1. Read this doc + P19 spec §11 + P19A Loop 2 evidence
2. Implement Workbench attachment preview (signed URL / proxy)
3. Display `document_checklist` + `guided_workflow_state` (read from JSON; write optional in P19B)
4. Broker actions: set document type, reassign, mark manual handle
5. Unassigned queue from `wecom_media_intake` cases
6. **STOP** before P19D — Andy sign-off

---

## Related Documents

| Doc | Role |
|-----|------|
| `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` | P19 technical authority |
| `docs/p19_mobile_task_workflow_recon.md` | Spark Driver pattern recon |
| `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` | Start/Done Card + Rule 8 |
| `docs/evidence/p19a_loop2_live_wecom_image_smoke_2026_07_05.md` | P19A Loop 2 PASS evidence |
| `docs/evidence/p19a_loop1_media_intake_foundation_2026_07_05.md` | P19A Loop 1 evidence |

---

*P19B-0 recon complete — documentation only. STOP.*
