# P19H-3h — Evidence Chain / Broker Review Design

**Date:** 2026-07-10  
**Sprint:** P19H-3h Design  
**Scope:** Audit trail, Workbench review surfaces, exception visibility

---

## 1. Why evidence chain matters

Chen pilot value proposition: **「不用从几十条微信里翻」**.

Without a complete evidence chain:
- Broker cannot trust what customer「officially」submitted vs casual chat
- Duplicate or conflicting inputs create liability confusion
- Post-pilot audit (regulatory, dispute) has no structured record
- H5 investment is wasted if Workbench still shows unstructured blobs

**Evidence chain = who said what, when, through which channel, with what confidence.**

### Core principle — Production-grade workflow product, not AI demo

**做可上线、可卖钱、能省时间的 production 产品，不做 AI 炫技 demo。**

Evidence chain and broker review are **production requirements**, not nice-to-have audit features. A workflow product that brokers cannot trust, audit, or sell on is an AI demo — not shippable software.

| Production requirement | Evidence chain role |
|------------------------|---------------------|
| Key actions auditable | Timeline on every H5 submit, field save, photo upload, broker action |
| Broker final authority | `broker_done` manual only — timeline records Chen's explicit confirmation |
| Commercial value | Broker reviews structured brief in ~10s instead of scrolling 50 WeChat messages |
| AI as assist, not flow | AI-extracted facts tagged provisional; H5/broker confirmation upgrades authority |
| Ship discipline | Design-level test matrix (§10) + smoke before production deploy |

**Together with Structured Task First:** Structured surfaces produce authoritative facts; evidence chain proves what happened; broker review closes the loop. **AI is a capability that enriches the brief — not a substitute for timeline, confirmation, or `broker_done`.**

**Spark Driver parallel:** Drivers trust payout because every trip action is logged and exceptions are visible. Brokers trust intake because every customer action is logged and exceptions are flagged — not because AI summarized a chat thread.

### Core principle — Append-first, Split-later

**先归档，后拆分。**

Customer-facing UX should not make users manage multiple incidents/cases. For Claim/Add Car, ordinary inbound content should append to the current lane/task timeline. AI, broker, and backoffice can later classify, split, merge, archive, or flag if needed. This reduces customer cognitive burden and keeps the workflow production-grade.

| Evidence chain role | Append-first |
|---------------------|--------------|
| **Timeline** | All ordinary supplements append as `customer_text` / media events on current case |
| **Broker review** | `possible_multi_claim_context` flags when multiple open Claims exist — broker splits later |
| **Authority** | Passive accident narrative stays provisional until H5/broker confirms |
| **Exceptions** | Strong explicit new-accident signals may create confirm event — logged in timeline |

---

## 2. What is stored

All evidence lives on the **case document** (Postgres JSON / `service_records.extra`) — no new tables.

| Artifact | Storage | Source tags |
|----------|---------|-------------|
| Message text | `claim_timeline` event | `wecom` |
| H5 field submit | `known_facts` + timeline | `h5_task` |
| Photos | Attachments array + GCS path | `h5_task`, `wecom`, `broker_upload` |
| Timestamps | ISO UTC on every event | System |
| Source channel | `source_channel` on timeline events | `wecom` / `h5_task` / `broker` |
| AI extracted facts | `known_facts` with `extraction_meta` | `ai_extract` (chat path) |
| Customer confirmed facts | `known_facts` from H5 PATCH | `h5_task` (authoritative for structured fields) |

### Fact authority hierarchy

```text
1. Customer H5 submit (structured)     — highest for form fields
2. Customer WeCom explicit confirm     — collision/lane choices
3. AI extraction from chat             — provisional until H5/Review confirms
4. Broker correction (future)          — overrides customer with audit note
```

### Attachment metadata (per photo)

```json
{
  "slot_key": "customer_damage_photo",
  "source": "h5_task",
  "gcs_path": "h5/{case_id}/customer_damage_photo/...",
  "content_sha256": "...",
  "received_at": "2026-07-10T12:00:00Z",
  "flow": "claim_evidence_pack"
}
```

---

## 3. Timeline design

Reuse `append_claim_timeline_event()` / `build_claim_timeline_event()` in `case_store.py`.

### Event types

| event_type | When | Payload highlights |
|------------|------|-------------------|
| `customer_submitted_field` | H5 PATCH step save | `step`, `fields[]`, `source_channel: h5_task` |
| `customer_uploaded_photo` | H5 or WeCom photo | `slot_key`, `attachment_id` |
| `h5_step_complete` | Step validation passed | `step`, `phase_after` |
| `ai_extracted_fact` | Chat extraction | `field`, `confidence`, `raw_snippet` |
| `customer_text` | WeCom free text append | `text_preview` (truncated) |
| `customer_submitted_intake` | H5 final submit | `missing_info_snapshot` |
| `broker_reviewed` | Broker opens case (future) | `broker_id`, `duration_ms` |
| `broker_done` | Broker Done click | `note` optional |
| `system_risk_flag` | Multi-open, collision | `flag_key`, `reason` |

### Timeline dedup

Existing `_claim_timeline_is_duplicate()` — extend for:
- Same `h5_step_complete` + step within 60s
- Same photo `content_sha256` + slot
- Same `customer_submitted_intake` submit_intent_id

### Timeline display (Workbench)

Chronological, newest last or first (match existing drawer). Each row:

```text
[14:32] 客户 · H5 · 事故时间、地点已填写
[14:35] 客户 · H5 · 车损照片已上传
[14:40] 客户 · H5 · 资料已提交
[15:00] 陈总 · 已确认完成
```

---

## 4. Broker Workbench

Existing surfaces (`ClaimCaseBriefPanel`, `ClaimEvidenceChecklist`, drawer) — enrich, do not redesign.

### Case Summary (hero)

From `build_claim_case_brief()`:

| Block | Content |
|-------|---------|
| Title | `Claim · 记录中` / `Broker Review` / `已确认` |
| Key facts | Datetime, location, one-line story, injury, vehicle |
| Phase | `derive_claim_phase()` human label |
| Customer | Display name or `微信客户` |

### Received

| Source | Display |
|--------|---------|
| Structured fields | Checklist with ✅ per `known_facts` key |
| Photos | Slot grid with thumbnail + received/skipped |
| Chat supplements |「微信补充」section if text not in H5 |

### Missing

Mirror Status Card `还缺` logic — **same function**, different presentation:

```text
还缺：对方车牌、现场照片
```

Drives `next_best_question` in brief.

### Risk flags

| Flag | Trigger | Workbench display |
|------|---------|-------------------|
| `possible_multi_claim_context` | Multi-open + ordinary append | Yellow banner:「该客户有多份未完成事故记录」|
| `possible_duplicate` | Similar datetime/location (future) | Suggest merge review |
| `low_confidence_extraction` | AI field confidence < threshold | Show raw snippet |
| `injury_yes` | `anyone_injured = yes` | Red highlight |

### Photos

`ClaimEvidenceChecklist` — per slot:
- Status: missing / received / skipped / needs_retake
- Source badge: H5 / 微信
- Click → full image

### Timeline

Full `claim_timeline` in drawer tab — broker-only detail.

### Done / follow-up

| Action | Effect |
|--------|--------|
| **Broker Done** | Phase → `broker_done`; End Card; remove from active queue |
| **Needs more info** (future) | Phase → `broker_needs_more_info`; WeCom notify + H5 link |
| **Mark duplicate** (future) | Risk flag + note; no customer notify |

---

## 5. Exception handling

### Possible duplicate

| Signal | System behavior |
|--------|-----------------|
| Same customer, similar datetime/location, two open cases | Flag `possible_duplicate`; no auto-merge |
| Broker action | Manual close/merge (future UI) |
| Customer | Not notified of internal flag |

### Possible multi claim

| Signal | System behavior |
|--------|-----------------|
| Multiple open Claims + ordinary traffic | Append to newest; flag `possible_multi_claim_context` |
| Strong new accident narrative | Collision Resolver (WeCom) — customer chooses |
| H5 | Token bound to one case_id; new case = new token |

### Conflicting facts

| Scenario | Resolution |
|----------|------------|
| H5 says Santa Ana; chat says Irvine | H5 wins for `accident_location`; chat preserved in timeline |
| Two injury values | Latest H5 PATCH wins; earlier in timeline |
| Broker sees conflict | Brief shows both with warning icon (future) |

### Low confidence extraction

| Scenario | Resolution |
|----------|------------|
| Chat-only field, no H5 | Show in brief with `待确认` badge |
| H5 completes field | Replace provisional; timeline notes upgrade |
| Broker | Uses `next_best_question` to verify |

---

## 6. Customer-visible vs broker-visible

| Data | Customer sees | Broker sees |
|------|---------------|-------------|
| Phase status | Simple: 记录中 / 已提交 / 已确认 | Full phase enum |
| Missing fields | Status Card 还缺 (plain Chinese) | Full list + field keys |
| Risk flags | **Never** | All flags + timeline notes |
| AI confidence | **Never** | Score + raw snippet |
| Timeline detail | **Never** (only 已收到 summary) | Full chronological log |
| Photo retake needs |「请补传车损照片」| `needs_retake` + reason |
| Multi-open warning | **Never** (no picker) | Banner + case list link |
| Collision state | Confirm Card choices | Pending state in extra |
| Broker Done | End Card ceremony | Internal completion timestamp |

### Customer status simplification map

| Internal phase | Customer label (Status Card / H5 Done) |
|----------------|------------------------------------------|
| `claim_started` … `accident_basics_in_progress` | 资料填写中 |
| `photos_in_progress` | 资料填写中 |
| `intake_ready_for_broker` / `broker_review` | 已提交，陈总确认中 |
| `broker_needs_more_info` | 还需补充资料 |
| `broker_done` | 已确认完成 |

---

## 7. H5 → Workbench handoff ceremony

```text
Customer H5 Submit
    → known_facts complete snapshot
    → claim_timeline: customer_submitted_intake
    → phase: intake_ready_for_broker → broker_review
    → Workbench queue: "Broker Review pending"
    → optional WeCom: 短确认

Broker opens drawer
    → build_claim_case_brief() [read-time, no LLM]
    → evidence checklist populated from attachments
    → missing_info drives highlights

Broker Done
    → broker_done timeline event
    → End Card (WeCom)
    → case leaves active queue
```

**No auto broker_done.** Chen must explicitly confirm — manual trust anchor. This is **non-negotiable production policy** (§1c): automation of broker confirmation would convert a sellable workflow product into an untrusted AI demo.

---

## 8. Add Car evidence chain (Phase 3)

Same pattern, lane-specific event types:
- `add_car_timeline` or unified timeline with `lane: add_car`
- Photo slots from `add_vehicle_photo_flow`
- Workbench uses existing Add Car brief enrichment

---

## 9. Compliance / disclaimer chain

Every customer touchpoint carries record-only framing:

| Surface | Disclaimer |
|---------|------------|
| WeCom Start | 不代表已向保险公司正式报案 |
| H5 footer | 此记录用于陈总办公室整理事故信息 |
| Status Card | 提醒 section |
| End Card | 不代表保险公司结案或赔付 |
| Workbench | No carrier-filing language (`CLAIM_FORBIDDEN_AUTOMATION_CLAIMS`) |

---

## 10. Test matrix (design-level)

| Test | Expected |
|------|----------|
| H5 full trip → Workbench | All key_facts populated; timeline ≥ 6 events |
| Chat supplement only | Timeline has wecom events; brief partial |
| H5 + chat same field | H5 value in brief; both in timeline |
| Multi-open flag | Banner visible; customer Status Card normal |
| broker_done | One End Card; terminal timeline |
| Photo from H5 + WeCom | Both in checklist with correct source badge |

---

*Builds on P19H-3e Claim brief, P19H-3f-5 single active task, existing `claim_timeline` in `case_store.py`.*
