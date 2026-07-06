# P18 — Chen Kui WeCom AI Case Intake Demo Blueprint

**Date:** 2026-07-04  
**Type:** Demo strategy + 3–4 day build plan — **planning only**  
**Audience:** Chen Kui (broker owner), Wu Xiaojie (office operator), Andy (founder)  
**Prerequisite:** WeCom channel technically working end-to-end:

`WeCom → Cloud Run → Cloud SQL (private IP) → inbox/outbox → WeCom reply`

Q0.11.1 PASS — one generic message → one guide-menu reply, no phantom outbox, no unintended Draft merge, generic text does not create Add Car Draft.

**Authority:** This document does not supersede ADR-001–005 or `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`. It defines what to **show** Chen Kui and what to **build next** in a focused sprint.

**Scope note:** B0 v1 treats mid–add-car claim mentions as a **flag only** (`claim_mentioned_at`). P18 deliberately adds **Story B — Claim Lite** as a *separate* standalone intake flow for the Chen Kui demo. Rule 8 still applies: one open flow per customer thread; claim during add-car → flag, not branch.

---

## 0. Main Positioning (say this first)

> **WeCom is only the channel. The product is an AI Case Intake Engine — an AI Insurance Workspace.**

Chen Kui should not walk away thinking “they built a WeChat chatbot.” He should walk away thinking:

> “My customers can message the office the way they already do — fragmented, over days, in Chinese and English — and my team gets a **case** with identity, memory, known facts, gaps, and a clear next action. **I confirm before anything changes.**”

---

## 1. Demo Narrative

### Before (today’s pain)

| Step | Reality |
|------|---------|
| Customer | Messages Chen Kui or Wu Xiaojie **personally** on WeChat |
| Information | Scattered across chat threads, voice notes, photos, days apart |
| Broker | Must **remember**, **ask again**, **organize**, **follow up** manually |
| Outcome | 10+ minutes of hunting and re-keying per add-car or accident call |

**Opening line for Chen Kui (Chinese):**

> “客户加车或出事故，吴小姐是不是要在微信里翻聊天记录、打电话补 VIN 和邮编，再手动输进系统？”

Wait for yes. Then:

> “这个演示不是‘聊天机器人能回消息’。是：**客户照常发微信，AI 帮办公室整理成一个 Case，你在 Workbench 里一眼看懂、点确认。**”

### After (what we demo)

```
Customer (WeCom service account)
    → fragmented messages over time
    → AI preserves identity + full conversation
    → AI builds/updates ONE active case (one business flow at a time)
    → Broker Workbench: identity, summary, known / missing / conflict, next action
    → Broker Confirm (Add Vehicle) or Manual Handle (Claim Lite)
    → Customer receives Done Card (Add Vehicle only) or safe ack (Claim)
```

### Why fragmented information is the hard problem

Insurance intake is rarely one clean form submission. Real customers:

- Send **partial facts** across multiple messages (“刚买了宝马” → later “VIN 是…” → next day “邮编 91101”)
- **Mix topics** (“加车，对了昨天还撞了”)
- **Contradict themselves** (two VINs, wrong ZIP, driver name unclear)
- **Never “submit”** — they just keep chatting

A chatbot that replies politely solves none of this. The product value is **case memory + structured readiness + broker gate** — turning chaos into something Wu Xiaojie can act on in under 30 seconds.

---

## 2. Five Core Demo Capabilities

### 2.1 Customer Identity Layer

| Concept | Demo behavior |
|---------|---------------|
| **Anchor** | WeCom `external_userid` on every inbound event |
| **Enrichment** | Merge with phone, ZIP, name, historical `service_records` when evidence is strong |
| **States to show** | **New Customer** · **Known Customer** · **Possible Match** |
| **Guardrail** | Do **not** over-merge automatically; uncertain match → broker confirmation |

**Existing:** `bind_case_channel_identity()`, `find_open_draft_case_by_external_userid()`, phone-based `active_case_resolver.py`, `update_case_customer()`.

**Gap for demo:** Explicit identity badge in Workbench (New / Known / Possible Match) — not built yet.

### 2.2 Conversation Memory Layer

| Concept | Demo behavior |
|---------|---------------|
| **Preserve** | Every original customer message, in order |
| **Timeline** | Evidence events + `record_messages` when Postgres path is on |
| **Future** | Images, click events (logged as evidence; no OCR in this sprint) |
| **Fragmented follow-ups** | Same case accumulates facts across turns and days |

**Existing:** `_record_wecom_evidence()`, `append_follow_up_message()`, `evidence_events[]`, `record_messages` table.

**Gap for demo:** Workbench “conversation thread” panel for WeCom-sourced cases (messages exist in DB; UI may show summary only today).

### 2.3 AI Case Builder

| Concept | Demo behavior |
|---------|---------------|
| **Classify** | Rule-based intent: add_car, claim_intake, policy_review, unclear |
| **Create/update** | Active case **only when actionable** (Start click, high-confidence + fields, or Claim Lite start) |
| **Summarize** | Known facts, missing fields, conflicts, suggested next question |
| **Discipline** | **One Business Flow at a Time** (Constitution Rule 8) |

**Existing:** `intent.py`, `identity.py` extractors, `active_case_bridge.py`, `_build_draft_case_stub()`, `collected_fields` / `still_needed_fields`.

**Gap for demo:** Claim Lite stub + extractors; optional “suggested next question” copy in customer reply.

### 2.4 Broker Workbench

| Surface | Demo behavior |
|---------|---------------|
| **List** | Cases from WeCom channel; Draft badge when `broker_confirmed_at` is null |
| **Detail** | Customer identity, business type, case summary, known / missing / flags, next action |
| **Actions** | **Confirm** → Done Card (Add Vehicle) · **Manual Handle** (Claim Lite — no auto policy change) |
| **Invariant** | No automatic policy change, ever |

**Existing:** `BrokerWorkbenchTab.tsx`, `PATCH /cases/{id}/confirm`, `confirm_case_by_broker()`, quote-ready / Manual Promote pattern.

**Gap for demo:** Claim Intake Summary block, identity state badge, WeCom channel indicator, claim banner (`claim_mentioned_at` is B0.4 — not implemented).

### 2.5 Future AI Opportunity Layer (vision placeholder only)

Show as a **disabled / “coming soon” insight box** in Workbench — do not automate:

- Renewal reminder · Cross-sell · Coverage gap · Risk flag · Missing opportunity · Claim urgency · Follow-up reminder

Reference: `docs/p16/P16_FUTURE_VISION.md` §8 — Loop 2 / Continuous Readiness hypothesis.

---

## 3. Architecture Map

### 3.1 End-to-end pipeline (production path)

```
Personal WeChat (customer)
        ↓
Enterprise WeCom 微信客服
        ↓
POST /api/wecom/kf/callback          [wecom_kf_callback.py]
        ↓ (WECOM_INBOX_QUEUE=1)
wecom_inbox_events                   [inbox_queue.py]
        ↓ manual drain / worker
process_wecom_inbox_event()          [inbox_worker.py]
        ↓
process_kf_msg_or_event()            [slice.py — orchestrator]
        ↓
sync_msg + watermark                 [sync_msg.py, sync_cursor.py, message_processed.py]
        ↓
normalize → classify intent          [normalize.py, intent.py]
        ↓
active case bridge                   [active_case_bridge.py]
        ↓
service_records + record_messages    [case_store.py, service_record_repository.py]
        ↓
reply outbox → WeCom send            [reply_outbox.py, send_msg.py, reply.py]
        ↓
Broker Workbench UI                  [BrokerWorkbenchTab.tsx]
        ↓
Broker Confirm → Done Card           [confirm_case_by_broker, PATCH .../confirm]
```

### 3.2 Component map (existing → role in demo)

| Layer | Component | File(s) | Demo role |
|-------|-----------|---------|-----------|
| **Channel** | Callback verify/decrypt | `routes/wecom_kf_callback.py` | Fast 200 ack |
| **Queue** | Inbox events | `wecom/inbox_queue.py`, `db/schema/wecom_inbox_events.sql` | Durable ingress (Q0) |
| **Queue** | Reply outbox | `wecom/reply_outbox.py`, `db/schema/wecom_reply_outbox.sql` | Exactly-one send |
| **Queue** | Admin drain | `scripts/wecom_drain_queues.py`, `routes/wecom_queue_admin.py` | Manual ops (no cron) |
| **Sync (Q0.10)** | Message dedup | `wecom/message_processed.py` | Claim `msg_id` before business logic; skip replay |
| **Sync (Q0.10)** | Sync cursor | `wecom/sync_cursor.py` | Watermark for incremental `sync_msg` pull |
| **Draft path** | Start-click create | `active_case_bridge.create_or_attach_draft_case_for_start_click()` | Draft on Start tap |
| **Draft path** | Field merge | `active_case_bridge.ingest_wecom_text_to_draft_case()` | VIN/ZIP/phone merge into open Draft |
| **Orchestration** | Slice | `wecom/slice.py` | B0 gates, merge rules (Q0.11.1) |
| **Intent** | Classifier | `wecom/intent.py` | add_car / claim / menu |
| **Identity** | Text extractors | `wecom/identity.py` | phone, VIN, ZIP, date, driver |
| **Case** | Active case bridge | `wecom/active_case_bridge.py` | Draft create/merge/confirm |
| **Case** | Resolver | `inbox_triage/active_case_resolver.py` | phone attach, broker_review |
| **Case** | Store | `inbox_triage/case_store.py` | flags, channel binding |
| **Persistence** | Postgres | `db/schema/stage1_service_record.sql` | `service_records`, `record_messages` |
| **Reply** | Start Card | `wecom/reply.py` `build_start_card_payload()` | Add Vehicle gate |
| **Reply** | Guide menu | `wecom/reply.py` `build_guided_menu_payload()` | Low-confidence routing |
| **Reply** | Done Card | `wecom/reply.py` `DONE_CARD_TEXT` | Post-confirm customer ack |
| **UI** | Workbench | `ui/.../BrokerWorkbenchTab.tsx` | Broker Confirm, quote progress |
| **API** | Confirm route | `routes/inbox_triage.py` `PATCH .../confirm` | Idempotent Done Card |

### 3.3 Feature flags (demo configuration)

| Flag | Purpose |
|------|---------|
| `WECOM_INBOX_QUEUE=1` | Queued ingress |
| `WECOM_REPLY_OUTBOX=1` | Queued egress |
| `WECOM_SLICE_SEND_REPLY=1` | Actually send to WeCom |
| `WECOM_B0_ACTIVE_WORKSPACE=1` | Start Card + Draft gate + no auto case on intent alone |

**Not in scope:** scheduler, cron, Pub/Sub, Cloud Tasks — use manual drain only (`docs/wecom_q0_smoke_test.md`).

### 3.4 Q0.10 reliability layer (why replay is safe)

Q0.10 pairs **sync cursor** (where to resume `sync_msg`) with **message_processed** (which `msg_id`s already ran business logic):

| Mechanism | File | What it prevents |
|-----------|------|------------------|
| `load_sync_cursor` / `save_sync_cursor` | `sync_cursor.py` | Re-pulling the entire WeCom history on every callback |
| `claim_message_processed` | `message_processed.py` | Double intent classification, double Draft merge, double outbox enqueue on callback retry |
| `update_message_processed_outcome` | `message_processed.py` | Audit trail: which case_id / outcome each msg_id produced |

Q0.11.1 proved the combination: generic text → exactly one guide-menu reply, no phantom outbox row, no Draft created without Start click.

---

## 4. Two Demo Storylines (build only these)

### Story A — Add Vehicle (primary, ~80% built)

**Already in code:** Start Card (`reply.py`), Draft on Start click (`slice.py` + `active_case_bridge.py`), field extractors (`identity.py`), Draft merge (`ingest_wecom_text_to_draft_case`), Broker Confirm + Done Card (`confirm_case_by_broker`, `BrokerWorkbenchTab.tsx`), B0 tests (`tests/test_wecom_active_case.py`).

**Customer script (can be split across 3–5 messages):**

1. “我想加一台车” → **Start Card** (no case yet)
2. Tap **Start / 开始** → **Draft Case** created, bound to `external_userid`
3. “VIN 1HGBH41JXMN109186” → merge into Draft
4. “邮编 91101，3月15号生效，主驾驶 Li Hua，电话 6265550100” → merge; quote_ready when complete
5. Broker opens Workbench → reviews known / missing → **Confirm**
6. Customer receives **Done Card**

**Proof points for Chen Kui:**

- Generic “hello” does **not** create a case (Q0.11.1)
- Fragmented messages **accumulate** into one Draft
- Broker sees readiness before anything is “real”
- Confirm is **explicit** and **idempotent**

**Maps to:** B0 contract steps 1–11 (`TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`).

### Story B — Claim Lite (secondary, ~20% built)

**Customer script:**

1. “刚出事故了” or menu **Claim / 事故理赔** → **Claim Start Card** or guided claim ack (new)
2. Customer provides over several messages: time, location, vehicle, injuries yes/no, other party, police report yes/no, “有照片稍后发”
3. AI creates **Claim Intake case** (separate service lane) — **collect and summarize only**
4. Workbench shows **Claim Intake Summary** (known / missing / urgency flags)
5. Broker clicks **Manual Handle** — **no** Confirm/Done Card automation, **no** FNOL filing

**Important boundaries:**

- Not full claim workflow
- Not adjuster dispatch
- Not photo OCR
- If customer mentions claim **inside** an open Add Vehicle Draft → flag only (`claim_mentioned_at`), do not branch flows (Rule 8)

**Maps to:** `intent.py` claim markers, `triage.py` claim templates (reference copy only), new claim stub in bridge.

---

## 5. What NOT to Do (3–4 day demo)

| Out of scope | Reason |
|--------------|--------|
| Full CRM / household model | Demo is case intake, not client management |
| Policy rating engine | ADR-003 — no carrier API |
| Automatic policy change | Broker gate is the product story |
| Full OCR / media automation | Images logged as evidence at most |
| Complete claim workflow | Claim Lite = intake summary only |
| Multi-topic workflow engine | One flow at a time; flags not branches |
| Cross-sell automation | Placeholder insight box only |
| Scheduler / cron / Pub/Sub / Cloud Tasks | Manual drain unless already running |
| Customer login / accounts | WeCom identity + phone is enough |
| Timeline UI | ADR-002 |
| LLM intent classification | Rules-first for demo reliability |

---

## 6. Minimal Data Model Gaps

All changes stay on existing `service_records.extra` + case JSON — **no new tables** (per B0 contract).

| Field / concept | Story | Action |
|-----------------|-------|--------|
| `wecom_external_userid` | A, B | ✅ Exists — ensure populated on all WeCom cases |
| `broker_confirmed_at` | A | ✅ Exists |
| `claim_mentioned_at` | A (Rule 8) | ⚠ B0.4 — set when claim inside add-car thread |
| `identity_match_state` | A, B | **New** — `new` \| `known` \| `possible_match` (extra JSON) |
| `identity_match_candidates` | A, B | **New** — optional list of record_ids + reason |
| `service_lane=claim_intake` | B | **New** — use existing lane pattern (`SERVICE_LANE_ADD_CAR` precedent) |
| Claim stub shape | B | **New** — `issue_category: claim_intake`, fields: `accident_time`, `location`, `vehicle`, `injuries`, `other_party`, `police_report`, `photos_pending` |
| `collected_fields` / `still_needed_fields` | B | Reuse add-car pattern with claim field set |
| `record_messages` rows | A, B | Ensure WeCom messages write on Postgres path (verify dual-write) |
| `intake_channel=wecom` | A, B | Set on save for channel filtering in Workbench |

---

## 7. UI / Workbench Gaps

| Gap | Priority | Story | Notes |
|-----|----------|-------|-------|
| Draft badge on case list | P0 | A | When `!broker_confirmed_at` — detail shows Confirm/Manual Promote; list badge not wired yet |
| WeCom channel tag | P0 | A, B | “微信客服” on list + detail |
| Identity state badge | P1 | A, B | New / Known / Possible Match |
| Claim Intake Summary panel | P0 | B | Known / missing claim fields, urgency |
| Claim mentioned banner | P1 | A | When `claim_mentioned_at` set mid add-car |
| Conversation thread (read-only) | P1 | A, B | Pull `record_messages` or evidence_events |
| Manual Handle CTA for claim | P0 | B | Distinct from Confirm — no Done Card |
| Future opportunity placeholder | P2 | — | Static “coming soon” card |
| Demo filter: WeCom cases only | P1 | A, B | Optional list filter for live demo |

**Already built (do not rebuild):** Confirm button + Done Card path (B0.3), Manual Promote, quote_ready tags, Copy Draft, collected/still_needed display for add-car, `broker_confirmed_at` Active Case tag in detail.

---

## 8. Three- to Four-Day Implementation Plan

### Day 1 — Polish Story A end-to-end

| Task | Owner | Est. |
|------|-------|------|
| Enable B0 flags on pilot Cloud Run revision | Ops | 30m |
| Run Add Vehicle script locally + manual drain | Eng | 1h |
| Fix any merge / phantom-outbox regressions | Eng | 2h |
| Workbench: Draft badge + WeCom channel tag | Eng | 2h |
| Write Chen Kui demo script (5 min, bilingual cues) | Eng | 1h |
| Internal rehearsal: fragmented 5-message add-car | Eng | 1h |

**Exit:** Story A repeatable twice without manual DB cleanup.

### Day 2 — Claim Lite backend

| Task | Owner | Est. |
|------|-------|------|
| Add `SERVICE_LANE_CLAIM_INTAKE` + claim stub builder | Eng | 3h |
| Claim Start Card (mirror Start Card pattern) | Eng | 2h |
| Claim field extractors in `identity.py` (time, location, injuries yes/no) | Eng | 2h |
| `create_or_attach_claim_case_for_start_click()` + merge path in `slice.py` | Eng | 3h |
| Unit tests: claim create, merge, no add-car cross-create | Eng | 2h |

**Exit:** Claim messages create/update claim case; add-car flow untouched.

### Day 3 — Claim Lite Workbench + identity

| Task | Owner | Est. |
|------|-------|------|
| Claim Intake Summary UI block | Eng | 3h |
| Manual Handle action (status + broker note; no Done Card) | Eng | 2h |
| Identity badge (new / known / possible_match) — phone lookup only | Eng | 2h |
| Implement `claim_mentioned_at` flag for Rule 8 | Eng | 2h |
| Conversation thread read-only (minimal) | Eng | 2h |

**Exit:** Story B visible in Workbench; Story A still passes.

### Day 4 — Demo hardening + Chen Kui rehearsal

| Task | Owner | Est. |
|------|-------|------|
| Full dual-story rehearsal with Wu Xiaojie role-play | Team | 2h |
| Future opportunity placeholder card | Eng | 1h |
| Demo checklist + rollback revision pinned | Ops | 1h |
| Fix P0 bugs from rehearsal only | Eng | 3h |
| Record 2-min screen capture backup (optional) | Ops | 1h |

**Exit:** 5-minute live demo path documented; both stories complete once each.

---

## 9. Five-Minute Demo Script (Chen Kui)

### Minute 1 — Pain + positioning

State the Before narrative. Emphasize: **not a chatbot demo**.

### Minute 2 — Story A live (customer phone)

Show fragmented add-car messages → Start Card → Start → facts drip in.

### Minute 3 — Workbench (broker laptop)

Open case → identity, collected / still needed → **Confirm** → show Done Card sent.

### Minute 4 — Story B (claim)

New customer thread: “刚出事故” → claim intake → summary in Workbench → **Manual Handle**.

### Minute 5 — Vision + close

Show opportunity placeholder. Restate:

> “微信只是入口。产品是：**AI 帮办公室整理 Case，您确认后才行动。**”

---

## 10. Acceptance Criteria

### Document (this file)

- [x] Clearly states WeCom is channel; AI Case Intake Engine is product
- [x] Centers identity + case memory + AI case builder + broker workbench
- [x] Recommends Add Vehicle + Claim Lite as the two demo stories
- [x] Explains why fragmented/inconsistent information is the hard problem
- [x] Maps to existing implementation (§3)
- [x] Provides practical 3–4 day build plan (§8)
- [x] Planning only — no deploy, no live smoke, no code changes in this task

### Demo readiness (after sprint)

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 1 | Channel vs product | Chen Kui repeats “case intake workspace” not “chatbot” |
| 2 | Story A E2E | Fragmented add-car → Draft → Confirm → one Done Card |
| 3 | Story A guardrails | Generic text → guide menu only; no phantom outbox |
| 4 | Story B E2E | Claim messages → Claim Intake Summary → Manual Handle |
| 5 | Rule 8 | Claim mention during add-car → flag only, no second case |
| 6 | Identity | Workbench shows New or Known; Possible Match requires broker ack |
| 7 | Memory | Broker can see original message sequence for the case |
| 8 | No auto policy change | No UI or copy promises automatic policy update |
| 9 | Ops safety | Manual drain only; rollback revision documented |
| 10 | Time | Full demo ≤ 5 minutes |

---

## 11. Related Documents

| Doc | Use |
|-----|-----|
| `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` | B0 implementation authority |
| `docs/p16/P16_CHEN_KUI_DEMO_SCRIPT.md` | Prior web add-car demo (reference tone) |
| `docs/wecom_q0_smoke_test.md` | Queue ops + safety rules |
| `docs/evidence/wecom_q0_11_1_resmoke_2026-07-04.md` | Q0.11.1 PASS evidence |
| `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` | Rules 7–8 |
| `docs/p16/P16_FUTURE_VISION.md` | Opportunity layer vision |

---

*Planning document only. Implementation, deploy, and live smoke are separate tasks.*
