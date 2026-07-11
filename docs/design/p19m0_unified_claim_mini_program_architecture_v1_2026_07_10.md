# P19M-0 — Unified Claim Mini Program Architecture V1

> **本文档取代所有以 H5 + WeCom 双输入作为长期目标的客户体验设计。**
> 旧文档（`p19h3h_*`, `p19h3i_*`, `p19h3j_*`）仍作为历史证据和后端流程参考，但不再定义目标客户前台。

---

## 0. Document Status

| Field | Value |
|-------|-------|
| **Status** | **DRAFT FOR FOUNDER REVIEW** |
| **Owner** | P19M Architecture Freeze (Cursor agent) |
| **Date** | 2026-07-10 |
| **Branch** | `sprint/p16-trust-layer` |
| **Starting commit** | `d413434` — fix: clarify H5 and WeCom channel responsibilities |
| **Related historical docs** | `p19h3h_master_design_summary_2026_07_10.md`, `p19h3h_product_architecture_wecom_h5_workbench_2026_07_10.md`, `p19h3h_claim_h5_task_state_machine_2026_07_10.md`, `p19h3i_claim_task_dashboard_always_return_h5_2026_07_10.md`, `p19h3j_h5_wecom_channel_ux_policy_2026_07_10.md`, `p19e3_channel_strategy_wecom_h5_miniprogram_recon.md` |
| **Not approved for implementation** | Yes — no Prototype code until Gate 0 |
| **Approval gate** | Founder must approve this SSOT before P19M-1 Prototype |

---

## 1. Executive Decision

Insurance Unified Intake has validated the Claim workflow on H5 + WeCom dual-channel. Founder has now decided: **the WeChat Mini Program becomes the sole Customer Task App** — the only place customers perform structured accident intake, review, and submit.

WeCom / Enterprise WeChat retains **entry, notification, reminder, and broker communication** only. It sends mini program task cards; it does not run a parallel wizard.

Existing H5 (`/task/claim/:taskToken`, `H5ClaimIntakePage.tsx`) is **retained as fallback, QA asset, and API reference** — not deleted, not the primary entry.

Backend reuse is mandatory: `derive_claim_phase()`, `case_store.py`, `h5_task_intake.py` business logic, evidence pipeline, Broker Workbench — not rewritten.

Prototype scope is **one complete Claim loop** for a single tenant (Chen pilot config). Not a full insurance platform.

This document is architecture-only. **No code, no mini program project, no deploy, no schema migration** in P19M-0.

---

## 2. Product North Star

**North Star:**

```text
Customer receives one task
→ opens one Mini Program surface
→ provides text / voice / photos
→ AI organizes
→ customer reviews
→ submits once
→ Broker understands in 10 seconds
```

**Success experience:**

| Principle | Meaning |
|-----------|---------|
| One task | Customer perceives exactly one current accident task |
| One page system | Task Home → Guided Step → Review → Submit — no insurance mall homepage |
| One next action | Every screen has one obvious primary CTA |
| One submit exit | `POST submit` is the formal broker handoff — not WeCom chat |
| Return anytime | Resume lands on same task via session + task binding |
| No data loss | Append-first; chat mis-sent content saved, not discarded |
| Hidden complexity | No lanes, inbox, provenance, workflow phase exposed to customer |

---

## 3. Product Boundaries

### In scope

- Customer accident资料收集 (text, voice, photos)
- Task coordination and status
- Case establishment and evidence management
- AI extraction, categorization, missing-item detection, summary
- Broker review via existing Workbench
- WeCom entry / notification / supplement safety net
- H5 fallback for QA and emergency

### Out of scope

- Insurance quoting, underwriting, coverage decisions
- Liability / fault determination
- Official carrier filing or claim adjudication
- Payment / disbursement
- Carrier system replacement
- Full CRM, multi-broker admin UI
- Add Car lane in Prototype
- OCR, carrier API integration

### Future possibilities (not Prototype)

- Video / large file upload
- Full multi-tenant admin portal
- Native broker mobile app
- Proactive push notifications beyond WeCom cards
- Voice ASR production pipeline (if WeChat API insufficient)

### Explicitly NOT

- Insurance claim filing platform
- Carrier system
- CRM replacement
- Coverage/fault decision engine
- Quoting system

---

## 4. Target Users

### Customer (accident reporter)

| | |
|-|-|
| **Goal** | Report accident once, supplement later, know status |
| **Pain** | Lost in WeChat threads; unsure what's missing; double-submit anxiety |
| **Main action** | Open mini program → fill story → add photos → review → submit |
| **Never needs to understand** | case_id, lane, claim_phase, provenance, inbox, split/merge, AI confidence |

### Broker / office staff (Chen Kui pilot)

| | |
|-|-|
| **Goal** | Understand case in ~10s; confirm done; request more info |
| **Pain** | Scrolling 50 WeChat messages; missing materials; duplicate asks |
| **Main action** | Workbench drawer → brief + timeline + photos → Broker Done |
| **Never needs to understand** | Mini program internals, wx.openid, token HMAC |

### Tenant admin (future)

| | |
|-|-|
| **Goal** | Configure branding, fields, disclaimers per office |
| **Pain** | Per-broker code forks |
| **Main action** | Tenant config (future) — logo, copy, field policy |
| **Never needs to understand** | Case engine implementation |

### System operator (Andy / engineering)

| | |
|-|-|
| **Goal** | Deploy, smoke, recover, audit |
| **Pain** | Channel drift; undeployed fixes; Workbench public access |
| **Main action** | Run guardrails, smoke scripts, monitor timeline integrity |
| **Never needs to understand** | Customer-facing copy nuances (product owns) |

---

## 5. Target Experience Model

### Customer mental model

> 「我只有一个当前事故任务。」

### WeCom mental model

> 「聊天用于收到任务和联系 Broker。」

### Mini Program mental model

> 「这里是我完成事故资料的唯一地方。」

### Broker mental model

> 「这是一个持续更新、有来源、有状态的 Case。」

### Forbidden customer-visible concepts

`staging`, `inbox`, `draft fact`, `provenance confidence`, `workflow lane`, `split/merge`, `service_lane`, `guided_workflow_state`, `h5t1`, `external_userid`

---

## 6. End-to-End Customer Journey

| # | Step | Customer sees | Customer action | Backend action | State transition | Failure recovery | Analytics event |
|---|------|---------------|-----------------|----------------|------------------|------------------|-----------------|
| 1 | Task card | WeCom Start/Resume card with mini program CTA | Tap card | `claim_basics` creates case; mint task invitation; send card | `claim_started` | Card send fail → operator alert; customer can retry「我要理赔」 | `wecom_task_card_sent` |
| 2 | Open task | Mini Program loading → Task Home | Open from card | Session bind; `intake_info_for_token` equivalent | unchanged | Expired session → re-open card or「进度」 | `mp_task_opened` |
| 3 | Safety intro | Disclaimer + office name | Tap「开始」 | Read case; no write | unchanged | Token/session invalid → Help screen | `mp_safety_ack` |
| 4 | Accident basics | Injury radio | Select + Next | `patch_intake_fields` step=`injury` | `accident_basics_in_progress` | PATCH fail → retry toast | `mp_step_injury` |
| 5 | Story | Textarea or voice | Enter narrative | PATCH step=`story`; optional ASR | same | Network fail → local draft + retry | `mp_step_story` |
| 6 | Time/location | Date + location fields | Fill + Next | PATCH step=`time_location` | may → `accident_basics_complete` | Validation error inline | `mp_step_time_location` |
| 7 | Injury (if not done) | (merged in step 4 for prototype) | — | — | — | — | — |
| 8 | Other party | Vehicle + plate fields | Fill + Next | PATCH step=`vehicle_other_party` | `other_party_in_progress` | Soft-warn if empty | `mp_step_vehicle` |
| 9 | Photos | Camera / album slots | Upload 2+ photos | `ingest_h5_slot_upload` (reuse) | `photos_in_progress` → `photos_complete` | Upload retry; hash dedup | `mp_photo_upload` |
| 10 | AI organizes | (background) | — | Extraction on timeline events; `build_claim_case_brief` | unchanged | AI fail → show raw input in Review | `mp_ai_organize` |
| 11 | Missing guidance | Missing Items screen | Tap item → jump to step | `get_claim_missing_items()` | unchanged | — | `mp_missing_view` |
| 12 | Review | Summary of 已填写 / 还缺 / 照片 | Edit links or Submit | Read `intake_info_for_token` | unchanged | Missing required → disabled submit | `mp_review_view` |
| 13 | Submit | Primary CTA「提交给陈总」 | Tap once | `submit_intake_form` + idempotency | → `intake_ready_for_broker` / `broker_review` | Double-tap safe; 409 → Receipt | `mp_submit` |
| 14 | Receipt |「已提交」+ next steps | Done or supplement | Optional `try_send_h5_submit_confirmation` → WeCom ack | `broker_review` | WeCom notify fail → non-blocking | `mp_submit_receipt` |
| 15 | Resume later | Task Home with dashboard | Return via card or history | Same case_id; refresh intake info | unchanged | New session bind to same task | `mp_resume` |
| 16 | Post-submit supplement | Task Home「继续补充」 | Add photo/text in MP | Append timeline; not new submit | stays `broker_review` | — | `mp_post_submit_supplement` |
| 17 | Broker needs more | WeCom reminder card → MP | Fill requested items | Phase → `broker_needs_more_info` (future) | `broker_needs_more_info` | — | `mp_broker_needs_more` |
| 18 | Broker done | WeCom End Card | — | `mark_claim_broker_done` | `broker_done` | End card dedup | `broker_done` |

---

## 7. Mini Program Information Architecture

No traditional insurance homepage. Open → current task directly.

| # | Page | Purpose | Primary info | Primary CTA | Secondary | Empty state | Error state | Analytics | API dependency |
|---|------|---------|--------------|-------------|-----------|-------------|-------------|-----------|----------------|
| 1 | Task Entry / Loading | Bind session; resolve current task | Office name, loading | — | — | First visit welcome | Session fail → Help | `mp_entry` | Auth + `GET .../tasks/current` |
| 2 | Task Home | Orient; show progress | Status, received, missing, next |「继续填写」or「去提交」 | Contact broker | New task: safety copy | Case not found | `mp_home` | `intake_info` payload |
| 3 | Guided Step | One field group per screen | Step question + progress |「下一步」 | Back | — | Save fail retry | `mp_step` | `PATCH .../fields` |
| 4 | Media Capture | Photo evidence | Slot labels + thumbnails |「上传」/ Next | Skip optional | No photos yet | Upload fail per slot | `mp_media` | `POST .../upload`, `.../skip` |
| 5 | AI Review | Show organized facts | AI-suggested groupings |「确认」→ Review | Edit | No AI → skip to Review | — | `mp_ai_review` | brief read |
| 6 | Missing Items | Checklist | 还缺 list | Tap item → step | Skip to Review | All complete → auto Review | — | `mp_missing` | `get_claim_missing_items` |
| 7 | Final Review | Pre-submit summary | 已填写 / 还缺 / 照片 |「提交给陈总确认」 | Per-section edit | — | Submit disabled if gaps | `mp_final_review` | `GET intake` |
| 8 | Submit Receipt | Confirmation | 已提交 message |「返回」/「继续补充」 | — | — | — | `mp_receipt` | post-submit intake |
| 9 | Status / Resume | Return visit | Dashboard summary | Primary CTA from `dashboard_summary` | Refresh | — | Expired → Help | `mp_status` | `intake_info` |
| 10 | Error / Expired / Help | Recovery | Instructions |「联系陈总」/ re-open WeCom | — | — | All error codes | `mp_error` | — |

**Design rules:** one primary action per screen; no six-grid insurance mall; no internal workflow picker; Task Home is default landing after entry.

---

## 8. Screen-by-Screen Wireframe Skeleton

### Task Home

```text
[我的事故资料]
[状态：资料收集中]
[进度：3/6 已完成]

[已收到]
  ✓ 受伤情况：没有受伤
  ✓ 事故经过：…
  ○ 事故时间/地点

[还缺]
  · 车损照片
  · 对方车牌（可选）

[下一步]
  请补充事故时间和车损照片

[继续填写]          ← Primary CTA (Spark: one next action)
[联系陈总办公室]     ← Secondary

[此记录用于办公室整理事故信息，不代表已向保险公司正式报案]
```

*Reference mechanism:* Spark Driver one-next-action; TurboTax dashboard missing/received; Chinese insurance mini programs task continuity (conceptual — not copying any specific UI).

### Story (voice/text)

```text
[事故经过]  2/6
[请描述发生了什么]

[🎤 按住说话]  or  [文字输入框…………]

[AI 会帮你整理，提交前你可以修改]

[下一步]
[返回]
```

*Reference:* TurboTax guided interview; voice optional in Prototype.

### Photo capture

```text
[事故照片]  5/6
[请上传车损和现场照片]

[📷 车损照片]  [缩略图或 +]
[📷 现场照片]  [+]

[已上传 1/2 张]

[下一步]
[稍后再传]
```

*Reference:* Spark evidence capture; reuse `claim_evidence_pack` slots.

### Missing item

```text
[还差这些资料]
[提交前建议补全：]

  ○ 事故时间
  ○ 车损照片

[去补充]            ← jumps to step
[先去看看总结]
```

*Reference:* TurboTax missing-items gate before filing.

### Review

```text
[确认资料]
[提交前请检查]

已填写
  受伤：没有受伤
  时间：2026-07-10 10:00
  地点：Irvine Blvd
  经过：…
  照片：2 张

还缺（可选）
  对方车牌

[提交给陈总确认]     ← Primary (large, disabled until ready)
[修改某一项]
```

*Reference:* TurboTax review-before-file; H5 `review` step semantics from `H5ClaimIntakePage.tsx` — **not** visual copy.

### Submit receipt

```text
[✅ 已提交给陈总]

[陈总会人工确认后联系您]
[您仍可继续补充照片和细节]

[继续补充资料]
[完成]
```

### Status / Resume (submitted)

```text
[我的事故资料]
[状态：已提交，陈总确认中]

[已收到 …]
[下一步：等待陈总确认]

[继续补充资料]       ← Primary
[刷新状态]
```

---

## 9. Input Model

### Text

| Mode | Behavior |
|------|----------|
| Direct structured | PATCH per step via `patch_intake_fields()` |
| Free text | Story step; min length validated in `_validate_step_fields` |
| AI extraction | Background from timeline; draft in brief — not auto-confirmed |
| Customer confirmation | Final Review screen; submit = confirm |

### Voice

| Stage | Prototype | Production |
|-------|-----------|------------|
| Record | Nice-to-have | `wx.getRecorderManager` |
| Upload | POST voice endpoint (new) | GCS + attachment |
| Transcription | Mock or WeChat plugin — **official capability unverified** | ASR service |
| Editable transcript | Required before confirm | Customer edits in Review |
| Confirm | Same as text PATCH to `accident_description` | — |

### Photo

| Stage | Implementation |
|-------|----------------|
| Camera / album | `wx.chooseMedia` → multipart POST |
| Upload | Reuse `ingest_h5_slot_upload()` via facade |
| Slots | `customer_damage_photo`, `other_party_vehicle_photo`, `scene_photo` |
| Dedup | `h5_photo:{case_id}:{slot}:{content_sha256}` pattern from smooth UX doc |
| Thumbnail | Client preview + server attachment metadata |
| Timeline | `customer_uploaded_photo` event, `source_channel: customer_task` |

### Video / File

**Prototype:** Out. **Future:** size limits, virus scan, presigned upload — reuse GCS path pattern from `media_storage.py`.

### WeChat chat mis-sent content

| Rule | Behavior |
|------|----------|
| Must not be lost | `ingest_wecom_text_to_active_case` / `ingest_wecom_media_message` |
| External supplement | Provenance `wecom_customer_text` / `customer_supplement` |
| Not primary workflow | No wizard in chat |
| Review surfacing |「另外收到的资料」section in Review (Prototype: save only) |
| MP adoption | WeCom ack directs to mini program card, not H5 URL as primary |

---

## 10. State Machine Mapping

**SSOT:** `services/fiqa_api/wecom/claim_state.py` — `derive_claim_phase()`, `get_claim_missing_items()`. Frontend must not invent phases.

| Backend phase (`derive_claim_phase`) | MP customer state | Visible label | Allowed actions | API | Next state |
|--------------------------------------|-------------------|---------------|-----------------|-----|------------|
| `claim_started`, `accident_basics_in_progress` | collecting | 资料填写中 | Edit steps, upload | PATCH fields | basics complete |
| `accident_basics_complete`, `photos_in_progress` | collecting | 资料填写中 | Photos, story | upload | photos_complete |
| `photos_complete`, `other_party_in_progress` | collecting | 资料填写中 | Vehicle fields | PATCH | other_party_complete |
| `summary_ready` (missing items) | missing | 还差一些资料 | Missing Items screen | GET intake | review_ready |
| `summary_ready` (complete) | review_ready | 可以提交 | Review, Submit | GET intake | submitted |
| `intake_ready_for_broker`, `broker_review` | submitted | 已提交，确认中 | Supplement only | append media | broker_review |
| `broker_needs_more_info` | needs_more_info | 还需补充 | Guided补资料 | PATCH (policy TBD) | resubmit |
| `broker_done` | done | 已确认完成 | Read-only | GET status | terminal |
| Token/session invalid | expired | 链接已失效 | Help / re-open WeCom | — | recovery |
| API 5xx / network | error | 暂时无法连接 | Retry | — | previous |

**Rules:**

- `broker_done` only via `mark_claim_broker_done()` — Broker Workbench `POST /api/inbox/cases/{id}/broker-done`
- Customer visible states are a **projection** of backend phases — simpler labels only
- MP `current_step` in `h5_intake_state` JSON is UX hint — `derive_claim_phase` wins on conflict

---

## 11. Existing H5 → Mini Program Mapping

See companion doc: `p19m0_h5_to_mini_program_mapping_2026_07_10.md`.

Summary:

| H5 capability | Reuse |
|---------------|-------|
| `intake_info_for_token` | **Direct** — response shape |
| `patch_intake_fields` | **Direct** |
| `submit_intake_form` | **Direct** |
| `ingest_h5_slot_upload` | **Direct** |
| `h5t1` token | **Adapt** — add MP session binding; possibly task invitation code |
| `H5ClaimIntakePage.tsx` UI | **Replace** — new MP pages; same semantics |
| Dashboard (`dashboard_summary`) | **Adapt** — Task Home |
| WeCom H5 URL CTAs | **Replace** — mini program path cards |

**Do not** mechanically copy `H5ClaimIntakePage.tsx` layout, inline styles, or React stepper.

---

## 12. API Contract V1

Channel-neutral facade over existing H5 implementation. **Prototype may call H5 paths directly** via adapter; production should migrate to neutral names.

### Authentication model (all customer task APIs)

| Method | Prototype | Production |
|--------|-----------|------------|
| Task token in URL | Reuse `h5t1.*` from WeCom card query | Same + short-lived MP session |
| Session header | `X-Customer-Session` (new, TBD) | wx.login → server session |
| Credential | Token IS credential today (`verify_h5_task_token`) | Token + openid binding |

### Endpoints

#### `GET /api/customer/tasks/current`

| | |
|-|-|
| **Purpose** | Resolve active Claim task for bound identity |
| **Auth** | MP session or `external_userid` + tenant |
| **Request** | Headers: session; optional `tenant_id` |
| **Response** | Same as `intake_info_for_token` + `task_id` (= case_id) |
| **Idempotency** | Read-only |
| **Allowed states** | Any non-terminal |
| **Errors** | `404 no_active_task`, `401 session_invalid` |
| **Existing mapping** | **New** — wrap `find_active_claim_for_user()` from `claim_basics.py` + `intake_info_for_token` |
| **Prototype status** | Nice-to-have; can open via token from card query only |

#### `GET /api/customer/tasks/{task_id}`

| | |
|-|-|
| **Purpose** | Full task state (alias of intake GET) |
| **Auth** | Task token or session proving access to case_id |
| **Request** | `task_id` = `case_id`; or token in path |
| **Response** | `intake_info_for_token()` output — see `routes/h5_task_intake.py` `get_h5_intake` |
| **Idempotency** | Read-only |
| **Allowed states** | All |
| **Errors** | `403 invalid_or_expired_task_link`, `404 case_not_found` |
| **Existing mapping** | **Reuse** `GET /api/h5/tasks/{task_token}/intake` |
| **Prototype status** | **Must** — via H5 path or alias router |

#### `PATCH /api/customer/tasks/{task_id}/fields`

| | |
|-|-|
| **Purpose** | Save wizard step fields |
| **Auth** | Token |
| **Request** | `{ "step": "injury", "fields": { "anyone_injured": "no" } }` |
| **Response** | Updated intake info |
| **Idempotency** | `h5_field:{case_id}:{step}:{value_hash}` in `h5_task_intake.py` |
| **Allowed states** | Not submitted |
| **Errors** | `409 already_submitted`, `400 unsupported_step` |
| **Existing mapping** | **Reuse** `PATCH /api/h5/tasks/{token}/fields` → `patch_intake_fields()` |
| **Prototype status** | **Must** |

#### `POST /api/customer/tasks/{task_id}/media`

| | |
|-|-|
| **Purpose** | Upload photo to evidence slot |
| **Auth** | Token |
| **Request** | multipart: `file`, `slot` |
| **Response** | Upload result from `ingest_h5_slot_upload()` |
| **Idempotency** | content SHA256 per slot |
| **Allowed states** | Not `broker_done` |
| **Errors** | `403 user_ref_mismatch`, `400 slot_required` |
| **Existing mapping** | **Reuse** `POST /api/h5/tasks/{token}/upload` |
| **Prototype status** | **Must** |

#### `POST /api/customer/tasks/{task_id}/voice`

| | |
|-|-|
| **Purpose** | Upload voice note for transcription |
| **Auth** | Token |
| **Request** | multipart audio |
| **Response** | `{ transcript_draft, attachment_id }` |
| **Idempotency** | TBD |
| **Allowed states** | collecting |
| **Errors** | `501 not_implemented` in Prototype if mocked |
| **Existing mapping** | **New** — no existing endpoint |
| **Prototype status** | Nice-to-have / mock |

#### `POST /api/customer/tasks/{task_id}/review`

| | |
|-|-|
| **Purpose** | Customer confirms AI-organized facts (optional explicit confirm) |
| **Auth** | Token |
| **Request** | `{ "confirmed_fields": [...] }` |
| **Response** | Updated intake info |
| **Idempotency** | TBD |
| **Allowed states** | pre-submit |
| **Existing mapping** | **Not needed for Prototype** — Review is read + Submit |
| **Prototype status** | Out |

#### `POST /api/customer/tasks/{task_id}/submit`

| | |
|-|-|
| **Purpose** | Formal broker handoff |
| **Auth** | Token |
| **Request** | `{ "submit_intent_id": "uuid" }` + header `X-Submit-Intent-Id` |
| **Response** | intake info + `already_submitted` flag |
| **Idempotency** | `submit_intent_id` stored in `h5_intake_state.submit_intent_ids` |
| **Allowed states** | review_ready; not already submitted |
| **Errors** | `400 missing_required_fields`, `409 already_submitted` |
| **Existing mapping** | **Reuse** `POST /api/h5/tasks/{token}/submit` → `submit_intake_form()` |
| **Prototype status** | **Must** |

#### `GET /api/customer/tasks/{task_id}/status`

| | |
|-|-|
| **Purpose** | Lightweight poll for Task Home |
| **Auth** | Token / session |
| **Response** | `{ phase, customer_label, missing_count, submitted }` |
| **Existing mapping** | Subset of intake GET |
| **Prototype status** | Optional — full intake GET sufficient |

#### `POST /api/customer/tasks/{task_id}/resume`

| | |
|-|-|
| **Purpose** | Re-mint task invitation after expiry |
| **Auth** | WeCom-signed request or session |
| **Response** | `{ task_token, mini_program_path }` |
| **Existing mapping** | Partial — `mint_h5_claim_intake_form_link()` in `h5_task_link.py` |
| **Prototype status** | Adapt — WeCom「进度」flow |

**Migration strategy:** Add `routes/customer_task.py` facade that delegates to `h5_task_intake` + `h5_task_upload` — **no rewrite** of business logic in P19M-1.

---

## 13. Authentication and Identity

### Identity layers

| ID | Role | Source |
|----|------|--------|
| `wecom_external_userid` | WeCom customer key | WeCom callback — stored on case as `wecom_external_userid` |
| `wechat_openid` | Mini program user key | `wx.login` → `code2session` — **official binding to external_userid unverified** |
| `unionid` | Cross-app identity | Only if same WeChat Open Platform — **unknown for pilot** |
| `customer_id` | Internal stable ID | **Not implemented** — future |
| `case_id` / `task_id` | Task binding | Postgres `service_records.id` |
| `tenant_id` | Office isolation | **Not authoritative today** (`tenant_id_authoritative: null` in deployment profile) |
| `h5t1` token | Task invitation credential | `issue_h5_intake_form_token()` — 72h TTL |

### Rules

- Nickname (`customer_profile.py`) is **display-only**
- `external_userid` alone is not portable outside WeCom
- Phone optional for Prototype
- Pilot path: **WeCom task card carries `task_token` or `case_id` in mini program query** → MP stores session
- Perfect unified identity: **deferred**

### Official WeChat capabilities requiring validation

| Capability | Status |
|------------|--------|
| Enterprise WeChat → Mini Program card | **Unverified** |
| `wx.login` in mini program for US users | **Unverified** |
| Mini program category for insurance资料收集 | **Unverified** — may need specific 类目 |
| Overseas entity registration | **Unverified** — blocker risk |
| WeCom `external_userid` ↔ mini program `openid` mapping API | **Unverified** |
| Voice recognition plugin | **Unverified** |

**Do not fake conclusions.** Prototype Gate 1 must validate feasibility.

---

## 14. Multi-Tenant Architecture

### Model

```text
One mini program codebase
One backend deployment
Many tenants via configuration
```

| Config item | Storage (future) |
|-------------|------------------|
| `tenant_id` | API key / JWT claim / env per deploy |
| Office name, logo, theme | tenant config JSON |
| Broker display name | config |
| Welcome copy, disclaimer | config — today hardcoded「陈总」in `CLAIM_INTAKE_SAFETY_COPY` |
| Field requirements | per-tenant override on `get_claim_missing_items` |
| Workflow policy | lane config |
| Data isolation | `tenant_id` on cases — **not enforced today** |
| Storage namespace | GCS path prefix by tenant |
| API authorization | broker API key per tenant |

### Questions answered

| Question | Answer |
|----------|--------|
| One or many mini programs? | **One app, multi-tenant config** (Founder Decision 9) |
| Prototype tenant count? | **Single** — Chen pilot hardcoded config |
| Avoid over-engineering? | No tenant admin UI in Prototype; config via env/JSON |
| Scale to 10–30 offices? | Config-driven branding + API keys; verify WeChat white-label limits |

**Risk:** WeChat may not allow per-broker branding in one mini program without separate registrations — **open question for official validation**.

---

## 15. Data and Evidence Model

### Existing artifacts (reuse)

| Artifact | Location | Functions |
|----------|----------|-----------|
| Case | `service_records` / `get_case_for_read()` | Source of truth |
| Task state | `extra.h5_intake_state` | `update_case_h5_intake_state()` |
| Known facts | `extra.known_facts` | `patch_case_known_facts()` |
| Timeline | `extra.claim_timeline` | `append_claim_timeline_event()` |
| Attachments | case attachments array + GCS | `ingest_h5_slot_upload()` |
| Provenance | `known_fact_provenance` | WeCom supplements vs H5 confirm |
| Workflow | `claim_phase`, `guided_workflow_state` | `update_claim_workflow_state()` |
| Submission | `submit_intent_ids` in h5_intake_state | idempotency |

### Staging

**Prototype:** No per-field staging UI. All MP input → draft `known_facts` via PATCH. Customer confirms once at Final Review. Submit creates `customer_submitted_intake` timeline event.

**Post-submit:** Ordinary photos/notes append without new review cycle. Material fact changes trigger new review (future).

### Schema migration

**No** for Prototype. Existing JSON fields sufficient per `p19h3h_master_design_summary` and `case_store.py` patterns.

### Avoid

Per-message customer「采纳」for every WeChat text. Chat supplements auto-append with provenance label.

---

## 16. AI Workflow Contract

### AI may

| Capability | Input | Output | Customer visible? | Confirm? | Fallback | Audit |
|------------|-------|--------|-------------------|----------|----------|-------|
| Speech-to-text | audio file | transcript draft | Yes (editable) | Yes | Manual typing | timeline event |
| Fact extraction | free text | `known_facts` draft | No (shown in Review) | Yes at Review | Raw text kept | `ai_extracted_fact` |
| Categorization | photo | slot suggestion | Optional hint | No auto-move | Manual slot pick | attachment metadata |
| Missing detection | case | `get_claim_missing_items()` | Yes (Missing screen) | N/A | Static checklist | — |
| Summary | case | `build_claim_case_brief()` | Review subset | Submit = confirm | Deterministic brief | — |
| Duplicate hint | case history | risk flag | **Never** | N/A | Broker only | `system_risk_flag` |
| Broker brief | case | Workbench hero | Broker only | Broker confirms | — | — |

### AI may NOT

- Silent overwrite of customer-confirmed facts
- Advance `claim_phase` or H5/MP step index
- Trigger `broker_done`
- Liability / coverage decisions
- Official insurance filing

---

## 17. Media Pipeline

```text
Capture (wx.chooseMedia / recorder)
  → client size/format check
  → POST upload (multipart)
  → ingest_h5_slot_upload(claims, content, slot)
  → GCS via media_storage
  → attachment record on case
  → append_claim_timeline_event(customer_uploaded_photo)
  → optional AI classification (future)
  → thumbnail URL in response
  → idempotent retry on same hash
```

| Scenario | Handling |
|----------|----------|
| Upload interrupted | Client retry same file; hash dedup |
| Duplicate click | `h5_photo:{case_id}:{slot}:{sha256}` |
| Slow network | Loading state; min 300ms spinner (from smooth UX doc) |
| Large file | Reject client-side; video out of Prototype |
| WeCom photo | `ingest_wecom_media_message` — parallel path, same case |

---

## 18. Non-Functional Requirements

| Area | Prototype target | Production aspiration |
|------|------------------|----------------------|
| Performance | Task Home first render < 3s on 4G | TBD — measure in pilot |
| Upload retry | 3 client retries with backoff | Same |
| Idempotency | Submit + photo dedup proven in H5 tests | Extend to MP |
| Resumability | Same case after 72h token TTL via WeCom card | Session + token refresh |
| Accessibility | Large tap targets; readable Chinese | WCAG deferred |
| i18n | Chinese primary; English copy in tenant config | Future |
| Observability | Log `mp_*` analytics events; reuse routing_observability patterns | Datadog TBD |
| Audit | Timeline on every write — existing | Same |
| Privacy | No PII in logs; token never logged | Same |
| Retention | Existing case retention policy | Same |
| Error recovery | Help screen + WeCom「进度」 | Same |
| Security | HTTPS only; token HMAC; Workbench API key | MP session + broker auth |
| Rollout | Dev tools + 1 real device | Staged % |
| Rollback | H5 fallback links in WeCom cards | Required |

---

## 19. WeCom Integration Contract

### WeCom future role

| Function | Detail |
|----------|--------|
| Task invitation | Start / Resume mini program card |
| Reminder | Missing info nudge |
| Status notification | Submitted, broker done |
| Broker communication | Free text in chat |
| Re-open task | Resume card with same case |
| Emergency supplement | Save mis-sent media; ack + MP card |

### Message types

| Type | Trigger | Copy intent | MP destination | Forbidden |
|------|---------|-------------|----------------|-----------|
| Start Task Card |「我要理赔」| 事故记录已开始 | Task Home | Full wizard in chat |
| Resume Task Card |「进度」/ supplement ack | 继续补充 | Task Home | Raw H5 URL as primary CTA |
| Missing Info Reminder | broker_needs_more (future) | 还缺 X | Missing Items page | Structured field prompts |
| Submitted Receipt | H5/MP submit | 已收到资料 | Receipt page | Imply broker_done |
| Broker Needs More | broker action | 请补充 | Guided step | — |
| Broker Done | `mark_claim_broker_done` | 已确认完成 | Status (read-only) | Auto without broker |
| Error/Help | failure | 请联系办公室 | Help page | — |

### Forbidden WeCom behaviors

- Run full wizard in chat
- Repeat all structured questions in chat
- Imply chat submission = formal submit
- Expose long naked URLs (use mini program card)
- Parallel forms (chat + MP both collecting same fields actively)

**Code today:** `channel_ux_policy.py`, `reply.py` — P19M-1 must shift primary CTA from `mint_h5_claim_intake_form_link()` to mini program path while keeping H5 as fallback URL in error paths.

---

## 20. Broker Workbench Contract

### After mini program launch, Workbench must show

| Data | Source today | Change needed |
|------|--------------|---------------|
| Task status | `derive_claim_phase()` in `ClaimCaseBriefPanel` | None — phase is channel-agnostic |
| Confirmed facts | `build_claim_case_brief()` | None |
| Unsubmitted draft | `h5_intake_state`, `submitted` flag | None |
| Photos / voice | `ClaimEvidenceChecklist` | Add voice badge if added |
| Timeline | `claim_timeline` in drawer | Update `source_channel` label: `customer_task` |
| Missing items | `get_claim_missing_items()` | None |
| Last customer activity | timeline newest event | None |
| Latest submitted version | `customer_submitted_intake` event | None |
| Broker next step | brief `next_best_question` | None |
| broker_done | `POST /api/inbox/cases/{id}/broker-done` | None |

**Prototype:** No Workbench redesign. Optional: show `source_channel: customer_task` vs `h5_task` in timeline labels.

**Risk:** Workbench may be publicly accessible without auth — see Risks.

---

## 21. Prototype Scope

### Must Have

- Single tenant (Chen config)
- One current Claim task
- Task Home with progress / received / missing
- Story text input (one step)
- Photo upload (2 slots minimum)
- Review screen
- Submit with idempotency
- Resume same task
- Basic error / expired states
- Integration plan with existing `h5_task_intake.py` backend
- Broker Workbench readback verification

### Nice to Have

- Voice recording + mock transcription
- AI categorization display
- WeCom mini program card (vs URL scheme only)
- `GET /api/customer/tasks/current`

### Explicitly Out

- Add Car lane
- Multi-event / collision UI in MP
- Video upload
- Payments
- Insurance filing
- Full auth / account system
- Multi-tenant admin
- Native broker app
- Workbench redesign
- OCR
- Carrier integration

---

## 22. Prototype Acceptance Criteria

1. Customer opens mini program and knows next action without explanation
2. All formal structured input occurs in mini program — not WeCom chat wizard
3. Resume returns to same `case_id` / task
4. Photos attach to correct Claim case (not Add Car)
5. Review shows all inputs (text + photos)
6. Submit is idempotent (double-tap safe) — same as `submit_intake_form` tests
7. Broker sees submission in Workbench queue with updated brief
8. Add Car flow not triggered by Claim supplements
9. H5 is not promoted as primary entry in WeCom cards
10. No input lost on network retry
11. One primary button per screen
12. Demonstrable on WeChat devtools or real device

---

## 23. Architecture Risks

| # | Risk | Probability | Impact | Evidence | Mitigation | Prototype test |
|---|------|-------------|--------|----------|------------|----------------|
| 1 | WeChat 主体/类目审核 blocked | Medium | Critical | No mini program registered; `p19e3` noted audit weeks | Early Gate 1 feasibility spike | Attempt dev account registration |
| 2 | Overseas entity cannot operate 小程序 | Medium | Critical | US-based founder; unverified | Legal + WeChat biz dev consult | Document blocker early |
| 3 | WeCom external_userid ↔ MP openid linking | High | High | No code for openid binding; separate ID spaces | Task token in card query for Prototype | Card open with case_id param |
| 4 | US customers cannot use 微信 | Low-Medium | High | Chen pilot is WeChat-native | Confirm pilot user base | User interview |
| 5 | Data storage / privacy (PII in China) | Medium | High | GCS + Cloud Run US | Privacy policy; minimize retention | Legal review |
| 6 | Media upload size / timeout on MP | Medium | Medium | H5 upload works; MP differs | Chunked upload future; 2 photos only | Real device test |
| 7 | Voice / ASR unavailable | High | Low | No ASR endpoint | Text-only Must Have | Mock transcript |
| 8 | Tenant branding in one MP | Medium | Medium | Single 陈总 copy hardcoded | Single tenant Prototype | — |
| 9 | H5 / MP coexistence confusion | Medium | Medium | Dual links in recent deploys | WeCom policy: MP primary, H5 fallback only | Copy review |
| 10 | Public Workbench access | High | High | `p19h3i` eval: API key not enforced on UI | Enforce broker auth before pilot | Pen test |
| 11 | User adoption — customers stay in chat | Medium | High | `p19h3j` dual-channel habit | Strong MP cards; chat ack → MP | Pilot observation |

---

## 24. Open Questions

### Founder decision

| # | Question |
|---|----------|
| F1 | Approve MP as sole customer task app — confirm retirement of H5-primary WeCom CTAs |
| F2 | Prototype tenant: Chen only — confirm |
| F3 | Voice: Must Have or defer to post-Prototype? |

### WeChat official validation

| # | Question |
|---|----------|
| W1 | Can Enterprise WeChat send mini program cards to external contacts for this use case? |
| W2 | Required 类目 for accident资料收集 mini program? |
| W3 | US entity + US users — allowed? |
| W4 | `openid` binding path from WeCom KF session? |

### Technical spike

| # | Question |
|---|----------|
| T1 | Facade router vs direct H5 endpoint reuse in Prototype? |
| T2 | Mini program native vs lightweight framework? (Founder: no Taro/React/Vue in prompt — use WeChat native) |

### Pilot user test

| # | Question |
|---|----------|
| P1 | Do Chen's customers prefer MP over H5 in-app browser? |

### Legal / privacy

| # | Question |
|---|----------|
| L1 | Accident photos + narrative — cross-border storage disclosure needed? |

---

## 25. Decision Log

| # | Decision | Date |
|---|----------|------|
| D1 | Mini Program replaces H5 as **target** customer frontend | 2026-07-10 |
| D2 | H5 retained as fallback / QA / reference | 2026-07-10 |
| D3 | WeCom no longer primary structured data entry | 2026-07-10 |
| D4 | One task / one next action / one submit | 2026-07-10 |
| D5 | Existing backend reused (`claim_state`, `case_store`, `h5_task_intake`) | 2026-07-10 |
| D6 | Prototype single Claim loop only | 2026-07-10 |
| D7 | Single codebase multi-tenant direction | 2026-07-10 |
| D8 | No schema migration during architecture phase | 2026-07-10 |
| D9 | No implementation before SSOT approval | 2026-07-10 |

---

## 26. Implementation Gates

| Gate | Criterion | Status |
|------|-----------|--------|
| **Gate 0** | SSOT approved by Founder | **BLOCKED** |
| Gate 1 | WeChat registration / category feasibility | Not started |
| Gate 2 | Mini program dev shell runs | Not started |
| Gate 3 | Identity / task invitation works | Not started |
| Gate 4 | Text + photo loop works | Not started |
| Gate 5 | Review + Submit works | Not started |
| Gate 6 | Broker readback works | Not started |
| Gate 7 | Pilot safety / auth | Not started |
| Gate 8 | Human usability test | Not started |

**No Gate 0 approval → no P19M-1 code.**

---

## 27. Recommended Next Prompt

**Title:** `P19M-1 — Unified Claim Mini Program Prototype Foundation`

**Scope (10–15 items):**

1. Create WeChat mini program dev project (native WXML/WXSS/JS — no Taro/UniApp)
2. Single tenant config (Chen office name, disclaimer from `CLAIM_INTAKE_SAFETY_COPY`)
3. Task Entry page — accept `task_token` query from WeCom card
4. Task Home — consume `dashboard_summary` from intake API
5. Story step — PATCH `accident_description`
6. Photo step — reuse `POST /api/h5/tasks/{token}/upload` (2 slots)
7. Review + Submit — reuse submit endpoint with `submit_intent_id`
8. Receipt + Resume states
9. Error / expired token screen with WeCom recovery copy
10. Optional: `routes/customer_task.py` facade aliases (no business logic move)
11. WeCom Start Card → mini program path (keep H5 URL as fallback in Help only)
12. Smoke script: MP API loop against local/QA backend
13. Verify Workbench shows `customer_submitted_intake` after submit
14. Do NOT implement Add Car, video, multi-tenant admin, Workbench redesign
15. STOP after Prototype acceptance criteria §22 — no production deploy without Founder review

---

*P19M-0 complete — awaiting Founder SSOT approval. No implementation authorized.*
