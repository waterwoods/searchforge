# P19B-1 Recon — Workbench Attachment UI Placement

**Date:** 2026-07-05  
**Type:** Product / UX placement recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19B implementation agents  
**Prerequisite:** P19A Loop 2 PASS · `docs/p19_guided_workflow_start_end_card_recon.md` (P19B-0)

**Evaluated surface:** https://ui-smoky-beta.vercel.app/workbench/document-intake  
**Code authority:** `ui/src/pages/DocumentIntakeInboxPage.tsx` (`BrokerCaseDetail` + right `Drawer`)

**This loop:** No code. No deploy.

---

## 1. Verdict (TL;DR)

| Question | Recommendation |
|----------|----------------|
| **Drawer vs new page?** | **Drawer in existing `/workbench/document-intake`** — do not create a standalone documents page for P19B |
| **One case = one surface?** | **Yes** — queue row → Open → single drawer completes broker review for demo |
| **Attachment block position** | **After Next Step + Missing Items, before lane fact cards** |
| **Raw image** | **Inline thumbnail + click-to-expand** in drawer (P19B MVP) |
| **OCR / broker confirm** | **Defer to P19C / P19D** — show `ocr_status: not_started` badge only |
| **Independent page needed?** | **Not for P19B MVP** — see §6 |

---

## 2. Broker Daily Use Path

### 2.1 Chen Kui / office operator path (production demo)

Documented canonical broker URL:

> `https://ui-smoky-beta.vercel.app/workbench/document-intake`

(`docs/p16/P16_CHEN_KUI_DEMO_SCRIPT.md` — "Broker inbox (Wu Xiaojie)")

**Daily loop today:**

```text
Open Office Review Queue
  → scan Customer / Lane / Status / Summary
  → click Open
  → read Next Step banner
  → read Missing Items (if NEED_INFO)
  → read Customer / Vehicle / Warnings
  → Copy Report or Confirm
  → close drawer → next case
```

**Daily loop with P19 WeCom photos (target):**

```text
Open Office Review Queue
  → see attachment indicator on row (📎 count or "New photo")
  → Open case
  → Next Step (unchanged)
  → Missing Items (unchanged)
  → **Attachments** ← NEW: see what customer sent on WeCom
  → Vehicle / packet facts (unchanged)
  → Warnings (unchanged)
  → Confirm / Copy / close
```

**Key observation:** The broker never navigates to a second product. WeCom intake is **evidence arriving into the same case** the office already reviews. A new `/documents` page would break the trained path and add a "where do I click?" moment — exactly the cognitive load P19 must avoid.

### 2.2 What is NOT the primary broker path

| Surface | Route | Role today | P19B priority |
|---------|-------|------------|---------------|
| **Office Review Queue** | `/workbench/document-intake` | Chen Kui demo inbox | **P19B target** |
| Unified Intake Workbench | `/intake` → `BrokerWorkbenchTab` | Paste-triage lab / trial | Secondary — has filename-only attachment links, no preview |
| Customer Wizard | `/add-car` | Customer-facing | Out of scope |

**Recommendation:** Implement P19B attachment UI in `DocumentIntakeInboxPage` first. Optionally extract a shared `<CaseAttachmentsPanel>` component later for `BrokerWorkbenchTab` — do not block P19B on dual-surface parity.

### 2.3 Unassigned WeCom photos

P19A creates `service_lane = wecom_media_intake` holding cases. These are **not** in today's `isP16DocumentCase()` filter — they do not appear in the queue.

**P19B placement:** Same page, **second queue section** above or below main table:

```text
┌─ Unassigned WeCom Photos (N) ─────────────────┐
│ Customer · Received · [Open]                    │
└───────────────────────────────────────────────┘
┌─ Office Review Queue ──────────────────────────┐
│ ... existing lanes ...                          │
└───────────────────────────────────────────────┘
```

Still one URL, one mental model — not a new page.

---

## 3. Should Case Review Be One Page?

### 3.1 Yes — for P19B MVP and Chen Kui demo

| Principle | Rationale |
|-----------|-----------|
| **一案一 drawer** | Broker opens one case; all context visible without navigation |
| **Next Step stays on top** | Action intent unchanged — attachments support the step, don't replace it |
| **Photos adjacent to gaps** | Missing Items → Attachments → Facts is the natural "what's missing / what arrived / what we know" vertical scan |
| **No tab switching** | Tabs inside drawer (Details \| Photos) add friction; vertical scroll is acceptable for 1–5 images |

### 3.2 When one drawer is insufficient (not P19B)

| Situation | Mitigation in-drawer first | New page only if |
|-----------|---------------------------|------------------|
| 5+ accident photos | Thumbnail grid + "show all" expand | 15+ images per case routinely |
| PDF multi-page | Page count badge + open in new tab | Dedicated PDF viewer product |
| OCR field confirm (P19C) | Collapsible "OCR draft" inside drawer | Field-by-field audit across many docs |

**Demo reality:** Most cases have 1–4 attachments. Drawer scroll is fine.

### 3.3 Drawer width

Current: `width={520}`.

| Option | Recommendation |
|--------|----------------|
| Keep 520px | OK for single-column thumbnail (~480px wide) |
| Widen to 560–600px | Optional if inline image feels cramped — not required for MVP |

Do **not** go full-screen modal for MVP — breaks queue context (broker loses sight of list).

---

## 4. Attachment Block Position in Drawer

### 4.1 Current drawer order (`BrokerCaseDetail`)

```text
1. Status tags (READY / BROKER_REVIEW / NEED_INFO + Lane)
2. TopActionBanner — "Next Step"
3. MissingItemsCard — still_needed_fields (NEED_INFO only)
4. Customer / Vehicle / Claim / Policy cards — structured facts
5. Chinese Follow-Up
6. Sources
7. Warnings
8. Actions — Confirm, Copy Report, Delete
```

### 4.2 Recommended order (P19B)

```text
1. Status tags
2. TopActionBanner — "Next Step"                    ← unchanged
3. MissingItemsCard                                 ← unchanged
4. ★ CaseAttachmentsPanel (NEW)                     ← insert here
5. Customer / Vehicle / Claim / Policy cards
6. Chinese Follow-Up
7. Sources
8. Warnings
9. Actions
```

**Why here:**

- Broker reads **what to do** (Next Step) and **what's still missing** before looking at photos.
- Photos are **proof for the fact cards below** — seeing VIN photo immediately above empty VIN field in packet is the "aha" moment.
- Warnings stay near actions — Coverage Risk "do not advise driving" remains the last thing before Confirm.

### 4.3 Drawer layout sketch

```text
┌─ Drawer: 企业微信客户 (尾号 mxcw) · Coverage Risk ─── [×] ─┐
│ [BROKER_REVIEW] [Coverage Risk]                              │
│                                                              │
│ ┌─ Next Step ─────────────────────────────────────────────┐  │
│ │ 陈总人工核实保单状态、停保原因、恢复/替代方案。            │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ Missing Items ────────────────────────────────────────┐  │
│ │ □ DMV notice    □ policy number    □ notice date        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ Attachments (2) ──────────────────── WeCom ──────────┐  │
│ │ ┌─────────────┐  DMV notice · received · Jul 5 8:50pm  │  │
│ │ │  [thumbnail]│  Binding: high · OCR: not started      │  │
│ │ │   240×180   │  [Open full] [Set type ▼]  (P19B+)     │  │
│ │ └─────────────┘                                        │  │
│ │ ┌─────────────┐  unknown_document · unassigned         │  │
│ │ │  [thumbnail]│  Binding: unknown                       │  │
│ │ │             │  [Open full] [Attach to case ▼]        │  │
│ │ └─────────────┘                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ Customer ─────────────────────────────────────────────┐  │
│ │ Name: WeCom - ...mxcw                                   │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Vehicle ──────────────────────────────────────────────┐  │
│ │ (empty — facts come after broker/OCR later)             │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ⚠ Warnings: Coverage status risk — do not advise driving…   │
│                                                              │
│ [Copy Report]  [Copy Portal Format]                           │
│ [Delete demo case]                                            │
└──────────────────────────────────────────────────────────────┘
```

### 4.4 Queue list enhancement (same page)

Add lightweight row signal — no new page:

| Column / signal | MVP |
|-----------------|-----|
| 📎 icon + count | If `case_attachments.length > 0` |
| "New photo" dot | If attachment `received_at` within 24h (optional) |
| Unassigned section | `wecom_media_intake` lane rows |

---

## 5. How to Display: Image / Metadata / Slot / OCR

### 5.1 Display layers (P19B vs later)

| Layer | P19B MVP | P19C | P19D |
|-------|----------|------|------|
| **Raw image** | Thumbnail + open full | Same | Same |
| **Metadata** | type, time, source, size, binding | + ocr_status | + slot assignment |
| **Slot** | Read-only hint if `document_type` maps to slot | — | Interactive checklist |
| **OCR draft** | Badge `not_started` only | Expandable draft fields | — |
| **Broker confirm** | — | Per-field confirm | Document confirm |

### 5.2 Per-attachment card (MVP)

```text
┌──────────────────────────────────────────┐
│ [Thumbnail  max 200px height]            │
│                                          │
│ renewal_notice          [medium]         │  ← document_type + confidence badge
│ WeCom · Jul 5, 8:50 PM · 232 KB        │  ← source · received_at · size
│ Binding: high                          │  ← binding_confidence
│ OCR: not started                         │  ← ocr_status (static in P19B)
│ [Open full size]                         │  ← new tab or Modal image viewer
└──────────────────────────────────────────┘
```

**Thumbnail source:** New backend endpoint required for GCS WeCom attachments — current `GET /cases/{id}/attachments/{id}` serves **local files only** (`get_attachment_file_path`). P19B backend must add auth-gated proxy or signed URL for `storage_uri` (gs://). UI placement unchanged.

### 5.3 Metadata field display rules

| Field | Show in UI | Format | Never show |
|-------|------------|--------|------------|
| `attachment_id` | Broker debug only | Truncate `att_…` | — |
| `source` | Yes | `WeCom` tag | — |
| `received_at` | Yes | Local datetime | — |
| `mime_type` | Yes | `JPEG` / `PDF` | — |
| `size_bytes` | Yes | KB/MB | — |
| `document_type` | Yes | Human label + confidence color | — |
| `binding_confidence` | Yes | high/medium/low/unknown | — |
| `intake_status` | If unassigned | `unassigned` warning | — |
| `ocr_status` | Yes | Badge only | OCR field values |
| `storage_uri` | No | — | Full gs:// path |
| `external_userid` | No | — | Full ID — use masked customer label |
| `msg_id` | Optional debug | Truncate | Full in copy |

### 5.4 Slot display (P19B = read-only hint)

Map `document_type` → slot label from P19B-0 §4 (no interactive slot editor in P19B):

| document_type | Slot hint label |
|---------------|-----------------|
| `vin_photo` | VIN photo |
| `registration` | Registration |
| `renewal_notice` | Renewal notice |
| `accident_photo` | Accident photos |
| `dmv_notice` | DMV notice |

Show as subtle subtitle under type: `Slot: VIN photo` — prepares for P19D checklist without building checklist UI now.

### 5.5 OCR status (P19B)

| ocr_status | UI |
|------------|-----|
| `not_started` | Gray badge "OCR: not started" |
| `queued` / `draft` / `confirmed` / `failed` | **Hide detail in P19B** — show "OCR: pending" or hide row until P19C |

Do not render `ocr_draft` field values in P19B.

### 5.6 Empty state

When `case_attachments.length === 0`:

```text
┌─ Attachments ─────────────────────────────┐
│ No photos yet. Customer may send via WeCom. │
└───────────────────────────────────────────┘
```

Do not hide the section — broker learns to expect it.

---

## 6. When a Standalone Documents Page Is Warranted

**Not for P19B.** Defer until at least one trigger is true:

| Trigger | Threshold | Why separate page might help |
|---------|-----------|------------------------------|
| Volume | 20+ attachments per case common | Drawer scroll exhaustion |
| Cross-case ops | Daily bulk reassign across 50+ orphan photos | Dedicated unassigned workbench |
| OCR confirm UI | Field-by-field confirm on 10+ docs per case | Split-pane doc viewer + form (P19C+) |
| Compliance audit | External auditor needs read-only doc portal | Separate auth surface |
| Non-case documents | Firm-wide document library unrelated to cases | Different product |

**Chen Kui demo:** None of these apply. Stay on one queue + one drawer.

### 6.1 Anti-patterns (do not build)

| Anti-pattern | Why |
|--------------|-----|
| `/workbench/attachments` top-level nav | Splits attention from case queue |
| Full-screen document viewer as default | Loses case context |
| Duplicate attachment UI in 3 surfaces | Maintenance + drift |
| OCR-first layout | Violates "raw image first" principle |

---

## 7. P19B MVP — Minimum UI Scope

### 7.1 In scope (P19B MVP)

| # | Feature | Surface |
|---|---------|---------|
| 1 | `CaseAttachmentsPanel` in drawer | `DocumentIntakeInboxPage` |
| 2 | Inline image thumbnail (JPEG/PNG) | Per attachment card |
| 3 | PDF placeholder + open/download | Icon + link if not inline-renderable |
| 4 | Metadata row: type, confidence, source, time, size, binding | Per attachment card |
| 5 | `ocr_status` badge (`not_started` only) | Per attachment card |
| 6 | Open full size (new tab or Modal) | Per attachment |
| 7 | Empty attachments state | Drawer section |
| 8 | Queue row 📎 count | Main table |
| 9 | Unassigned `wecom_media_intake` queue section | Same page |
| 10 | GCS auth-gated preview API | Backend prerequisite |

### 7.2 Stretch (still P19B if cheap)

| # | Feature |
|---|---------|
| 11 | Manual document type dropdown |
| 12 | Reassign attachment to another case |
| 13 | Drawer width 560px |

### 7.3 Explicitly out of P19B

| Item | Loop |
|------|------|
| OCR draft field panel | P19C |
| Broker confirm OCR → facts | P19C |
| Interactive document checklist / slots | P19D |
| Guided customer upload buttons | P19D |
| Ask customer for clearer photo (outbound) | P19D |
| Standalone documents page | Not planned for pilot |
| `BrokerWorkbenchTab` parity | Post-P19B optional |

### 7.4 MVP field list (attachment card)

**Must display:**

```typescript
// P19B MVP — per case_attachments[] item
{
  attachment_id,      // truncated, optional
  source,             // "wecom"
  mime_type,          // display label
  size_bytes,
  received_at,        // or created_at fallback
  document_type,      // humanized
  document_type_confidence,
  binding_confidence,
  ocr_status,         // badge only
  intake_status,      // if "unassigned"
  // thumbnail via preview_url from API — not storage_uri
}
```

**API addition (backend P19B, not UI-only):**

```typescript
preview_url: string;  // auth-gated, short TTL — never public GCS URL
```

**Must not display:**

- Full `external_userid`
- `storage_uri` / public GCS URL
- `ocr_draft` values
- Coverage / quote / claim conclusions derived from image

---

## 8. Implementation Notes (for P19B agents — do not build in this loop)

| File | Change |
|------|--------|
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Add `CaseAttachmentsPanel`; extend `isP16DocumentCase` or add unassigned filter |
| `ui/src/features/intake/components/CaseAttachmentsPanel.tsx` | **New** shared component (recommended) |
| `services/fiqa_api/routes/inbox_triage.py` | GCS preview/download for WeCom `storage_uri` |
| `ui/src/api/inboxTriage.ts` | Extend `CaseAttachment` type with WeCom fields + `preview_url` |

**Do not** create new route in `App.tsx` or `OfficeReviewShell` nav for P19B.

---

## 9. Recon Verdict

| Question | Answer |
|----------|--------|
| **Recommended placement** | **Existing `/workbench/document-intake` right drawer** — `CaseAttachmentsPanel` after Missing Items |
| **New page?** | **No** for P19B MVP |
| **One case one drawer?** | **Yes** |
| **Raw image priority** | Thumbnail inline in drawer; full size on demand |
| **OCR / confirm** | Badge only in P19B; full UI in P19C/D |
| **Code changed** | **No** |
| **Deploy** | **No** |

### 9.1 Strongest placement insight

> **Attachments are not a separate product — they are evidence inside the case the broker already opens.**  
> The drawer order **Next Step → Missing → Photos → Facts → Warnings** mirrors how 陈总 already thinks: what do I do, what's missing, what did the customer send, what does the system know, what must I not say.

---

## Related Documents

| Doc | Role |
|-----|------|
| `docs/p19_guided_workflow_start_end_card_recon.md` | P19B-0 workflow + slot design |
| `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` | P19B acceptance criteria §14 |
| `docs/evidence/p19a_loop2_live_wecom_image_smoke_2026_07_05.md` | Attachment metadata shape |
| `docs/p16/P16_CHEN_KUI_DEMO_SCRIPT.md` | Canonical broker URL |
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Current drawer implementation |

---

*P19B-1 recon complete — documentation only. STOP.*
