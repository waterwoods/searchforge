# P19H-3h — Claim H5 Task State Machine

**Date:** 2026-07-10  
**Sprint:** P19H-3h Design  
**Lane:** Claim (`service_lane: claim`)  
**Flow token:** `FLOW_CLAIM_INTAKE_FORM` (new)  
**Route:** `/task/claim/:taskToken`  
**Pattern:** Spark Driver「trip」— one stage, one primary action (production-grade task workflow, not standalone app)

---

## Overview

The **Claim Intake Trip** is a linear 9-step wizard inside H5. The state machine (`derive_claim_phase`) remains backend-authoritative; H5 reflects it but does not invent phases.

```text
Start → Injury → Time+Location → Story → Vehicle/Other → Evidence → Review → Submit → Done
```

**Design principles:**

- **Production-grade workflow product, not AI demo** — shippable, sellable, time-saving; main flow = H5 + state machine; AI assist only; idempotent + evidence-backed; broker confirms `broker_done` (see architecture doc §Production-grade)
- **Structured Task First, AI Assist Second** — state machine controls flow; H5 is structured execution; AI is draft/assist only (see architecture doc §Core principle)
- **Append-first, Split-later** — ordinary WeCom/H5 supplements append to current Claim; split/merge/archive is backend/broker (see architecture doc §Append-first)
- One primary button per screen
- Button disables + spinner on action
- Back navigation allowed (except after final submit)
- Token resume (72h TTL recommended for multi-day accidents)
- All writes → `known_facts` + `claim_timeline` with `source_channel: "h5_task"`
- Chat supplements merge into same case (safety net); H5 is primary

### Input authority (Claim H5 MVP — non-negotiable)

| Priority | Source | Treatment |
|----------|--------|-----------|
| 1 | H5 buttons / fields / upload / submit | **Authoritative** — drives phase and `missing_info` |
| 2 | H5 confirmed facts (`PATCH` + timeline `h5_task`) | **Confirmed** — shown in Review and Workbench |
| 3 | WeCom free text / photos | **Supplemental / provisional** — merge to case; may pre-fill H5; never skip wizard steps |
| 4 | AI extraction from chat | **Draft only** — Workbench hint; broker confirms |

**Append-first rule:** Passive accident narrative, photos, and supplements **append** to the active Claim timeline without customer collision prompts. H5 continue link offered on Status / missing / append when intake is continuable. Only strong explicit new-accident language triggers rare WeCom confirm.

**Implementation guardrails for tomorrow:**

- Do **not** advance H5 steps based on WeCom/AI extraction alone
- Do **not** let LLM decide phase or replace `derive_claim_phase`
- Do **not** build WeCom msgmenu as primary field collection for new Claims
- WeCom injury quick-reply: legacy only; new cases → H5 Step 2
- Workbench brief may show AI-suggested fields; **broker_done** remains manual Chen trust anchor
- Every step write → `claim_timeline` with `source_channel: h5_task` (production evidence chain)
- Production changes require test + smoke + rollback consideration before deploy

**Spark Driver takeaway:** One trip, one primary action, clear completion — because **task cards and state machines** make production workflows trustworthy. AI chat does not. Production standards > demo effects.

---

## Step 0 — Entry (WeCom, not H5)

| Attribute | Value |
|-----------|-------|
| **Trigger** | Customer sends `我要理赔` |
| **WeCom output** | Framed Start Card `【事故记录已开始 ✅】` |
| **Primary CTA** | `打开资料填写页面` → signed H5 link |
| **Secondary** |「您也可以继续在微信发文字或照片」|
| **Disclaimer** | 不代表已向保险公司正式报案 |

**Injury quick-reply menu:** Deprecate as primary for new Claims (Option A from recon). Injury becomes H5 Step 1. Keep WeCom injury handler for legacy cases only.

**Backend on Start:**

- Create Claim case (`claim_started`)
- Mint `h5t1` token (`FLOW_CLAIM_INTAKE_FORM`, `case_id`, `lane: claim`)
- Append timeline: `claim_started` (source: `wecom`)
- Do NOT send duplicate Start Card (reply dedup)

---

## Step 1 — Start (H5 landing)

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Orient customer; show trip name and progress shell |
| **Header** | `事故资料收集` |
| **Subcopy** | 我是陈总办公室的值班助手。请按步骤填写，陈总会人工确认。 |
| **Progress** | `0/8 已完成` (or from `missing_info` count) |
| **Fields** | None (welcome only) |
| **Validation** | — |
| **Primary button** | `开始填写` → Step 2 |
| **Error state** | Token expired →「链接已过期，请在微信回复『进度』获取新链接」|
| **Saved state** | Read `GET /api/h5/tasks/{token}/intake` for existing progress; skip to first incomplete step if resuming |
| **known_facts** | — |
| **claim_case_brief** | `phase`, `missing_info` count |
| **Broker impact** | Case visible in Workbench once Start ceremony complete |

---

## Step 2 — Injury

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Capture injury status — safety-critical first question |
| **Fields** | `anyone_injured`: radio `没有受伤` / `有人受伤` / `不确定` |
| **Values** | `no` / `yes` / `unknown` (maps to existing `is_injury_yes()` helpers) |
| **Validation** | Required — cannot proceed without selection |
| **Primary button** | `下一步` |
| **Error state** | API fail →「保存失败，请重试」+ retry; no silent skip |
| **Saved state** | PATCH persists immediately; back nav shows prior selection |
| **known_facts** | `anyone_injured` |
| **claim_case_brief.key_facts** | `anyone_injured` → display label「是否有人受伤」|
| **Timeline** | `customer_submitted_field` / `h5_step_complete` step=`injury` |
| **Broker impact** | Brief highlight if `yes` — urgent follow-up flag |

**Special UX:** If `yes`, show inline alert:「如有人受伤且情况紧急，请先拨打 911，再继续填写。」

---

## Step 3 — Accident Time + Location

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Anchor the accident in time and place |
| **Fields** | `accident_datetime` (date + time picker or structured text); `accident_location` (text, placeholder: 城市 / 路口 / 停车场) |
| **Validation** | Both required. Datetime: parseable, not future. Location: min 3 chars |
| **Primary button** | `下一步` |
| **Error state** | Invalid datetime →「请填写有效的事故时间」; empty location → inline field error |
| **Saved state** | Partial save allowed per field on blur or step advance |
| **known_facts** | `accident_datetime`, `accident_location` |
| **claim_case_brief** | Both appear in key_facts; drive Status Card「事故时间·地点」section |
| **Timeline** | `h5_step_complete` step=`time_location` |
| **Broker impact** | Core brief fields; missing blocks `accident_basics_complete` |

**Note:** Reuse `date_normalization.py` for chat/H5 consistency.

---

## Step 4 — Accident Story

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Capture narrative — what happened |
| **Fields** | `accident_description` (textarea) |
| **Placeholder** | 例如：我停在红灯前，后车追尾撞上。请尽量写清楚谁先动、怎么撞的。 |
| **Validation** | Required; min 10 chars; max 500 (`CLAIM_MAX_DESCRIPTION_LENGTH`) |
| **Primary button** | `下一步` |
| **Error state** | Too short →「请再补充一些细节」; too long → char counter + block |
| **Saved state** | Auto-save draft in localStorage + server PATCH on next |
| **known_facts** | `accident_description` |
| **claim_case_brief** | Summary hero text source |
| **Timeline** | `h5_step_complete` step=`story` |
| **Broker impact** | Primary narrative for Chen review; no LLM rewrite needed |

---

## Step 5 — Vehicle / Other Party

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Own vehicle + other party identifiers |
| **Fields** | `own_vehicle_info` (text: year/make/model or description); `other_party_plate` (optional text); `other_party_info` (composite: insurer, contact, vehicle — free text or sub-fields) |
| **Validation** | `own_vehicle_info` required (min 2 chars). Other party: at least one of plate / insurer / description recommended — soft warning if empty, allow proceed with confirmation |
| **Primary button** | `下一步` |
| **Error state** | Missing own vehicle → block; soft-missing other party → modal「对方信息暂时没填，可以稍后在照片步骤补充」|
| **Saved state** | Per-field PATCH |
| **known_facts** | `own_vehicle_info`, `other_party_plate`, `other_party_info` (and sub-keys if split: `other_party_phone`, `other_party_name`) |
| **claim_case_brief** | `other_party_info`, vehicle line in key_facts |
| **Timeline** | `h5_step_complete` step=`vehicle_other_party` |
| **Broker impact** | Drives `other_party_in_progress` → `other_party_complete` phases |

**Mapping note:** Align with `OTHER_PARTY_INFO_SIGNALS` in `claim_state.py` for completeness checks.

---

## Step 6 — Evidence (photos)

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Collect photo evidence via existing slot flow |
| **Fields** | 3 slots (reuse `claim_evidence_pack`): `customer_damage_photo`, `other_party_vehicle_photo`, `scene_photo` |
| **Validation** | `customer_damage_photo` required; `other_party_vehicle_photo` soft-required; `scene_photo` optional. Skip allowed per slot (existing `/skip` API) |
| **Primary button** | `下一步` (enabled when required slot received or skipped) |
| **Error state** | Upload fail → slot-level retry; GCS error →「上传失败，请检查网络后重试」|
| **Saved state** | Slot status from `GET /api/h5/tasks/{token}` (existing upload API) |
| **known_facts** | Attachment metadata on case; slot status in `claim_evidence` state |
| **claim_case_brief** | `evidence_received` count; `ClaimEvidenceChecklist` panel |
| **Timeline** | `customer_uploaded_photo` per slot (source: `h5_task`) |
| **Broker impact** | Evidence checklist drives review readiness |

**Implementation:** Reuse `POST /api/h5/tasks/{token}/upload` and `/skip`. May embed upload UI inline or deep-link to `/task/upload/:token` for slot — prefer **inline** for Spark continuity.

---

## Step 7 — Review

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Customer confirms what was received; edit gaps before handoff |
| **Display** | Sections: 已填写 / 还缺 / 已上传照片 |
| **Fields** | Read-only summary with「修改」links back to steps 2–6 |
| **Validation** | All hard-required fields present (derive from `missing_info`) |
| **Primary button** | `提交给陈总确认` (only if review-ready) |
| **Secondary** | Per-section edit links |
| **Error state** | Missing required → highlight sections in red; button disabled with tooltip「请先补全标红项目」|
| **Saved state** | Live read from `GET /api/h5/tasks/{token}/intake` |
| **known_facts** | Read-only aggregation |
| **claim_case_brief** | Mirror of Workbench brief (customer-safe subset) |
| **Timeline** | — (no write until submit) |
| **Broker impact** | Reduces broker back-and-forth on obvious gaps |

---

## Step 8 — Submit to Broker

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Atomic handoff — customer knows submission worked |
| **Action** | `POST /api/h5/tasks/{token}/submit` |
| **Validation** | Server re-checks `missing_info`; phase guard (not already `broker_review` / `broker_done`) |
| **Primary button** | Same as Step 7 — becomes submit trigger |
| **UX on click** | Button `disabled` immediately; spinner「提交中…」; idempotency key in header |
| **Error state** | Network fail →「提交失败，请重试」+ enabled retry; 409 already submitted → redirect to Step 9 |
| **Saved state** | `claim_phase` → `intake_ready_for_broker` or `broker_review`; `guided_workflow_state` updated |
| **known_facts** | Final snapshot frozen for broker |
| **Timeline** | `customer_submitted_intake` (source: `h5_task`) |
| **Broker impact** | Case surfaces in Office Review Queue with `Broker Review pending` |
| **WeCom notify (P1)** | Optional:「已收到您提交的事故资料。陈总会人工确认。」+ H5 resume link |

**Idempotency:** Same `submit` key → 200 with existing state, no duplicate timeline event.

---

## Step 9 — Done / Confirmation

| Attribute | Value |
|-----------|-------|
| **Screen goal** | Closure + clear next steps (not carrier filing) |
| **Display** | `已提交给陈总` ✅ |
| **Sections** | **已收到** (summary) · **还缺** (if any soft gaps) · **下一步** (陈总人工确认后会联系您) |
| **Fields** | None |
| **Primary button** | `返回微信` or `补充资料` (re-opens H5 at Review if gaps remain) |
| **Error state** | N/A (terminal for this submit) |
| **Saved state** | Read-only; token may allow edit until `broker_done` |
| **known_facts** | — |
| **claim_case_brief** | Customer sees simplified status; broker sees full brief |
| **Timeline** | — |
| **Broker impact** | Chen reviews → Broker Done → WeCom End Card |

**Disclaimer footer (every H5 page):** 此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。

---

## H5 ↔ WeCom ↔ Workbench sync

| Event | H5 shows | Status Card shows | Workbench shows |
|-------|----------|-------------------|-----------------|
| Step 2 complete | 1/8 已完成 | 还缺 updates on next `进度` | key_facts partial |
| Step 8 submit | Done screen | 已提交 / broker_review | Broker Review queue |
| Broker Done | (token read-only or expired) | End Card via WeCom | 已确认 / 已交接 |

Status Card must append: `继续补充资料：{H5_LINK}` — same token or re-mint if expired.

---

## Phase mapping (backend, unchanged)

```text
Steps 2–5 complete → accident_basics_complete
Step 6 required slots → photos_complete (or photos_in_progress)
Step 8 submit → intake_ready_for_broker → broker_review
Broker Done → broker_done
```

H5 step index is a **customer UX construct**; backend continues using `derive_claim_phase()`.

---

## Exception paths (not in H5 wizard)

| Scenario | Handler | H5 behavior |
|----------|---------|-------------|
| New accident while open Claim | Collision Resolver (WeCom) | Current H5 token stays bound to prior case; new Start mints new token |
| Multi-open ordinary supplement | Append to newest (P19H-3f-5) | H5 resume link for active case |
| Customer uses chat only | `claim_basics.py` append | Status Card re-links H5 |
| Lane switch Add Car → Claim | Confirm Card | H5 Add Car token invalidated on Claim start |

---

## APIs (new, P0)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/h5/tasks/{token}/intake` | Phase, steps, `key_facts`, `missing_info`, safety copy |
| `PATCH /api/h5/tasks/{token}/fields` | Save one step's fields |
| `POST /api/h5/tasks/{token}/submit` | Final customer handoff |

Reuse existing: `GET /api/h5/tasks/{token}`, `POST .../upload`, `POST .../skip`.

---

## Test matrix (design-level)

| Test | Expected |
|------|----------|
| Full 9-step happy path | Brief complete; broker_review phase |
| Resume after 24h | Token valid; lands on first incomplete step |
| Submit twice | Second returns 200 idempotent; one timeline event |
| Chat + H5 dual write | Same `known_facts`; H5 value wins on conflict for same key (Structured Task First) |
| WeCom text only, no H5 | Case exists; Status Card re-links H5; chat facts provisional until H5 confirm |
| AI extracts field from chat | Draft in Workbench; does not auto-complete H5 step |
| Injury yes | Brief highlight + WeCom urgent copy on Status Card |
| Skip optional photo | Phase advances; missing noted in Review |

---

*Field names align with `claim_state.py` (`anyone_injured`, not `injury_status`).*
