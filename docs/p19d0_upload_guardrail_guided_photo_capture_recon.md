# P19D-0 — Upload Guardrail / Guided Photo Capture Recon

**Date:** 2026-07-05  
**Revision:** 2026-07-05 v2 — **strict guardrail** (replaces v1 soft-cap / save-all-triage framing)  
**Type:** Product / UX guardrail recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19D implementation agents  
**Prerequisite:** P19A (media intake) ✅ · P19B (Workbench attachment UI) ✅ · P19B-0 guided workflow recon ✅

**Evaluated gap:** Real WeCom users may **bulk-select album photos** and flood the case. P19A currently stores every image to GCS with minimal discipline. P19D must **prevent mis-upload at the workflow layer**, not merely triage after the fact.

**This loop:** No code. No deploy. No schema migration.

---

## P19 North Star

> **P19 的目标不是增强图片上传能力，而是减少错误上传的机会；图片只是 guided workflow 中某一步的 evidence。**

| P19 is not | P19 is |
|------------|--------|
| A better photo inbox / album receiver | A **guided task** with verification at each step |
| Maximize attachments stored | **Minimize wrong uploads** before they become broker work |
| Photo-first data collection | **Structured input first**; photo only when that step requires proof |
| Bulk accept → sort later | **One step → one evidence** (with strict bulk pause) |

Every P19A/B/D design choice should be judged against this sentence.

---

## 0. Executive Summary

P19A/P19B proved the **attachment pipe works** — that was infrastructure, not the product goal. P19D-0 defines **strict upload guardrail** so customers upload **less, more correctly**, not more.

**Product goal (one line):** Reduce wrong-upload opportunities; images are **step evidence only**, not the main intake channel.

**Core shift (v1 → v2):**

| v1 (rejected) | v2 (this doc) |
|---------------|---------------|
| Soft cap; save all; flag excess | **Strong limit bulk**; default **one image per step** |
| Album dump → triage in Workbench | **>3 images → pause auto-processing**; customer must confirm |
| GCS storage as default for every event | Storage is **intentional per slot**; privacy/cost/mis-upload matter |
| Photo-first collection | **Structured input first**; photo is last resort |

**Spark Driver insight (corrected):**

Spark is **not** a bulk photo-upload product. It is a **barcode + step verification** workflow:

```text
Spark:     arrive → scan barcode → verify item → [exception path] → next item → complete
           photo only when the step explicitly requires proof (damage, placement, ID edge case)

Insurance: Start → button/text/field for each fact → ONE photo only when checklist says proof needed
           → verify slot → next step → broker review → End
```

Photos are **proof steps**, not a substitute for buttons, typed fields, scan, or (later) OCR-assisted structured capture.

**Recommendation:** **Yes — P19D-1 should implement strict upload guardrail first**, before OCR. Strict limits reduce wrong evidence, storage cost, and broker noise.

---

## 1. Upload Guardrail Principles (v2 — Strict)

### 1.1 Core principles

| # | Principle | Meaning |
|---|-----------|---------|
| **S1** | **Bulk upload prohibited by default** | Guided flow does not invite album multi-select. Copy + UX discourage batch send. |
| **S2** | **One step → one image (default)** | Active `current_slot_id` accepts **one** primary proof image per prompt cycle. |
| **S3** | **Structured input first** | Prefer: Start Card buttons → text fields → (future) scan/VIN entry → OCR draft confirm → **photo last**. |
| **S4** | **Current slot only** | Images bind only to the **prompted** slot; no opportunistic fill of future slots from one batch. |
| **S5** | **Normal slot = 1 image** | VIN, single-page notice, insurance card: **1** accepted as primary. |
| **S6** | **Special slot = 2–3 max** | Registration front/back, multi-page notice **within same slot**: max **3** primaries after explicit step widen. |
| **S7** | **>3 in one batch = bulk mistake** | Pause auto slot assignment, auto OCR, and normal Workbench surfacing until customer confirms intent. |
| **S8** | **No auto-OCR on floods** | Never queue OCR for bulk-suspect or quarantined images. |
| **S9** | **Claim lane exception** | Higher per-batch limits allowed **only** with **batch confirm** between sub-batches (e.g. 5 + confirm + 5). |
| **S10** | **Storage is intentional, not default** | Do not treat “download everything to GCS” as unconditional success. Consider privacy, retention cost, mis-upload risk. |

### 1.2 What replaces “save all, triage later”

P19A behavior (store every WeCom image to GCS) is a **foundation**, not the **product default** going forward.

| Stage | Strict P19D behavior |
|-------|----------------------|
| WeCom channel | Always send safe ack (customer must not think message was ignored) |
| **≤3 images, slot-open** | Download → GCS → assign to `current_slot_id` per limits → Workbench visible |
| **>3 images (bulk mistake)** | **Pause pipeline**: ack + confirm menu; images may be held **quarantined** (metadata + optional deferred GCS) until confirm |
| Customer confirms “yes, all for this step/case” | Promote quarantined set in **batches ≤3** with slot assignment |
| Customer says “wrong” / no confirm | Broker-only quarantine review; **no auto slot fill** |
| Retention | Configurable TTL on quarantined blobs; broker-promoted only stays long-term |

**Privacy / cost / mis-upload:** Every unnecessary GCS object is customer PII surface area and OCR cost. Strict guardrail **reduces stored proof** to what the guided step requested.

### 1.3 Preserved safety (unchanged)

| Rule | Stance |
|------|--------|
| One active business case per customer (B0) | ✅ |
| No coverage/claim/quote decisions in chat | ✅ |
| No public GCS URL | ✅ |
| Broker can review promoted evidence | ✅ |
| No OCR auto-confirm | ✅ |
| Broker manual delete | Future only; **no customer-facing auto-delete** |

### 1.4 Input priority ladder (per step)

```text
1. Button tap     (Start, upload-intent, confirm, waive)
2. Text field     (VIN, ZIP, date, phone)
3. Scan / typed ID (future: barcode, VIN keyboard)
4. OCR-assisted   (P19C+: broker confirms draft → field)
5. Photo proof    (ONLY when step says so — one image default)
```

### 1.5 Guardrail vs guided workflow vs OCR

| Layer | Role |
|-------|------|
| **Guided workflow** | Start Card → one step at a time → End Card |
| **Strict upload guardrail** | Enforce 1-image default, bulk pause, quarantine |
| **OCR** (P19C) | Only on **promoted primary** slot images |
| **Broker confirm** | Facts + document acceptance |

---

## 2. Recommended Per-Slot Limits (Strict)

**Default rule:** `max_primary = 1` unless slot is marked **special multi**.

**Special multi:** `max_primary = 3` (registration front/back, multi-page notice in **one** slot step).

### 2.1 Add Vehicle (`add_car`)

| Slot ID | Type | Max primary | Step mode |
|---------|------|-------------|-----------|
| `slot_vin_photo` | normal | **1** | Text VIN preferred; photo if can't type |
| `slot_registration` | special | **2–3** | After 1st image, prompt “need back page?” before 2nd |
| `slot_insurance_card` | normal | **1** | Optional slot |
| `slot_driver_license` | normal | **1** | Optional |
| `field_*` (ZIP, date, phone) | text | **0 images** | No photo unless customer insists → quarantine |

**Lane batch ceiling:** **3 images per prompt cycle**. More → bulk mistake flow (§4).

### 2.2 Premium Review (`policy_review`)

| Slot ID | Type | Max primary | Notes |
|---------|------|-------------|-------|
| `slot_renewal_notice` | special | **3** | One step widened: “第 1–3 页续保通知” |
| `slot_dec_page` | special | **2–3** | Alternative doc path |
| `slot_current_premium` | normal | **1** | Prefer text for premium amount |
| `field_renewal_date` | text | **0** | |

**Rule:** Renewal OR dec page — not both unless broker widens checklist.

### 2.3 Claim Lite (`claim_lite`) — exception lane

| Slot ID | Type | Max per sub-batch | Notes |
|---------|------|-------------------|-------|
| `slot_accident_photos` | claim-multi | **5** per sub-batch | **Must confirm** before next 5 |
| `slot_police_report` | special | **3** | |
| `slot_other_party_info` | normal | **1–2** | |
| `field_*` | text | **0** | Safety fields first |

**Claim lane total guidance:** up to **10–15** accident images **only** across **2–3 confirmed sub-batches**, not one album dump.

### 2.4 Coverage Risk (`coverage_risk`)

| Slot ID | Type | Max primary |
|---------|------|-------------|
| `slot_dmv_notice` | special | **3** |
| `slot_cancellation_notice` | special | **3** |
| `field_policy_number` | text | **0** |

### 2.5 Unassigned / no active case

| Context | Behavior |
|---------|----------|
| 1 image, no case | Holding case (P19A path) — **1 image only** auto-processed |
| 2–3 images | Lane disambiguation menu; no slot assign until case + slot |
| **>3 images** | Quarantine + “请先确认这些照片属于哪个事项” — **no mass GCS promote** |

### 2.6 Quick reference

| Category | Max images per step | Bulk mistake threshold |
|----------|---------------------|-------------------------|
| Normal slot | **1** | >3 in 120s window |
| Special slot | **2–3** (explicit widen) | >3 without widen flag |
| Claim accident sub-batch | **5** (+ confirm) | >5 without confirm |
| Text field step | **0** (photo → quarantine) | any photo triggers re-prompt |

---

## 3. Step-Based Capture Design (Strict)

### 3.1 Default step = one proof

Each guided message:

```text
第 2 步 · 行驶证
请现在拍 **1 张** 行驶证正面照片。
如果暂时不方便拍照，可以打字发 VIN / 车牌 / 提车日期。
[我上传行驶证照片]  [我打字补充]  [联系陈总]
```

**No copy** that says “可以一次发多张” except **Claim accident sub-batch** after explicit widen.

### 3.2 Widening to 2–3 (special slots only)

After first image received:

```text
收到第 1 张。如果行驶证有反面，请再发 **1 张** 反面（最多再 2 张）。
```

System sets `slot_max_primary = 3` for this step only.

### 3.3 Album vs camera

| Behavior | Strict stance |
|----------|---------------|
| Encourage live capture | ✅ Copy only |
| Allow album | ✅ WeCom limitation — but **discourage** multi-select in copy |
| Auto-process album batch | ❌ **>3 → pause** |

### 3.4 Spark-aligned step transition

```text
Prompt step (button/text/photo)
  → customer action
  → verify (slot filled? bulk mistake? wrong type?)
  → if OK: advance current_slot_id
  → if bulk mistake: PAUSE (§4)
  → if wrong type: keep 1 promoted; ask retake (additive max 1 replacement primary)
```

---

## 4. Bulk Upload Handling Strategy (Strict)

### 4.1 Definitions

| Term | Definition |
|------|------------|
| **Prompt cycle** | From step prompt until next step prompt or 120s idle |
| **Bulk batch** | >3 `image`/`file` messages same customer within 120s **OR** >1 image when `current_slot` max_primary=1 and not widened |
| **Bulk mistake** | Batch exceeds slot limit or global **>3** threshold |
| **Quarantine** | Received at channel; **not** promoted to case primary list / OCR / normal Workbench |

### 4.2 Decision table

| Count | Active slot? | Auto-processing | Storage | Customer |
|-------|--------------|-----------------|---------|----------|
| **1** | Yes, slot open | ✅ Assign primary; ack | GCS promote | 收到，陈总会人工确认。 |
| **2–3** | Yes, special slot widened | ✅ Up to slot max | GCS promote | 收到 {N} 张。 |
| **2–3** | Yes, normal slot (max 1) | ⚠️ **1st promote only**; rest quarantine | 1 GCS + quarantine meta | 当前步骤只需 1 张。已收到第一张；其余请先确认。[确认] [发错了] |
| **>3** | Any | ❌ **PAUSE** — no assign, no OCR | Quarantine (defer or isolated prefix) | 您一次发了较多图片。请先确认是否都属于当前这一步。[是] [不是] [联系陈总] |
| **>5** | Claim, no prior sub-batch confirm | ❌ PAUSE | Quarantine | 理赔照片请分批发送：每次最多 5 张，发完请点确认。 |
| **Claim sub-batch 2** | After customer confirms batch 1 | ✅ Next ≤5 | GCS promote batch 2 | 收到第二批。还需要补充吗？ |

### 4.3 What “pause auto-processing” means

When bulk mistake:

1. **Do not** assign attachments to `current_slot_id` beyond limit  
2. **Do not** advance guided workflow step  
3. **Do not** enqueue OCR  
4. **Do not** show quarantined items in default Workbench attachment list (broker **Quarantine** subsection only)  
5. **Do** send safe WeCom ack + confirm buttons  
6. **Do** log `bulk_upload_pending_confirm = true` on case  

### 4.4 After customer confirms

| Response | Action |
|----------|--------|
| **是 — same step** | Promote up to slot max in order; re-quarantine remainder; clear pause if within limit |
| **是 — claim next batch** | Promote next ≤5 to accident slot; ask confirm again |
| **不是 / 发错了** | Leave quarantined; broker reviews; prompt customer to resend **1** image for current step |
| No response | Broker sees **Bulk mistake (N quarantined)** badge |

### 4.5 Anti-patterns (strict)

| Do not | Why |
|--------|-----|
| Auto-save 20 album images to case as primary | Mis-upload + privacy + cost |
| Auto-OCR all quarantined | Cost + false fields |
| Tell customer “upload rejected” without ack | Channel trust |
| Silently drop WeCom messages | Compliance / customer trust — quarantine ≠ ignore |
| Use bulk upload as default happy path | Violates Spark-style discipline |

### 4.6 P19A → P19D migration note

P19A **always** GCS-persisted. P19D-1 introduces **promote vs quarantine** split. Existing attachments unchanged; new strict rules apply to **new** intake after deploy.

---

## 5. Duplicate / Wrong / Unclear (Strict)

| Situation | Promoted storage | Behavior |
|-----------|------------------|----------|
| Duplicate `msg_id` | N/A | Dedup (P19A) |
| Re-shoot same slot | Max 1 new primary; prior → `superseded` (broker visible) | Ask one clearer photo |
| Wrong doc for step | Do not promote to slot | Quarantine + “当前步骤需要 {expected}” |
| Blurry | 1 promoted if only copy; flag `needs_clearer_photo` | Ask one retake |
| Text step receives photo | Quarantine | “这一步请先打字回复；如必须拍照请点上传按钮” |

---

## 6. Workbench Display (Strict)

```text
├─ Document Checklist ─────────────────────────────────
│ [●] VIN photo      1/1 received
│ [○] Registration   prompted — expecting 1 image
├─ Promoted attachments (N) ─────────────────────────
│   primary slot images only
├─ ⚠ Quarantine / bulk mistake (M) ───────── broker only
│   not OCR · not counted toward checklist complete
├─ Customer / Warnings ──────────────────────────────
```

Badges: `Primary` · `Quarantined` · `Bulk mistake` · `Needs confirm` · `Superseded`

---

## 7. Customer Copy (Strict)

**One step one image:**
```
为了避免资料放错，请只上传当前这一步需要的 **1 张** 照片。
能打字填写的（VIN、邮编、日期），请优先打字。
```

**Bulk mistake (>3):**
```
您一次发了较多图片。为避免传错资料，请先确认这些都属于当前「{step_label}」吗？
[是的] [不是，我发错了] [联系陈总]
```

**Normal slot overflow (2+ when only 1 wanted):**
```
当前步骤只需要 1 张 {slot_label}。已收到第一张，请先确认是否还要继续发。
```

**Claim sub-batch:**
```
收到 5 张事故照片。如果还有更多，请确认后继续发下一批（每次最多 5 张）。
[继续上传下一批] [就这些] [联系陈总]
```

**Pause — do not continue:**
```
请先不要继续上传照片，陈总会查看已收到的资料。如需补充我们会微信联系您。
```

---

## 8. Safety Red Lines

| Red line | Strict stance |
|----------|---------------|
| Public GCS URL | Never |
| OCR auto-confirm | Never |
| Auto-OCR bulk / quarantine | Never |
| Coverage/claim/quote in chat | Never |
| Encourage album bulk | Never in copy |
| Unconditional store-all as product policy | **Removed** — promote intentionally |
| Customer-facing auto-delete | Never |
| Broker delete / retention policy | Future; document separately |

---

## 9. Recommendation

### 9.1 Should P19D-1 be strict upload guardrail?

**Yes.** Implement **strict** guardrail before OCR and before permissive triage UI.

```text
P19D-1 Strict Upload Guardrail MVP
  → one-step-one-image default
  → >3 bulk mistake pause + quarantine
  → promote vs quarantine split
  → claim sub-batch confirm
  → customer copy + case flags
  → Workbench quarantine badge (read-only)

P19D-2  Slot checklist UI + broker promote/dismiss quarantine
P19D-3  Guided buttons + Start Card integration
P19C    OCR on promoted primary only
```

### 9.2 P19D-1 MVP scope (strict)

| # | Deliverable |
|---|-------------|
| 1 | `upload_guardrail.py` — slot limits, bulk detector, promote/quarantine decision |
| 2 | `current_slot_id` + `slot_max_primary` (1 default, 3 widened) |
| 3 | Attachment `intake_status`: `promoted` \| `quarantined` \| `superseded` |
| 4 | Case flags: `bulk_upload_pending_confirm`, `quarantine_count` |
| 5 | Reply templates — strict copy (§7) |
| 6 | Claim sub-batch confirm (5 + confirm + 5) |
| 7 | Workbench: hide quarantined from primary list; show count + broker expander |
| 8 | Tests: 1→promote; 4→pause+quarantine; claim 5+5 with confirm |

**Not in P19D-1:** OCR, visual dedup, auto-delete, schema migration.

---

## 10. Recon Verdict (v2)

| Question | Answer |
|----------|--------|
| **Problem** | Album bulk upload bypasses guided discipline |
| **Spark lesson** | **Barcode/step verify**; photo only for required proof |
| **Core guardrail** | **Prohibit bulk by default**; one image per step; structured input first |
| **Per-slot limits** | Normal **1**; special **2–3**; claim **5+batch confirm** |
| **>3 images** | Bulk mistake — pause auto-processing; confirm required |
| **GCS** | **Promote intentionally** — not save-all default |
| **Before OCR?** | **Yes** |
| **P19D-1** | **Strict upload guardrail MVP** |
| **Code / deploy** | **No** |

### 10.1 Strongest insight (v2)

> **P19 不是增强上传，是减少误传；图片只是 guided workflow 某一步的 evidence。**  
> Spark wins on **verification steps** (barcode, confirm, next item) — not photo volume. Storage and OCR apply only to **promoted step evidence**, not every album mis-tap.

---

## Related Documents

| Doc | Role |
|-----|------|
| `docs/p19_guided_workflow_start_end_card_recon.md` | Slots, states (note: §5 multi-image rules superseded by this doc for limits) |
| `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` | P19 master spec |
| `docs/evidence/p19b_deploy_live_ui_smoke_2026_07_05.md` | P19B live baseline |

---

*v2 strict guardrail recon — documentation only. STOP.*
