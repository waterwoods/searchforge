# P19 — WeCom Photo Intake / Mobile Case Builder

**Date:** 2026-07-05  
**Type:** Product + technical specification — **documentation only**  
**Audience:** Andy, Chen Kui demo team, future Cursor/Claude/Codex implementation agents  
**Prerequisite:** Loop 0–3C/3D stable on `sprint/p16-trust-layer` — text + buttons + Workbench lanes proven live.

**Authority:** Does not supersede ADR-001–005, `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`, or `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md`. Defines the **next product stage** after text-only WeCom intake.

**Stable baseline (pre-P19):**

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Backend | Cloud Run `fiqa-api-00148-mk2` |
| Frontend | https://ui-smoky-beta.vercel.app |
| DB | GCP Cloud SQL `caseiq` @ `10.73.0.3` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` |
| Neon | Legacy only — not QA truth |
| Live lanes | Add Vehicle (Start Card + Draft), Premium Review, Claim Lite, Coverage Risk |
| Known gap | WeCom image/media not implemented (`sync_msg` skips non-text) |

---

## 1. Executive Summary

Text-only WeCom intake proved the core thesis: customers can message naturally, tap buttons, and brokers can act from Workbench. That is necessary but not sufficient for a real **Insurance Case Builder IQ**.

Insurance workflows are **document- and photo-heavy**. Customers already carry the evidence on their phones: insurance cards, renewal notices, DMV letters, accident photos, registration slips, driver licenses, VIN stickers. Asking them to re-type everything in chat is slow, error-prone, and unlike how they already behave.

The target experience is simple:

> **Send photo → tap button → fill only missing info → broker confirms.**

AI must **not** replace the broker. AI organizes messy customer materials, drafts facts, and surfaces gaps. **Broker confirms** before anything becomes official case truth.

**Product phrase:**

> **Mobile Case Builder = Text + Buttons + Photos + Checklist + Broker Confirmation**

End-to-end vision:

```text
WeCom customer sends insurance card / renewal notice / DMV notice / accident photo
→ system receives media
→ system stores attachment
→ binds image/document to the correct active case
→ Workbench shows attachment and document type
→ optional OCR draft extracts useful fields
→ broker confirms/corrects
→ case becomes more complete
```

---

## 2. Product Motivation

### Walmart Spark Driver analogy

Spark Driver works because the workflow is **mobile-first**:

- scan barcode or confirm item
- photo proof of delivery
- tap status buttons
- simple checklist — no long forms

Insurance customers behave the same way on WeCom:

| Customer has on phone | Lane it supports |
|----------------------|------------------|
| Insurance card | Add Vehicle, Coverage Risk |
| Renewal notice | Premium Review |
| DMV notice | Coverage Risk |
| Cancellation notice | Coverage Risk |
| Accident photos | Claim Lite |
| Registration / temp tag | Add Vehicle |
| Driver license | Add Vehicle |
| VIN photo / sticker | Add Vehicle |

If customers can send these through WeCom, the system builds the case **faster** than any generic chatbot that only replies with text.

### What this product is — and is not

| Is | Is not |
|----|--------|
| Broker-controlled case builder | Generic chatbot |
| Mobile task workflow (photo + tap + checklist) | Autonomous insurance processor |
| AI that organizes materials and drafts facts | AI that decides coverage, liability, or quotes |
| Channel = WeCom; product = Case Builder IQ | "We built a WeChat bot" |

---

## 3. P19 Scope

### In scope — P19 MVP

1. **WeCom image/message media intake** — detect `image`, `file`, and related media msgtypes in callback/sync path.
2. **Download media from WeCom** using `media_id` (and equivalent file identifiers per WeCom API).
3. **Store media safely** — GCS preferred; never raw binary in Postgres.
4. **Create attachment record** — metadata JSON on case or unassigned intake event.
5. **Bind attachment to case:**
   - current active case in flow, if one exists
   - otherwise lightweight unclassified intake event or customer lane choice
6. **Workbench shows:**
   - thumbnail / secure link
   - source channel (WeCom)
   - received time
   - possible document type
   - case binding + binding confidence
   - broker action affordances
7. **Optional OCR draft** (later sub-loop):
   - not required for first implementation (P19A)
   - rule / vision / OCR-based later
   - broker must confirm extracted facts

### Out of scope — first P19 MVP

| Item | Reason |
|------|--------|
| Automatic policy change | Broker gate; ADR-003 |
| Automatic quote | Premium lane is review-only |
| Automatic claim filing | Claim Lite is intake + manual handle |
| Coverage status decision | Coverage Risk is high-risk manual review |
| Automatic legal/coverage advice | Safety / compliance |
| Full document AI confidence automation | Broker confirms all facts |
| Batch OCR pipeline | Phased; P19A is attachment-only |
| Complex multi-document reconciliation | Defer to post-MVP |
| Customer identity KYC automation | WeCom `external_userid` + phone sufficient for demo |
| Replacing broker review | Constitution Rule 7 / B0 contract |

---

## 4. Target User Experience

### Flow A — Add Vehicle: insurance card / VIN photo

| Step | Actor | Action |
|------|-------|--------|
| 1 | Customer | Says: "明天提新车，帮我加保险" |
| 2 | System | Sends Start Card |
| 3 | Customer | Taps Start |
| 4 | System | Asks for VIN / dealer / delivery date / driver |
| 5 | Customer | Sends photo: temp registration, VIN sticker, insurance card |
| 6 | System | Replies: "收到图片，我会先放到这个加车 case 里，陈总会人工确认。" |
| 7 | Broker | Workbench shows attachment under Add Vehicle case |

### Flow B — Premium Review: renewal notice

| Step | Actor | Action |
|------|-------|--------|
| 1 | Customer | Says: "保险又涨了" |
| 2 | System | Creates `policy_review` case |
| 3 | System | Asks for renewal notice / current policy |
| 4 | Customer | Sends photo or PDF |
| 5 | System | Stores document |
| 6 | System (optional OCR) | Draft: carrier, renewal premium, policy period, insured vehicles |
| 7 | Broker | Workbench: renewal notice attached, OCR draft fields, missing fields, next step |

### Flow C — Claim Lite: accident photos

| Step | Actor | Action |
|------|-------|--------|
| 1 | Customer | Says: "我撞车了" |
| 2 | System | Creates `claim_lite` case |
| 3 | System | Asks customer to confirm safety; send accident photos if safe |
| 4 | Customer | Sends photos |
| 5 | System | Stores photos |
| 6 | Broker | Workbench: accident photos, time received, manual handle, missing facts |
| 7 | System | **Never** decides liability or whether to file claim |

### Flow D — Coverage Risk: DMV / cancellation notice

| Step | Actor | Action |
|------|-------|--------|
| 1 | Customer | Says: "DMV 说我没保险" |
| 2 | System | Creates `coverage_risk` case |
| 3 | Customer | Sends DMV notice or cancellation notice |
| 4 | System | Stores attachment |
| 5 | System (optional OCR) | Draft: notice date, policy number, carrier, cancellation/lapse date |
| 6 | Broker | Workbench: high-risk manual review |
| 7 | System | **Never** tells customer whether they can drive |

---

## 5. Case Binding Rules

Incoming WeCom image/document binding priority:

| Priority | Condition | Action | `binding_confidence` |
|----------|-----------|--------|----------------------|
| 1 | Customer has **active case in current flow** | Bind to that case | `high` |
| 2 | Image follows a **system prompt requesting that document** | Bind to prompted case | `high` |
| 3 | **Latest open case** exists and is recent (configurable window, e.g. 48h) | Bind to most recent open case | `medium` |
| 4 | **Multiple open cases** — ambiguous | Do not guess aggressively; create unclassified intake or ask customer | `low` / unassigned |
| 5 | **No active case** | Create `unclassified_document_intake` or `document_intake` event | `unknown` |

### Ambiguous binding — customer prompt

When multiple open cases or no clear match:

> 这是加车资料 / 保费资料 / 理赔照片 / DMV通知？

### Invariants

- **Raw media event must never be lost** — even if download fails, record event + error state.
- **Uncertain binding must be visible** in Workbench (`binding_confidence`, unassigned queue).
- **Broker can reassign** attachment to any case.

### Alignment with B0 / Constitution

- One business flow at a time (Rule 8) — binding should prefer the **active lane case**, not a second open case.
- Add Vehicle Draft before broker confirm remains valid — photos attach to Draft, not Active.

---

## 6. Document Type Classification

### First-pass document types

```
insurance_card
renewal_notice
dmv_notice
cancellation_notice
registration
vin_photo
driver_license
accident_photo
vehicle_photo
claim_document
unknown_document
```

### MVP classification signals (no OCR required)

| Signal | Example |
|--------|---------|
| Customer text context | "这是续保通知" → `renewal_notice` |
| Current lane | Add Vehicle open → `insurance_card` / `vin_photo` / `registration` |
| Recent system prompt | "请发续保通知照片" → `renewal_notice` |
| Filename / media type | `.pdf` + Premium lane → `renewal_notice` (low confidence) |
| Manual broker selection | Workbench override |

OCR-based classification is a **later** enhancement.

### Document type confidence

`high` · `medium` · `low` · `unknown`

**Do not overtrust classification.** Show confidence in Workbench; broker can correct.

---

## 7. Data Model Direction

**No schema migration in P19A** unless explicitly approved. Prefer existing `service_records` + JSON extra fields.

### Existing hooks (codebase today)

- `case_store.add_attachment_to_case()` — local filesystem + `case_attachments[]` on case JSON
- `case_store` normalizes `case_attachments` list on load
- Web upload path uses `data/unified_intake_attachments/` (dev); WeCom path should use GCS in production

### Preferred MVP JSON shape

Store under case `extra` or top-level `case_attachments` (extend existing lite schema):

```json
{
  "attachments": [
    {
      "attachment_id": "att_...",
      "source": "wecom",
      "external_userid": "...",
      "msg_id": "...",
      "media_id": "...",
      "storage_uri": "gs://...",
      "mime_type": "image/jpeg",
      "received_at": "2026-07-05T...",
      "bound_case_id": "case_...",
      "binding_confidence": "high",
      "document_type": "renewal_notice",
      "document_type_confidence": "medium",
      "ocr_status": "not_started",
      "ocr_draft": null,
      "broker_confirmed": false
    }
  ]
}
```

**Field mapping note:** Align with existing `case_attachments` keys (`attachment_id`, `filename`, `type`, `size_bytes`, `created_at`) where possible; add WeCom-specific fields as extensions to avoid breaking web upload path.

### Unassigned intake

When no case binding:

- Option A: standalone `document_intake` row or event in `record_messages` with attachment metadata
- Option B: synthetic "unassigned" pseudo-case visible only in Workbench unassigned queue
- P19A should pick **one** approach in implementation loop; spec allows either if broker can attach later

### Future normalized tables (post-MVP)

If JSON becomes too limited:

| Table | Purpose |
|-------|---------|
| `case_attachments` | Normalized attachment metadata |
| `attachment_events` | Raw ingress audit trail |
| `ocr_drafts` | Versioned extraction drafts |
| `broker_field_confirmations` | Confirmed facts audit |

---

## 8. Storage Strategy

### Preferred: Google Cloud Storage

| Requirement | Detail |
|-------------|--------|
| Bucket | Dedicated WeCom media bucket (name TBD — see §15) |
| Object path | `gs://<bucket>/wecom/<external_userid>/<yyyy>/<mm>/<msg_id>.<ext>` |
| Postgres | Metadata + `storage_uri` only — **never** store binary image in DB |
| Workbench display | Signed URL or backend proxy — no public objects |
| Retention / deletion | Document policy later; preserve raw file until broker confirms or case archived |

### WeCom media expiry

WeCom `media_id` **expires** (typically within days). Download must happen **soon after message receipt** — ideally in same worker pass as text processing.

### Dev / local

- May use local path under `UNIFIED_INTAKE_ATTACHMENTS_DIR` for local smoke
- Production path must be GCS

### Security

- No public bucket ACLs
- Workbench auth required for preview
- Do not expose full `external_userid` in UI (mask suffix only — Loop 3D pattern)

---

## 9. WeCom Media Pipeline

### End-to-end pipeline

```text
WeCom callback / sync_msg
  → detects image / file / media message (msgtype != text only)
  → extracts media_id (and file metadata per WeCom API)
  → dedup by msg_id (existing message_processed pattern)
  → downloads media from WeCom API
  → validates file type and size
  → uploads to GCS (or safe dev storage)
  → creates attachment metadata
  → applies case binding rules (§5)
  → persists to case JSON or unassigned intake
  → sends safe customer acknowledgement (§12)
  → Workbench displays attachment
  → optional OCR job later (async, P19C)
```

### Implementation notes

| Note | Detail |
|------|--------|
| Current path | `sync_msg` / slice mainly handles **text + buttons**; non-text skipped today |
| P19 adds | Media handling branch — must not break Q0.11.1 text path |
| Dedup | Use `msg_id` + existing `message_processed` / inbox dedup |
| Download failure | Record raw event; show error in Workbench; do not lose customer message |
| Reply | Safe ack via existing outbox path; no OCR claims in customer reply |

### Suggested code touchpoints (for implementers — do not build in spec loop)

| Component | Role |
|-----------|------|
| `services/fiqa_api/wecom/sync_msg.py` | Detect media msgtypes |
| `services/fiqa_api/wecom/slice.py` | Orchestrate media branch parallel to text |
| `services/fiqa_api/wecom/active_case_bridge.py` | Bind to active Draft/case |
| `services/fiqa_api/inbox_triage/case_store.py` | Extend `add_attachment_to_case` or WeCom variant |
| `ui/.../BrokerWorkbenchTab.tsx` | Attachment section (P19B) |

---

## 10. OCR / Extraction Strategy

### P19A — No OCR, attachment only

| Goal | Detail |
|------|--------|
| Receive | WeCom image/file detected |
| Store | GCS + metadata |
| Bind | Case or unassigned |
| Show | Workbench thumbnail/link |
| OCR | **None** |

### P19B — Workbench attachment UI

Manual document type, reassign, preview — still no OCR.

### P19C — OCR draft (optional sub-loop)

OCR extracts **draft** fields by document type. Fields are never official until broker confirms.

| Document type | Possible extracted fields |
|---------------|---------------------------|
| **Insurance card** | carrier, policy number, named insured, vehicle year/make/model, VIN, effective/expiration dates |
| **Renewal notice** | carrier, policy number, renewal premium, term dates, vehicles, coverage summary |
| **DMV notice** | notice date, vehicle, VIN/plate, issue type, required action date |
| **Cancellation notice** | carrier, policy number, cancellation date, reason, reinstatement instructions |
| **Accident photo** | classify as `accident_photo` only — **no liability judgment** |

### P19D — Broker confirmation

| State | Workbench behavior |
|-------|-------------------|
| OCR Draft | Show extracted fields with confidence |
| Broker actions | Confirm / Correct / Ignore per field |
| Confirmed | Update case `known_facts` / `collected_fields` |
| Unconfirmed | Remain in `ocr_draft` only |

Existing web-path OCR (`policy_review/handler.py`, `v6_attachment_sidecar`) may inform engine choice but **must not** be auto-enabled on WeCom path without explicit P19C loop approval.

---

## 11. Workbench UX

### Per-case attachment section

```
Attachments
├── thumbnail / secure preview link
├── document type (+ confidence badge)
├── received time
├── source: WeCom
├── customer label (masked)
├── OCR status (not_started | draft | confirmed | failed)
├── extracted draft fields (if any)
└── broker actions:
    ├── confirm field
    ├── correct field
    ├── mark document type
    ├── reassign attachment
    └── request clearer photo
```

### Unassigned attachment queue

```
Unassigned WeCom Attachment
├── customer (masked label)
├── received time
├── image preview
├── suggested case / lane (if any)
├── [Attach to existing case]
├── [Create new case]
└── [Ask customer what this is]
```

### Document checklist (per lane)

| State | Meaning |
|-------|---------|
| needed | System or broker marked document required |
| received | Attachment stored, not confirmed |
| confirmed | Broker confirmed document + key fields |
| missing | Still required for case readiness |

Example Add Vehicle checklist: VIN photo, registration, insurance card (optional), driver license (optional).

---

## 12. Customer Reply Templates

Safe, conservative copy — no coverage/legal/quote claims.

### Generic image received (active case)

> 收到图片，我先把它放到您的服务 case 里，陈总会人工查看确认。

### Image received, no active case

> 收到图片。为了放到正确的服务事项里，请问这是加车资料、保单/续保资料、理赔照片，还是 DMV/停保通知？

### Insurance card / add vehicle

> 收到保险卡/车辆资料图片，我会先放到加车 case 里。陈总会人工确认 VIN、日期和车辆信息。

### Renewal notice

> 收到续保/保费资料，我会先整理到保单检视 case 里。陈总会人工查看，不会线上直接报价。

### Claim photo

> 收到事故照片。请先确认人是否安全，我会把照片放到理赔服务 case 里，陈总会人工联系您。

### DMV / cancellation notice

> 收到通知图片。这个属于高风险保单状态问题，需要陈总人工核实。线上不能判断您是否仍有保障，也不能建议您是否可以开车。

### Download / storage failure (internal tone for implementers)

Customer should still get acknowledgement that message was received; broker sees error state. Do not claim successful attachment if storage failed.

---

## 13. Safety / Compliance Rules

**Strict — non-negotiable for all P19 loops:**

| Rule | Detail |
|------|--------|
| Never declare coverage active/inactive from OCR alone | Coverage Risk = manual only |
| Never tell customer they can or cannot drive | DMV/cancellation lane |
| Never file claim automatically | Claim Lite = intake + broker |
| Never change policy automatically | ADR-003 |
| Never quote premium automatically | Premium Review = review only |
| Never infer liability from accident photos | Store + classify only |
| Never expose full `external_userid` in UI | Mask suffix |
| Do not display sensitive images publicly | Signed URL / auth proxy |
| Attachments must be private | No public GCS |
| Broker confirmation required | Before updating official case facts |
| OCR confidence must be visible | Draft vs confirmed |
| Raw uploaded file must be preserved | Audit + broker review |

---

## 14. Implementation Loops Proposal

Break P19 into small, safe loops. **STOP after each loop for QA + Andy approval before next.**

### P19A — Media intake foundation

| Item | Detail |
|------|--------|
| **Goal** | WeCom image/file detection → download → GCS → metadata → case bind or unassigned → Workbench placeholder → safe ack |
| **No OCR** | Attachment only |
| **Acceptance** | WeCom image appears in Workbench on case; text lanes regress-free; dedup works |

### P19B — Workbench attachment UI

| Item | Detail |
|------|--------|
| **Goal** | Case detail attachment section: preview, document type manual select, reassign, mark unknown |
| **Acceptance** | Broker can view, classify, reassign without API hacks |

### P19C — Optional OCR draft (insurance card / renewal notice)

| Item | Detail |
|------|--------|
| **Goal** | OCR on saved attachment → draft fields → broker confirm/correct |
| **Acceptance** | No automatic official case update; OCR status visible |

### P19D — Customer checklist and guided upload

| Item | Detail |
|------|--------|
| **Goal** | After lane start, system asks for specific documents; customer taps upload intent buttons |
| **Buttons** | "我上传保险卡" · "我上传续保通知" · "我上传DMV通知" · "我上传事故照片" |
| **Acceptance** | Next image binds with `binding_confidence=high` |

### P19E — Demo rehearsal integration

| Item | Detail |
|------|--------|
| **Goal** | Chen Kui demo: text + buttons + photo upload + Workbench end-to-end |
| **Acceptance** | `check_chen_kui_demo_environment.sh --cloud-api` PASS with photo scenario documented |

---

## 15. Technical Questions / Open Decisions

| # | Question | Options / notes |
|---|----------|-----------------|
| 1 | GCS bucket name and retention policy | New bucket vs existing project bucket; lifecycle rules TBD |
| 2 | Attachment metadata storage | JSON on `case_attachments` first vs new table |
| 3 | Workbench image preview auth | Signed URL TTL vs backend proxy endpoint |
| 4 | WeCom media download IP allowlist | Static egress IP already used for callback — verify media API same |
| 5 | Cloud Run egress/NAT for WeCom media API | Confirm current NAT sufficient |
| 6 | OCR engine | Google Vision · Document AI · Gemini vision · Tesseract · **defer to P19C** |
| 7 | OCR sync vs async | Async recommended; never block customer ack |
| 8 | Large images / PDFs | Max size aligned with `MAX_ATTACHMENT_SIZE_BYTES`; resize policy TBD |
| 9 | Multiple open cases | Binding window duration; customer disambiguation UX |
| 10 | Demo attachment cleanup | Seed script / archive flag for smoke images |
| 11 | Unassigned intake storage | Pseudo-case vs `record_messages` event — pick in P19A |
| 12 | Extend `add_attachment_to_case` vs WeCom-specific path | Reuse vs parallel to avoid breaking web upload |

---

## 16. P19 Acceptance Criteria

### P19A MVP — pass only if all true

| # | Criterion |
|---|-----------|
| 1 | WeCom image message is detected |
| 2 | Media is downloaded **or** failure is recorded with visible error |
| 3 | Attachment metadata is saved |
| 4 | Attachment bound to active case **or** unassigned intake |
| 5 | Workbench shows attachment |
| 6 | Customer receives safe acknowledgement (§12) |
| 7 | Existing text lanes do not regress: Generic, Add Vehicle, Premium, Claim, Coverage Risk |
| 8 | No OCR required for P19A |
| 9 | No schema migration unless explicitly approved |
| 10 | No public file exposure |
| 11 | Dedup prevents duplicate attachments (`msg_id`) |
| 12 | **Cursor STOPs before P19B** — QA gate + Andy sign-off |

### Regression gate (run before and after P19A)

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# WeCom tests: pytest tests/test_wecom_*.py (82+ passed at Loop 3B)
```

---

## 17. Recommended Next Action

**Do not implement in this spec loop.**

Next implementation loop:

> **P19A Loop 1 — WeCom Media Intake Foundation**

Scope: media detection, download, GCS storage, attachment metadata, case binding, Workbench placeholder, safe customer ack, zero OCR, zero schema migration.

Entry checklist before coding:

1. Read this document + `TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`
2. Confirm GCS bucket + IAM for Cloud Run service account
3. Verify WeCom media API access from Cloud Run egress IP
4. Branch from `sprint/p16-trust-layer` at latest stable tag
5. Implement P19A only; STOP at acceptance criteria §16

---

## 18. Related Documents

| Doc | Relevance |
|-----|-----------|
| `docs/p18_chen_kui_wecom_ai_case_intake_demo.md` | Demo narrative; text-first proof |
| `docs/p18_8_implementation_asset_inventory_risk_review.md` | Confirms media gap in `sync_msg` |
| `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` | One flow at a time; broker confirm gate |
| `docs/runbooks/CHEN_KUI_DEMO_ENVIRONMENT.md` | Live env + QA commands |
| `docs/evidence/loop_3b_stable_checkpoint_2026_07_05.md` | Pre-P19 stable checkpoint |

---

*P19 spec loop complete — documentation only. No code, deploy, or schema changes in this loop.*
