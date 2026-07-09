# P19H-3e-R1 — Claim Story Recorder Best Practice Recon

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Best practice recon / P19H-3e-1 scope definition — **no production code, no deploy, no schema migration**  
**Prerequisite:** P19H-3e category strategy recon · P19H-3d WeCom image binding deployed · P19H-3c-3 Evidence Checklist · P19H-3c-R3 Identity Resolver  
**Related:** `p19h3e_claim_case_builder_category_strategy_recon.md` · `p19h3d_r1_claim_human_simulation_workflow_simplification_recon.md` · `p19h3d_r0_claim_photo_intake_ux_simplicity_recon.md` · `p19h3c_r4_claim_workflow_business_value_alignment_recon.md` · `p19h3c_r1_claim_multichannel_intake_best_practice_recon.md` · `p19h3c_r2_claim_identity_resolution_duplicate_prevention_recon.md` · `evidence/p19h3d_wecom_claim_image_binding_mvp_2026_07_09.md` · `evidence/p19h3c3a_claim_evidence_summary_backend_2026_07_09.md` · `evidence/p19h3c3b_claim_evidence_checklist_ui_2026_07_09.md`

---

## 1. Executive Summary

P19H-3e established the product category: **Claim Story Recorder + Case Builder** — not a photo upload tool, not FNOL filing, not damage AI. This recon answers *how* to build that wedge using industry best practice, and defines **P19H-3e-1** as the next coding sprint.

| Question | Answer |
|----------|--------|
| What category are we? | **WeChat-native Claim Story Recorder + Case Builder** (GTM: Broker Claim Service Copilot) |
| Chen's real pain? | **Cannot reconstruct the accident story** without scrolling WeChat and relying on memory |
| Customer's real job? | **Talk normally in WeChat** — text, photos, voice — not complete a form |
| Data backbone? | **`claim_timeline[]` + `claim_case_brief`** on existing `case_id` JSONB |
| Chen sees first? | **Claim Case Brief** — who, what, when, where, injury?, evidence, gaps, next question |
| Next sprint? | **P19H-3e-1 Claim Story Timeline + Case Brief Foundation** |
| H5 role? | **Optional 补充资料** — not primary, not hero CTA |
| Broker Manual Slot Assignment? | **Deferred** — adds clerical work; brief delivers more value |
| Verdict | **GO** on P19H-3e-1 · **HOLD** on slot assignment, OCR, ASR, LLM extraction · **STOP** — no code in this recon |

**One-line thesis:**

> 微信里的理赔故事记录器 — 客户照常发微信，AI 帮陈总抄下来、整理好，输出 Claim Case Brief；陈总打开 Workbench 先看故事和缺口，不先看 checklist。

---

## 2. Best Practice Principles

### Category definition

**WeChat-native Claim Story Recorder + Case Builder** — a broker-office accident scribe that captures omnichannel intake into one claim file and produces a broker-ready brief. Not an adjuster system. Not a filing bot.

### 2.1 What good FNOL / digital intake systems do well

| Pattern | What carriers/innovators do | Our borrow |
|---------|---------------------------|------------|
| **Capture first, adjudicate later** | FNOL digitizes first-hand loss info; reduces transcription errors; speeds downstream handling | ✅ Record every message/photo before asking「够不够赔」 |
| **Safety gate** | Injury check before details | ✅ Already shipped (`manual_handle`) |
| **Progressive disclosure** | 15–20 fields eventually, but not all at once | ✅ Basics (3 fields) → story events → one gap question |
| **Reflexive / guided questions** | Auto-follow-up when key fact missing («Where did this happen?») | ✅ **One** next best question only |
| **Channel-agnostic record** | Phone, app, web, chat → same claim file | ✅ One `case_id`, many `source_channel` values |
| **Idempotency** | `sourceMessageId` prevents duplicate FNOL creates | ✅ `wecom_msg_id` dedup (shipped) |

**Reject from FNOL:** coverage verification, fault determination, straight-through processing, carrier routing,「已报案」language.

### 2.2 What unified claim file / single claim view systems do well

Snapsheet, Guidewire ClaimCenter, and modern intake platforms emphasize: **documents, communications, notes, and actions captured/logged/searchable in a single file.**

| Capability | Industry pattern | Our MVP equivalent |
|------------|------------------|-------------------|
| Single claim view | One screen: loss details + comms + docs + tasks | **Claim Case Brief** hero panel |
| Communication log | Every SMS/email/chat logged chronologically | **`claim_timeline[]`** |
| Document index | All attachments linked to claim, not scattered | **`case_attachments[]`** (shipped) + timeline refs |
| Activity search | Find「when did customer mention police» | Timeline text search (defer UI; structure now) |
| Notes vs system events | Broker notes distinguished from customer messages | `actor: broker` vs `actor: customer` |

**Key insight:** Chen's「翻微信」pain is exactly what unified claim files solve — he needs **one scrollable story**, not three disconnected surfaces (WeChat, H5, checklist).

### 2.3 What we should borrow

| # | Borrow | Implementation |
|---|--------|----------------|
| 1 | **Unified claim file** | All channels → `claim_timeline[]` on one `case_id` |
| 2 | **Capture before organize** | Append event immediately; brief recomputed async/sync |
| 3 | **Guided but not form-heavy** | Basics once; then story mode; one gap question |
| 4 | **Human-in-the-loop** | AI records; Chen decides; never「已判定」 |
| 5 | **Simple customer entry** |「照常说事故」— WeChat-native |
| 6 | **Walmart Spark Driver task UX** | One simple next action for customer; hide backend complexity |
| 7 | **Idempotent intake** | `msg_id` / `attachment_id` dedup on timeline |
| 8 | **Broker next action** | Computed from brief, not slot checklist alone |

### 2.4 What we should avoid

| Avoid | Why |
|-------|-----|
| Photo slot taxonomy as hero UX | Chen needs story, not clerical classification |
| H5 as primary mental model | Customers live in WeChat under stress |
| 20-field intake wizard | Abandonment; feels like bureaucracy after crash |
| AI damage estimate / OCR / ASR as MVP gates | Wrong category; liability + scope creep |
| Fault / coverage /「已报案」language | Broker judgment; compliance risk |
| Broker Manual Slot Assignment before brief | Optimizes checklist, not story understanding |
| Equal-weight CTAs (H5 = WeChat = 联系陈总) |「三个系统」confusion (P19H-3d-R1) |
| Auto slot classification | Wrong slot worse than unassigned |

### 2.5 Walmart Spark Driver style simplicity

Spark Driver hides dispatch complexity behind **one task at a time** on mobile:

| Spark pattern | Claim Story Recorder equivalent |
|---------------|--------------------------------|
| One active delivery task | One active claim case per accident |
| Simple CTA: «Navigate» / «Confirm pickup» | Simple CTA for customer: «继续说事故»/ send photo — no menu |
| Status visible without opening 5 screens | Chen: Brief answers 7 questions in 10 seconds |
| Backend routing invisible | Identity resolver, slot status, phase — all behind brief |
| Progressive task unlock | Basics → story capture → optional H5 supplement |

**Rule:** Customer never sees「方式一/二/三」. Chen never sees「待分类」before he sees「发生了什么」.

### 2.6 How to avoid making Chen do clerical work

| Clerical task | System should instead |
|---------------|----------------------|
| Scroll WeChat to reconstruct story | **Timeline + Brief summary** |
| Classify photos into 3 slots | Show thumbnails grouped; slots optional/collapsed |
| Re-type what customer said on phone | Phone summary → timeline (P19H-3c-R5, after 3e-1) |
| Re-ask for photos already sent | Ack + evidence count in brief |
| Merge duplicate cases manually | Identity resolver (shipped) + brief shows conflict |
| Drag-drop slot assignment | **Defer** — not MVP wedge |

### 2.7 Human-in-the-loop without slowing the customer

| Actor | Speed | Responsibility |
|-------|-------|----------------|
| **Customer** | Immediate ack (<3s) | Send naturally; no wait for Chen |
| **AI** | Record first (<1s persist); organize second (<5s brief refresh) | Scribe, one gap question, warm copy |
| **Chen** | Async — opens when ready | Read brief, call back, decide filing |

**Invariant:** Customer never waits for Chen to「approve» a message. Every inbound is recorded instantly. Chen's review is **downstream**, not a gate on intake.

---

## 3. Customer UX

### 3.1 Target feeling

```text
我只要在微信里把事故说清楚、把照片发过来就行。
系统会帮陈总记录。
陈总会人工确认。
```

### 3.2 First reply after「我要理赔」

```text
您好，我是陈总办公室的值班助手。

请先确认：您和车上的人现在都安全吗？有没有受伤需要叫救护车？

如果安全，请用一条消息告诉我：
· 大概什么时候、在哪里
· 发生了什么事

我会先帮您记录下来，陈总会人工确认后联系您。
这不代表已经向保险公司正式报案。
```

**Rules:** Safety first · Chen named ·「记录」not「受理」· No H5 button on first message.

### 3.3 How AI asks for missing info

**One question only.** Pick highest-priority gap from brief engine:

| Priority | Gap | Question |
|----------|-----|----------|
| P0 | Injury unknown after basics | 「请问有人受伤吗？」 |
| P1 | No time | 「请问事故大概是什么时候？」 |
| P1 | No location | 「请问事故在哪里发生的？」 |
| P2 | No description detail | 「能再简单说一下怎么发生的吗？」 |
| P3 | No photos at all (after 30+ min) | 「如果方便，可以发几张现场或车损照片，我帮您一起记录。」 |

**Never:** bullet list of 5 missing items · re-ask field already in `known_facts` · slot jargon（「请上传对方车辆 slot」）.

### 3.4 How AI acknowledges photos

**Tier A (bound to active claim):**

```text
收到照片，已记到这份事故记录里 ✅
陈总会整理确认，不用重复发同一张。
您也可以继续用文字补充说明。
```

**Tier C (no open claim, photo-first):**

```text
照片已收到 ✅
如果这是理赔相关，请回复「我要理赔」，我帮您建立记录。
```

**Never after WeChat photos on case:**「或点下面按钮分步上传」.

### 3.5 How AI handles voice messages

**No ASR in 3e-1.** Stub only:

```text
语音已收到，我先帮您记下。
陈总会听完后再联系您确认。
您也可以打字简单说一下时间和地点。
```

Timeline event: `event_type: customer_voice_stub`, `attachment_id` if media stored, `transcript: null`.

### 3.6 How AI avoids making customer repeat

| Rule | Behavior |
|------|----------|
| Dedup `msg_id` | Same WeChat message → same timeline event, same ack |
| Basics partial merge | Extract what's present; ask only missing field |
| Photo receipt | Never re-request slot already `received` in H5 |
| Phone + WeChat | When phone summary ships, brief shows merged story (3e-2+) |
| Multi-message story | All texts append to timeline; brief synthesizes |

### 3.7 When H5 appears, if ever

| Context | H5? |
|---------|-----|
| First claim start | **No** — story mode first |
| After basics complete, calm customer | **Optional secondary** —「如果想分步补充照片，可以点下面」 |
| Customer already sent WeChat photos | **Suppress** — no H5 nag |
| At accident scene, stressed | **Never push** — WeChat only |
| Chen sends link from Workbench | **Yes** — broker-initiated, one slot (future) |
| Injury / manual_handle | **No** |

**H5 button label (when shown):** `补充事故资料` — not `上传事故照片` as hero.

---

## 4. Chen UX

### 4.1 Target feeling

```text
我不用翻微信，不用靠脑子记。
我一打开就看到这起事故的故事、证据和缺口。
```

### 4.2 Workbench first screen (Claim drawer)

```text
┌─────────────────────────────────────────────────────────┐
│ ⚠️  [仅当 injury / manual_handle / contact_requested]      │
├─────────────────────────────────────────────────────────┤
│ 📋 事故摘要 · Claim Case Brief                    [刷新] │
│   李女士 · 昨晚 Costco 停车场被追尾，后保险杠受损…        │
│   受伤：未知 · 警方：未知 · 照片：3 张微信                │
├─────────────────────────────────────────────────────────┤
│ ❓ 还缺什么                                              │
│   · 对方车牌 / 保险信息                                  │
│   · 是否有人受伤                                         │
├─────────────────────────────────────────────────────────┤
│ 💬 建议问客户                                            │
│   「请问对方车牌号是多少？如果没看到可以说一下。」          │
├─────────────────────────────────────────────────────────┤
│ 🕐 事故时间线                              [展开全部]    │
│   19:02 客户 · 我要理赔                                  │
│   19:03 客户 · 昨晚7点 Costco 停车场 被追尾               │
│   19:05 客户 · 📷 照片 ×3                               │
├─────────────────────────────────────────────────────────┤
│ 📷 已收资料                                    3 张      │
│   [thumb] [thumb] [thumb]  微信 · 未分类                 │
├─────────────────────────────────────────────────────────┤
│ ▶ 照片清单（H5 分步状态）                    [折叠]      │
│   ✅ 自己车损 · ○ 对方车辆 · ○ 现场                      │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Claim Case Brief order (above the fold)

Within the Brief hero panel, top-to-bottom:

1. **Narrative summary** (2–4 sentences, Chinese)
2. **Key facts row** — 时间 · 地点 · 受伤 · 警方 · 照片数
3. **Customer identity** — name + WeCom source
4. **Confidence badge** — 低/中/高 (how complete the story is)
5. **Last updated** — `brief_updated_at`

### 4.4 What Chen knows in 10 seconds

| # | Question | Brief field |
|---|----------|-------------|
| 1 | Who? | `customer.display_name` |
| 2 | What happened? | `summary` |
| 3 | When / where? | `key_facts.accident_datetime` / `accident_location` |
| 4 | Injury? | `key_facts.injury_status` |
| 5 | Evidence? | `evidence_received` |
| 6 | Missing? | `missing_info[]` |
| 7 | What to ask next? | `next_best_question` |

### 4.5 Timeline appearance

- Chronological, oldest-first (story reads naturally)
- Icon per event type: 💬 text · 📷 photo · 🎤 voice · ✅ basics · 📞 phone (future)
- Expandable text for long messages; truncate in list, full in expand
- Link `attachment_id` → thumbnail in photos section
- Max 50 events (ring buffer); oldest dropped with audit log (defer)

### 4.6 Photos appearance

- Thumbnail grid — **all** claim attachments, not slot-grouped
- Badge: `微信` / `H5` / `陈总上传`
- **No slot assignment required** to view
- Caption: filename + `received_at`
-「未分类」badge OK — not a blocker for Chen's review

### 4.7 Missing info appearance

- 3–5 bullets max
- Chinese labels: `对方车牌`, `受伤情况`, `事故时间`, etc.
- `severity: critical | important | optional`
- Never slot keys exposed: use「对方车辆照片」not `other_party_vehicle_photo`

### 4.8 Next best question

- Single string, ready to copy or read on phone
- Framed as suggestion: 「建议问客户：…」
- Chen may ignore — not auto-sent to customer in 3e-1

### 4.9 What Chen does next

```text
1. Read Brief (10 sec)
2. Scan photos (10 sec)
3. Call / WeChat customer with next_best_question
4. Optionally expand checklist if filing needs slot clarity
5. File with carrier (outside CaseIQ)
```

---

## 5. System / AI Behavior Rules

### 5.1 Core rules

| # | Rule |
|---|------|
| R1 | **Record first** — every inbound creates timeline event before any analysis |
| R2 | **Organize second** — recompute `claim_case_brief` after timeline/facts change |
| R3 | **One next best question** — max one proactive ask per customer turn |
| R4 | **Never judge liability / coverage** — no fault, no「能赔」 |
| R5 | **Never claim filed** — no「已报案」「正式受理」 |
| R6 | **Never over-ask** — if basics complete + photos received, stay quiet unless critical gap |
| R7 | **Update brief on every new event** — monotonic `brief_updated_at` |
| R8 | **WeChat-first** — timeline event for every text + image, not just attachments |
| R9 | **Idempotent** — duplicate `msg_id` / `attachment_id` → no duplicate timeline event |
| R10 | **Human decides** — brief is prep; `broker_confirmed_at` remains Chen's gate |
| R11 | **AI is scribe, not adjuster** — copy uses「记录」「整理」「陈总会确认」 |
| R12 | **Injury → manual** — block photo nag; escalate to Chen |

### 5.2 Brief recomputation trigger

Recompute `claim_case_brief` when:

- New timeline event appended
- `known_facts` updated (basics extraction)
- New `case_attachment` added
- `claim_attachment_slots` changed (H5 skip/receive)

### 5.3 Forbidden phrases (extend existing guardrails)

`CLAIM_FORBIDDEN_AUTOMATION_CLAIMS` plus: `一定会赔`, `责任在`, `全责`, `对方有责`, `保险公司已收到`.

---

## 6. P19H-3e-1 Scope

**Sprint name:** P19H-3e-1 Claim Story Timeline + Case Brief Foundation

### Scope matrix

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | `claim_timeline[]` on case JSONB | **include in 3e-1** | Core data backbone |
| 2 | Text message timeline events | **include in 3e-1** | Hook `claim_basics.py` + `append_follow_up_message` path |
| 3 | Image/media timeline events | **include in 3e-1** | Hook `media_intake.py` after bind |
| 4 | `basics_complete` timeline event | **include in 3e-1** | When `is_accident_basics_complete()` flips true |
| 5 | Minimal voice stub event | **include in 3e-1** | `customer_voice_stub`; no ASR |
| 6 | `build_claim_case_brief()` | **include in 3e-1** | New function in `claim_workbench_display.py` |
| 7 | Deterministic summary from basics + snippets | **include in 3e-1** | Template/string join; no LLM required for ship |
| 8 | `key_facts` object | **include in 3e-1** | From `known_facts` + attachment counts |
| 9 | `missing_info` object | **include in 3e-1** | Rule-based from fact template |
| 10 | `next_best_question` | **include in 3e-1** | Single question; priority rules |
| 11 | Workbench Case Brief hero panel | **include in 3e-1** | New React component above checklist |
| 12 | Story-centric copy patch | **include in 3e-1** | Subset of P19H-3d-1; bundled with deploy |
| 13 | Tests | **include in 3e-1** | Timeline append, dedup, brief shape, UI smoke |
| 14 | Timeline UI (full expandable) | **defer to 3e-2** | 3e-1: brief embeds last 3 events; full list in 3e-2 |
| 15 | LLM-enriched narrative summary | **defer to 3e-2** | 3e-1 deterministic OK |
| 16 | Customer proactive gap question auto-send | **defer to 3e-2** | 3e-1 computes question; Chen-facing first |
| 17 | Phone summary timeline event | **defer to 3e-2** | P19H-3c-R5 dependency |
| 18 | Broker note timeline event | **defer to 3e-2** | Workbench entry form |
| 19 | H5 upload timeline event | **defer to 3e-2** | Low priority; attachments already on case |
| 20 | R7 H5 nag suppression | **defer to 3e-2** | Copy patch partial in 3e-1 |
| 21 | Broker Manual Slot Assignment | **defer to 3e-2** | After brief ships; low priority |
| 22 | OCR / ASR / damage AI | **never** | Category guardrail |
| 23 | Fault / coverage / carrier filing | **never** | Broker domain |
| 24 | Schema migration / new DB table | **never** | JSONB only |
| 25 | AI photo classification | **never** | Wrong slot worse than unassigned |

### 3e-1 deliverables (concrete)

```text
Backend:
  - append_claim_timeline_event(case_id, event) in case_store or claim_state
  - Wire: claim_basics (text), media_intake (image), basics_complete transition
  - build_claim_case_brief(case) → claim_case_brief dict
  - enrich_claim_for_workbench() adds claim_timeline + claim_case_brief

Frontend:
  - ClaimCaseBriefPanel.tsx — hero above ClaimEvidenceChecklist
  - Collapse Evidence Checklist by default for claim cases

Copy:
  - Opening「陈总办公室值班助手」framing
  - Photo ack trim (no H5 re-push language)
  - Basics-complete story-centric C1 (H5 demoted to secondary)

Tests:
  - test_claim_timeline_append_dedup
  - test_build_claim_case_brief_deterministic
  - test_claim_case_brief_missing_info_priority
  - test_enrich_claim_for_workbench_includes_brief
```

---

## 7. Claim Timeline Data Shape

### 7.1 Storage

- Field: `claim_timeline` (array on case JSONB, same as `known_facts`)
- Max length: **50 events** (ring buffer — drop oldest when exceeded)
- No schema migration

### 7.2 Event types

| `event_type` | When | Required fields |
|--------------|------|-----------------|
| `claim_started` | New claim case created | `actor: system` |
| `customer_text` | WeCom text on claim path | `text`, `message_id` |
| `customer_photo` | WeCom image bound to case | `attachment_id`, `message_id` |
| `customer_voice_stub` | WeCom voice (no ASR) | `attachment_id` optional, `message_id` |
| `basics_complete` | All 3 basics fields present | `facts_snapshot` |
| `h5_upload` | H5 slot received (3e-2) | `attachment_id`, `slot_key` |
| `broker_note` | Chen Workbench note (3e-2) | `text`, `broker_user` |
| `phone_summary` | Chen phone summary (3e-2) | `text`, `broker_user` |
| `system_ack` | Optional — bot reply logged (3e-2) | `text` |

### 7.3 Common fields (all events)

```json
{
  "event_id": "evt_<uuid>",
  "event_type": "customer_text",
  "source_channel": "wecom",
  "created_at": "2026-07-08T19:03:00Z",
  "actor": "customer",
  "message_id": "wm_abc123",
  "attachment_id": null,
  "text": "昨晚在 Costco 停车场被追尾",
  "metadata": {}
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_id` | string | yes | `evt_` + uuid4 |
| `event_type` | string | yes | From table above |
| `source_channel` | string | yes | `wecom` / `h5_task` / `workbench` / `phone` / `system` |
| `created_at` | ISO8601 | yes | Event time (message time, not persist time) |
| `actor` | string | yes | `customer` / `broker` / `system` |
| `message_id` | string | no | WeCom `msg_id` — idempotency key for chat |
| `attachment_id` | string | no | Links to `case_attachments[]` |
| `text` | string | no | Message body or summary |
| `metadata` | object | no | Extensible — `slot_key`, `facts_snapshot`, etc. |

### 7.4 Idempotency rule

```text
IF event has message_id AND message_id already in claim_timeline[].message_id
  → skip append, return existing event_id
IF event_type=customer_photo AND attachment_id already in timeline
  → skip append
ELSE
  → append event
```

### 7.5 Ordering rule

- Append-only array
- Sort key: `created_at` ascending
- Display: chronological (oldest first)
- Tie-break: append order

### 7.6 Attach existing `case_attachments`

On 3e-1 deploy, **optional backfill** for open claim cases:

```python
for att in case_attachments:
    if att.source == "wecom" and att not in timeline:
        append customer_photo event
```

Not required for ship — forward-only OK for pilot.

### 7.7 Future channels

| Channel | `source_channel` | `event_type` | Notes |
|---------|------------------|--------------|-------|
| H5 upload | `h5_task` | `h5_upload` | Include `metadata.slot_key` |
| Phone note | `phone` | `phone_summary` | Broker-entered text |
| Broker Workbench | `workbench` | `broker_note` | Free text |
| Voice transcript | `wecom` | `customer_voice` | 3e-2+ when ASR ships; until then `customer_voice_stub` |

### 7.8 Example timeline

```json
{
  "claim_timeline": [
    {
      "event_id": "evt_001",
      "event_type": "claim_started",
      "source_channel": "wecom",
      "created_at": "2026-07-08T19:02:00Z",
      "actor": "system",
      "text": "客户发起理赔"
    },
    {
      "event_id": "evt_002",
      "event_type": "customer_text",
      "source_channel": "wecom",
      "created_at": "2026-07-08T19:02:30Z",
      "actor": "customer",
      "message_id": "wm_001",
      "text": "我要理赔"
    },
    {
      "event_id": "evt_003",
      "event_type": "customer_text",
      "source_channel": "wecom",
      "created_at": "2026-07-08T19:03:00Z",
      "actor": "customer",
      "message_id": "wm_002",
      "text": "昨晚7点 Costco 停车场 被追尾"
    },
    {
      "event_id": "evt_004",
      "event_type": "basics_complete",
      "source_channel": "system",
      "created_at": "2026-07-08T19:03:01Z",
      "actor": "system",
      "metadata": {
        "facts_snapshot": {
          "accident_datetime": "昨晚7点",
          "accident_location": "Costco 停车场",
          "accident_description": "被追尾"
        }
      }
    },
    {
      "event_id": "evt_005",
      "event_type": "customer_photo",
      "source_channel": "wecom",
      "created_at": "2026-07-08T19:05:00Z",
      "actor": "customer",
      "message_id": "wm_003",
      "attachment_id": "att_xyz",
      "metadata": { "mime_type": "image/jpeg" }
    }
  ]
}
```

---

## 8. Claim Case Brief Data Shape

### 8.1 Top-level shape

```json
{
  "claim_case_brief": {
    "summary": "李女士报告昨晚约7点在 Costco 停车场被追尾，后保险杠受损。已收到 3 张微信照片。对方车牌和受伤情况尚未确认。",
    "customer": {
      "display_name": "李女士",
      "source_channel": "wecom",
      "wecom_external_userid": "wm_..."
    },
    "key_facts": {
      "accident_datetime": "昨晚7点",
      "accident_location": "Costco 停车场",
      "accident_description": "被追尾",
      "injury_status": "unknown",
      "police_involved": "unknown",
      "other_party_info": "unknown",
      "own_vehicle_info": null
    },
    "evidence_received": {
      "photo_count": 3,
      "photo_sources": { "wecom": 3, "h5_task": 0 },
      "voice_count": 0,
      "has_basics": true,
      "slots_received": ["customer_damage_photo"],
      "slots_missing": ["other_party_vehicle_photo"],
      "unassigned_wecom_photos": 3
    },
    "missing_info": [
      {
        "key": "other_party_plate",
        "label": "对方车牌 / 保险信息",
        "severity": "important",
        "reason": "not_mentioned"
      },
      {
        "key": "injury_status",
        "label": "是否有人受伤",
        "severity": "critical",
        "reason": "unknown"
      }
    ],
    "next_best_question": "请问有人受伤吗？对方车牌号您看到了吗？",
    "confidence": "medium",
    "source_event_ids": ["evt_003", "evt_004", "evt_005"],
    "brief_updated_at": "2026-07-08T19:05:01Z",
    "brief_version": 1
  }
}
```

### 8.2 Field definitions

#### `summary`

- **Format:** 2–4 sentences, Chinese, past tense narrative
- **3e-1:** Template-built from `known_facts` + photo count + top missing item
- **3e-2:** Optional LLM polish (same guardrails)
- **Must include:** who (if known), what, when/where (if known), evidence count, top gap
- **Must not include:** fault, coverage,「已报案」

#### `key_facts`

| Key | Values | Source |
|-----|--------|--------|
| `accident_datetime` | string \| null | `known_facts` |
| `accident_location` | string \| null | `known_facts` |
| `accident_description` | string \| null | `known_facts` |
| `injury_status` | `yes` / `no` / `unknown` | safety gate + keyword scan |
| `police_involved` | `yes` / `no` / `unknown` | keyword scan timeline |
| `other_party_info` | string \| null | extracted from description |
| `own_vehicle_info` | string \| null | if mentioned |

#### `evidence_received`

| Key | Purpose |
|-----|---------|
| `photo_count` | Total claim attachments (image/*) |
| `photo_sources` | Breakdown by `source` |
| `voice_count` | Voice stubs |
| `has_basics` | `is_accident_basics_complete()` |
| `slots_received` / `slots_missing` | From existing `claim_evidence_summary` |
| `unassigned_wecom_photos` | Count from existing helper |

#### `missing_info`

| `severity` | Meaning |
|------------|---------|
| `critical` | Injury unknown, safety unclear |
| `important` | Other party, police, core photos |
| `optional` | Scene photo, extra detail |

| `reason` | `not_mentioned` / `unknown` / `not_provided` / `skipped` |

#### `next_best_question`

- Single string, conversational Chinese
- Priority: injury > time > location > other party > photos
- **3e-1:** Computed for Chen; not auto-sent
- Max 2 short questions joined（「A？B？」）only if both critical — prefer one

#### `confidence`

| Level | Criteria |
|-------|----------|
| `low` | Basics incomplete OR zero photos AND vague description |
| `medium` | Basics complete + some photos OR good description |
| `high` | Basics + photos + injury answered + other party mentioned |

#### `source_event_ids`

- Last N timeline events used to build brief (audit trail)
- Typically last 5–10 events

#### Stale / unknown handling

| Situation | Brief behavior |
|-----------|----------------|
| Field not yet provided | `null` in key_facts; appears in `missing_info` |
| Customer said「不知道」 | `key_facts` = `"unknown"`; not in missing_info |
| Contradictory messages | Timeline shows both; summary uses **latest** + flag `metadata.conflict: true` (3e-2) |
| No timeline yet | Brief from `known_facts` + attachments only; `confidence: low` |

### 8.3 Chinese labels for Workbench

| Key | Label |
|-----|-------|
| `summary` | 事故摘要 |
| `key_facts.accident_datetime` | 事故时间 |
| `key_facts.accident_location` | 事故地点 |
| `key_facts.accident_description` | 事故经过 |
| `key_facts.injury_status` | 受伤情况 |
| `key_facts.police_involved` | 警方介入 |
| `key_facts.other_party_info` | 对方信息 |
| `evidence_received.photo_count` | 已收照片 |
| `missing_info` | 还缺什么 |
| `next_best_question` | 建议问客户 |
| `confidence` | 资料完整度 |
| `claim_timeline` | 事故时间线 |

#### Injury status display

| Value | Display |
|-------|---------|
| `yes` | 有受伤 ⚠️ |
| `no` | 无受伤 |
| `unknown` | 待确认 |

---

## 9. Workbench Layout

### 9.1 Recommended section order

| # | Section | Default state | Purpose |
|---|---------|---------------|---------|
| 1 | **Claim Case Brief** | Expanded | Hero — 10-second comprehension |
| 2 | **还缺什么** (from brief) | Expanded | Callback agenda |
| 3 | **建议问客户** | Expanded | Copy-ready question |
| 4 | **事故时间线** | Collapsed (show last 3) | Provenance / drill-down |
| 5 | **已收资料 / 照片** | Expanded if photos | Thumbnails without slots |
| 6 | **事故基本信息** | Collapsed | Redundant with brief; power users |
| 7 | **照片清单 (H5)** | **Collapsed** | Slot status — secondary |

### 9.2 Brief panel fields (above the fold)

```text
事故摘要
────────────────────────────────────────
李女士 · 昨晚 Costco 停车场被追尾，已收 3 张微信照片。

时间：昨晚7点    地点：Costco 停车场
受伤：待确认      警方：待确认
照片：3 张（微信）  资料完整度：中

还缺什么
· 对方车牌 / 保险信息
· 是否有人受伤

建议问客户
「请问有人受伤吗？对方车牌号您看到了吗？」
```

### 9.3 Migration from today

**Today (P19H-3c-3B):**

```text
1. Accident Basics
2. Evidence Checklist  ← hero
3. Case attachments
```

**After P19H-3e-1:**

```text
1. Claim Case Brief     ← NEW hero
2. 还缺什么 + 建议问客户
3. 事故时间线 (collapsed)
4. 已收照片
5. Accident Basics (collapsed)
6. Evidence Checklist (collapsed)
```

---

## 10. Customer Copy

Tone: calm · short ·「我先帮陈总记录」· no legal/coverage promise · no「已报案」· no「一定会赔」· no「责任在谁」

### 10.1 Claim start / safety

```text
您好，我是陈总办公室的值班助手。

请先确认您和车上的人是否都安全？有没有受伤？

如果安全，请告诉我大概时间、地点、发生了什么事。
我会先帮您记录下来，陈总会人工确认后联系您。
```

### 10.2 Accident story prompt (basics incomplete)

```text
谢谢。请用一条消息补充：
· 大概什么时候、在哪里
· 发生了什么事

不用写得很正式，说清楚就行。
```

### 10.3 After receiving basics

```text
【事故信息已记录 ✅】

时间：{accident_datetime}
地点：{accident_location}
描述：{accident_description}

您可以继续在微信里补充说明或发照片，都会记到同一份记录里。
如果想分步补充，可以点下面「补充事故资料」。
陈总会整理确认后联系您。
```

### 10.4 After receiving photo

```text
收到照片，已记到这份事故记录里 ✅
陈总会整理确认，不用重复发同一张。
```

### 10.5 After receiving voice

```text
语音已收到，我先帮您记下。
陈总会听完后再联系您。
您也可以打字说一下时间和地点。
```

### 10.6 Missing one key fact

```text
好的，已记录。

请问{missing_field_question}？
```

Examples: `事故大概是什么时候？` / `事故在哪里发生的？` / `有人受伤吗？`

### 10.7 Ambiguous multiple claims (tier B)

```text
您有不止一起进行中的事故记录。
请回复要补充哪一起，或回复「新事故」开始新的记录。
陈总会帮您确认。
```

### 10.8 No open claim + photo first

```text
照片已收到 ✅

如果这是理赔相关，请回复「我要理赔」，
我帮您建立事故记录。
```

### 10.9 Human handoff / contact Chen

```text
好的，您可以点下面「联系陈总」，或直接拨打陈总电话。
紧急情况请先拨打 911。
```

---

## 11. Avoiding Chen Clerical Work

### 11.1 Why Broker Manual Slot Assignment is lower priority

| Factor | Slot assignment | Case Brief |
|--------|-----------------|------------|
| Solves Chen's #1 pain | ❌ No — he still doesn't know the story | ✅ Yes — narrative + gaps |
| Adds Chen work | ✅ Yes — drag photos to 3 buckets | ❌ No — read-only summary |
| Customer value | Low — customer already sent photos | High — faster callback |
| Pilot volume | ~5–15 claims/month — eyeball OK | Always valuable |
| Depends on | Checklist-centric model | Story-centric model |

Slot assignment optimizes **H5 checklist accuracy**. Case Brief optimizes **broker service velocity**. R4 ranked「scroll WeChat to reconstruct story» as pain #1 — brief addresses that directly.

### 11.2 How Case Brief reduces Chen work more than slot assignment

| Without brief | With brief |
|---------------|------------|
| Open WeChat → scroll → memory | Open Workbench → read 4 sentences |
| Checklist ○ but photos exist → confusion |「3 张微信照片」+ thumbnails |
| Re-ask customer for time/place | Summary shows what's recorded |
| Guess what to ask on callback | `next_best_question` ready |

### 11.3 Minimal photo handling for pilot

| Enough for pilot | Not required |
|------------------|--------------|
| Photos on case (`case_attachments`) | Slot assignment |
| Thumbnail grid in brief | AI classify damage/scene/other |
| Count + source badge | OCR plate read |
| `unassigned` OK | Checklist all-green |

Chen can verbally ask「这是车损还是对方车» on callback — acceptable at pilot volume.

### 11.4 Show photos without forcing classification

- Grid view: all images, source badge, timestamp
- No drag-drop in 3e-1
- Checklist collapsed — shows slot status for H5 users without blocking brief
- Copy to Chen: 「微信照片已收到，暂未分类」— not「待您归类」

### 11.5 When manual classification might become useful

| Trigger | Action |
|---------|--------|
| Claim volume > 20/month | Revisit slot assign |
| Carrier filing needs slot-specific PDFs | Broker assigns at filing time |
| Chen requests it explicitly | P19H-3d-2 as optional power feature |
| H5 adoption drops | Slots matter less — timeline matters more |

**Default:** Story recorder path makes slot assignment **optional forever**, not MVP gate.

---

## 12. Acceptance Criteria for P19H-3e-1

| # | Criterion | Verification |
|---|-----------|--------------|
| AC-1 | Every Claim text message on active case appends `customer_text` timeline event | Unit test + scenario sim |
| AC-2 | Every bound WeCom image appends `customer_photo` timeline event | Unit test |
| AC-3 | Duplicate `wecom_msg_id` does not duplicate timeline event | Idempotency test |
| AC-4 | `basics_complete` event fires once when third field captured | Integration test |
| AC-5 | `build_claim_case_brief()` returns all required keys | Schema test |
| AC-6 | Brief `summary` updates when basics or timeline changes | Regression test |
| AC-7 | `missing_info` identifies unknown injury / location / time | Rule test |
| AC-8 | `next_best_question` is exactly one primary question | Assert single string |
| AC-9 | Workbench Claim drawer shows Case Brief **above** Evidence Checklist | UI test |
| AC-10 | Evidence Checklist **collapsed by default** on claim cases | UI test |
| AC-11 | No liability / coverage / claim filed language in brief or copy | Guardrail test |
| AC-12 | Add Vehicle lane unaffected — no timeline on non-claim cases | Lane isolation test |
| AC-13 | `enrich_claim_for_workbench()` includes `claim_case_brief` + `claim_timeline` | API test |
| AC-14 | Voice message creates `customer_voice_stub` event (no ASR) | Stub test |
| AC-15 | Existing tests pass; new tests added | CI green |

---

## 13. Final Recommendation

### 13.1 Expected final answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What should we build next? | **P19H-3e-1 Claim Story Timeline + Case Brief Foundation** |
| 2 | Best product experience? | Customer talks normally in WeChat → AI scribes → Chen opens Brief |
| 3 | Data backbone? | **`claim_timeline[]` + `claim_case_brief`** on existing case JSONB |
| 4 | What should Chen see first? | **Claim Case Brief** — summary, facts, gaps, next question |
| 5 | What should customer do? | **Say the accident in WeChat** — text/photos/voice; no forced wizard |
| 6 | What should AI do? | **Record first, organize second, ask one gap question, never adjudicate** |
| 7 | What should we not do? | OCR, ASR, damage AI, slot assignment hero, carrier filing, fault/coverage |
| 8 | Is H5 still needed? | **Yes, as optional 补充资料** — not primary, not first CTA |
| 9 | Is Broker Manual Slot Assignment needed now? | **No** — defer until brief ships; low priority |
| 10 | GO/HOLD/STOP? | **GO** on 3e-1 · **HOLD** on slot assign, phone summary, LLM brief · **STOP** on adjuster scope |

### 13.2 Strategic alignment

This recon **implements** P19H-3e category strategy with industry-backed UX patterns:

```text
FNOL capture discipline     → timeline append, no adjudication
Unified claim file          → one case_id, all channels
Guided not form-heavy       → basics + one question
Human-in-the-loop           → Chen decides; AI scribes
Spark Driver simplicity       → one customer action; hidden complexity
```

### 13.3 Supersedes

| Prior doc | Superseded item |
|-----------|-----------------|
| P19H-3d-R1 | Next sprint = 3d-1 copy first → **now 3e-1 brief first, copy bundled** |
| P19H-3d-R0/R1 | H5 primary CTA → **WeChat primary, H5 secondary** |
| P19H-3d-R1 | Slot assignment immediately after copy → **deferred** |

### 13.4 Sprint sequence (confirmed)

```text
1. P19H-3e-1   Claim Story Timeline + Case Brief Foundation     ← NEXT
2. P19H-3e-2   Timeline UI + LLM brief + customer gap auto-send
3. P19H-3c-R5  Broker phone summary → timeline
4. P19H-3d-2   Broker Manual Slot Assignment (optional, low priority)
```

---

## Appendix A — Industry Reference Notes

| Source pattern | Application |
|----------------|-------------|
| Snapsheet unified claim file | All comms + docs in one searchable record → `claim_timeline` + brief |
| Guidewire ClaimCenter | Centralized data, automated tasks, human decision in workflow → brief + checklist demoted |
| MDS / FNOL modernization | Capture first, organize second → timeline before brief |
| Walmart Spark Driver | One task UX → one gap question, no exposed backend |
| P19H-3c-R1 omnichannel | Channels are inputs, not workflows → timeline event per channel |

---

## Appendix B — Code Touchpoints (3e-1 implementation map)

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/case_store.py` | `append_claim_timeline_event()` |
| `services/fiqa_api/wecom/claim_basics.py` | Timeline on text + basics_complete |
| `services/fiqa_api/wecom/media_intake.py` | Timeline on image bind |
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | `build_claim_case_brief()`, enrich |
| `services/fiqa_api/wecom/reply.py` | Story-centric copy patch |
| `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx` | **New** hero panel |
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Brief above checklist, collapse checklist |
| `scripts/run_inbox_triage_scenarios.py` | Timeline + brief assertions |

---

*P19H-3e-R1 complete. Best practice recon only. No production code. No deploy.*
