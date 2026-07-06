# P19D — Step-by-Step Evidence Capture Doctrine (SSOT)

**Date:** 2026-07-06  
**Status:** **Canonical product doctrine** — supersedes any framing that treats P19 as “better photo upload” or “bulk intake + triage”  
**Audience:** Andy, Chen Kui demo team, all P19D+ implementation agents  
**Prerequisite:** P19A (media pipe) ✅ · P19B (Workbench preview) ✅ · P19D-1 (strict chat guardrail) ✅  

**This document:** Product doctrine + interaction rules + guardrail hierarchy + P19D-2 build guidance.  
**Not in scope:** Code, deploy, schema migration.

**Related recon (detail, not SSOT):**

| Doc | Role |
|-----|------|
| `docs/p19d0_upload_guardrail_guided_photo_capture_recon.md` | Strict guardrail limits, quarantine tables |
| `docs/p19_guided_workflow_start_end_card_recon.md` | Start/End Cards, slot matrix, copy |
| `docs/p19d15_h5_guided_task_ux_simulation_recon.md` | H5 UX simulation, channel split |
| `docs/p19d05_wechat_native_guided_workflow_channel_recon.md` | WeChat-native vs H5 channel recon |

---

## One-line doctrine (SSOT)

> **P19 的目标不是增强图片上传能力，而是像 DoorDash / KYC / Spark Driver 一样，在当前 case 的当前 slot 上，一次只采集、预览确认、提交一张证据，再进入下一步；图片只是 guided workflow 中某一步的 evidence，不是让用户一次多传再由系统猜。**

---

## A. Product doctrine

| # | Principle | Meaning |
|---|-----------|---------|
| **A1** | **Not photo-upload enhancement** | P19 does **not** optimize album intake, attachment count, or “save all then sort.” |
| **A2** | **Reduce wrong-upload opportunity** | Success = fewer mistaken uploads **before** they become broker work, GCS PII, or OCR cost. |
| **A3** | **Image = step evidence** | A photo is proof for **one** guided step in **one** slot — not a substitute for the whole checklist. |
| **A4** | **No bulk upload by default** | Bulk album send is **not** a normal customer path. |
| **A5** | **One step → one image (default)** | Normal slots accept **one** primary image per prompt cycle. |
| **A6** | **Current slot only** | Only the **active** `current_slot_id` accepts primary evidence; no opportunistic fill of future slots from one batch. |
| **A7** | **Preview → confirm → submit** | Customer sees preview and confirms **before** the image counts as submitted evidence for that step (H5 primary; chat cannot fully enforce). |
| **A8** | **Submit → next step** | After successful slot submit, workflow advances to the **next** single action — never “send everything now.” |
| **A9** | **OCR on promoted slot evidence only** | OCR (future P19C+) runs only on **promoted**, **current-slot** attachments. |
| **A10** | **Quarantined / bulk → no OCR** | Quarantined, bulk-paused, or wrong-slot images are **never** auto-OCR or auto-slot-filled. |

### Reference analogy (DoorDash / KYC / driver license)

```text
KYC / license verify:  Step 1 front of ID → preview → confirm → Step 2 back of ID → preview → confirm → done
                      NOT: upload 6 photos and let the system figure out which is front

Insurance Add Vehicle: Step 1 VIN photo → preview → confirm → Step 2 registration → … → broker review
                      NOT: 「请上传车辆资料」+ album dump
```

---

## B. Add Vehicle canonical flow

| Step | Customer action | Slot / field | Required | Notes |
|------|-----------------|--------------|----------|-------|
| **Start** | Tap **开始加车** on Start Card | — | — | Opens guided flow; does not imply quote |
| **1** | **现在请拍 VIN** | `slot_vin_photo` | Yes | One image; text VIN fallback allowed |
| **2** | **现在请拍行驶证** | `slot_registration` | Yes | One image per sub-step; front/back = **two steps**, not one album pick |
| **3** | **现在请拍保险卡（可跳过）** | `slot_insurance_card` | Optional | One image; skip button |
| **4** | **请补提车日期** | `field_delivery_date` | Yes | Text field — not a photo step |
| **5** | — | broker review | — | `guided_workflow_state → broker_reviewing`; Workbench queue |
| **End** | End Card E1 | — | — | 「资料已收到，陈总会人工确认」— not “policy updated” |

**Start Card (summary):** 开始加车 · 陈总会人工确认 · 不用填长表格  
**End Card (summary):** 资料已收齐，已转陈总人工确认 · 不承诺承保/报价

Full copy and slot matrix: `docs/p19_guided_workflow_start_end_card_recon.md` §1.2, §2, §4.1.

---

## C. Interaction rules (customer copy)

| Do | Don't |
|----|-------|
| 「现在请拍 **VIN**」 | 「请上传车辆资料」 |
| 「第 2 步：请拍 **行驶证正面**」 | 「可以一次发多张」 |
| One H5 link per slot (`count=1`) | One link that accepts an album |
| Insurance card **front** = step 3a; **back** = step 3b (if needed) | 「保险卡正反面一起发」 in one step |
| Text steps for dates, ZIP, phone | Photo when a text field suffices |

**Rule:** If a document has two sides, it is **two steps** with two previews — not two images in one picker.

---

## D. Guardrail rule (chat = fallback)

| Layer | Role | Pilot status |
|-------|------|--------------|
| **H5 / future MP guided capture** | **Primary experience** — proactive one-slot, preview, confirm | P19D-2 target |
| **WeCom chat guardrail (P19D-1)** | **Safety net** when customer ignores links and sends chat images | ✅ Shipped |
| **Workbench** | Broker review, quarantine triage, re-prompt | ✅ P19B |

**P19D-1 strict guardrail (live on QA):**

| Condition | Behavior |
|-----------|----------|
| **1 image** in normal slot window | Promote (if slot context allows) |
| **>1 image** in normal slot | **Possible mistake** — 1st promote, rest quarantine + confirm copy |
| **>3 images** in 120s window | **Pause** — bulk_upload_paused; customer told to stop and confirm |
| **Claim lane** | Up to **5 per batch** only with **batch confirm** before next batch; 6th+ quarantine; **no infinite bulk** |

Quarantine is **damage control**, not the product goal. The product goal is **preventing** the album dump via guided H5.

---

## E. Channel architecture (H5 / mini-program)

```text
WeCom chat     = entry · Start Card · text fields · status notify · human trust · link to current step
H5 task page   = current step · take ONE photo · preview · confirm · submit · optional in-page next step
Workbench      = broker review · promoted vs quarantined · re-prompt · confirm (later)
Mini program   = medium-term UX upgrade · NOT current pilot blocker
```

| Channel | Owns upload discipline? |
|---------|-------------------------|
| H5 | **Yes** — `count=1`, preview, slot token |
| Chat | **No** — reactive quarantine only |
| Workbench | **No** — review only |

Validate H5 with Chen Kui **before** investing in mini-program 审核 and native camera polish.

---

## F. Cursor / development guidance (P19D-2+)

### Do NOT build

- ❌ Multi-image upload page
- ❌ “Upload all vehicle documents” album UI
- ❌ Chat-first bulk intake enhancement
- ❌ OCR on quarantined images
- ❌ Slot editor / broker confirm facts (out of P19D-2 scope)

### DO build (P19D-2 MVP)

**Name:** **Single-slot upload page** — not “multi-image upload page.”

| # | Requirement |
|---|-------------|
| 1 | **First MVP scope:** Add Vehicle **`slot_vin_photo` only** |
| 2 | One page shows **only current slot** (title, example image, progress「第 1 步」) |
| 3 | Upload control **`count=1`** (camera or album — UI still single-select) |
| 4 | **Preview** full-screen before submit |
| 5 | **Submit** writes attachment with `slot_assignment`, `source=h5_task`, promoted metadata |
| 6 | **Success** → chat notify + 「下一步」link minted for `slot_registration` (P19D-3 chain) |
| 7 | Reuse P19D-1 guardrail as chat safety net; H5 path should rarely hit quarantine |

**Suggested sequence:**

```text
P19D-1   ✅ Strict chat guardrail (deployed QA)
P19D-2   H5 signed token + single-slot VIN page + upload API
P19D-2.5 Registration single-slot page + in-H5 step chain
P19D-3   Chat template card links + multi-step chain without returning to chat between photo slots
P19D-4+  Mini program (optional, after H5 pilot metrics)
```

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Doctrine adopted as SSOT | **GO** |
| P19D-2 = single-slot H5 (VIN first) | **GO** |
| P19D-2 = multi-image upload page | **HOLD / REJECT** |
| Chat-only pilot without H5 | **HOLD** — guardrail alone is insufficient |
| Mini program before H5 validation | **HOLD** |

---

*P19D core doctrine — documentation only. STOP before implementation.*
