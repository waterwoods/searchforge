# P19H-3h — Smooth UX / Idempotency / Async Design

**Date:** 2026-07-10  
**Sprint:** P19H-3h Design  
**Priority:** Critical — pilot trust depends on「点了就知道有没有成功」

---

## Design goal

Customer experience must feel like **Spark Driver**, not a fragile chatbot:

- Same action twice → same outcome, not duplicate work
- Every tap gets immediate feedback
- Status Card and H5 never disagree on「到哪一步了」
- Exceptions (collision, multi-open) never corrupt the happy path
- Backend can evolve sync → async without changing customer contract

**Production bar:** Spark Driver inspiration is **production-grade task workflow** — task cards, state machines, evidence chains, explicit feedback, exception control — not a chatbot demo. Smooth UX is how we meet the production standard; demo polish without reliability is **out of scope**.

---

## Core principle — Production-grade workflow product, not AI demo

**做可上线、可卖钱、能省时间的 production 产品，不做 AI 炫技 demo。**

Idempotency, loading states, async evolution, and error recovery exist because **production products** must survive real networks, real double-taps, and real broker trust — not because they look good in a demo.

| Production requirement | This document's answer |
|------------------------|------------------------|
| Stable, clear, low-confusion UX | Loading/disabled (§E), 短确认 (§B), Status sync (§C) |
| Structured main flow | H5 PATCH/submit authoritative; AI/chat supplemental |
| Idempotent, recoverable | §A keys, §G definitions, §H risky interactions |
| Evidence on key actions | Timeline events on submit, field save, photo upload |
| Ship discipline | Implementation checklist, metrics, smoke before deploy |

**AI is a capability, not the productized flow.** Faster chatbot replies do not satisfy the production bar. Deterministic task progression with AI behind the scenes does.

---

## Core principle — Structured Task First, AI Assist Second

**结构化任务优先，AI 理解辅助。**

Smooth UX is not「faster chatbot replies.」It is **deterministic task progression** with AI working behind the scenes.

| What controls the flow | What does NOT |
|------------------------|---------------|
| State machine (`derive_claim_phase`, step completion) | AI extraction or chat inference |
| H5 explicit submit / PATCH | WeCom free-text guessing |
| Idempotent button + phase guards | LLM deciding next customer prompt |

**Surface roles:**

- **H5 Task Page** — structured task execution (buttons, fields, upload, submit)
- **WeCom** — entry, notify, 短确认, Status/Start/End/Confirm Cards — not complex intake main UI
- **AI** — background understand, organize, summarize, missing hints, risk flags, broker draft
- **Broker Workbench** — shows AI draft + structured facts; broker confirms before treating as final

**Input priority (conflict resolution):**

```text
H5 submit/field  >  H5 confirmed facts  >  WeCom supplemental  >  AI draft
```

When chat and H5 disagree on the same `known_facts` key, **H5 wins** (see risky interaction #8). AI-extracted values never auto-advance the H5 wizard or phase without structured confirmation.

**Claim H5 MVP:** All idempotency and async patterns below assume this principle — sync H5 writes are authoritative; WeCom/AI paths are assist layers that must not fork the happy path.

### Core principle — Append-first, Split-later

**先归档，后拆分。**

Customer-facing UX should not make users manage multiple incidents/cases. For Claim/Add Car, ordinary inbound content should append to the current lane/task timeline. AI, broker, and backoffice can later classify, split, merge, archive, or flag if needed. This reduces customer cognitive burden and keeps the workflow production-grade.

| Smooth UX implication | Append-first rule |
|-----------------------|-------------------|
| **短确认** | Append ack is one line — not a Collision Card for passive accident words |
| **幂等** | Re-sent supplements dedupe; repeat「我要理赔」resends H5 continue, not new case |
| **状态卡同步** | Status / missing / append replies include H5 continue when intake continuable |
| **异常不污染主路径** | Collision Confirm is **rare** — strong explicit new accident only |
| **Multi-open** | Append to newest active Claim + broker `possible_multi_claim_context` flag |

---

## A. 幂等 (Idempotency principles)

| Rule | Customer expectation | Backend guarantee |
|------|---------------------|-------------------|
| Same button clicked twice | One effect | Idempotency key → dedupe store |
| Same submit clicked twice | One handoff to broker | Phase guard + submit key |
| Same photo uploaded twice | One attachment (or update) | Content-hash or slot+hash key |
| Same WeCom shortcut tapped repeatedly | Short ack or no-op | msg_id dedup + reply dedup |

**Golden rule:** At-least-once delivery (WeCom callbacks, mobile networks) must be safe. The system is **idempotent by default**, not opt-in.

---

## B. 短确认 (WeCom quick reply copy)

WeCom supplements should be **short acknowledgments**, not full Status Cards, unless customer explicitly requests status.

| Trigger | Copy |
|---------|------|
| Generic text/photo received | `已收到，正在为您整理，请稍等。` |
| Claim Start ceremony complete | `事故记录已开始，请继续下一步。` |
| Status Card just sent | `状态卡刚已发送，您可以继续补充资料。` |
| H5 field save (if WeCom notify enabled) | `已记录，您可以继续在页面填写。` |
| Photo bound to active case | `照片已收到，已记入当前记录。` |

**Do NOT** send a second Start Card, Confirm Card, or End Card as ack.

---

## C. 状态卡 (Status Card sync)

Status Card answers: **「现在到哪一步？」**

| Principle | Implementation |
|-----------|----------------|
| H5 and Status Card agree | Both read `derive_claim_phase()` + `missing_info` from same case |
| Status Card does not restart flow | `is_claim_status_request` → Status only; no new case |
| Status Card includes H5 link | Footer: `继续补充资料：{H5_LINK}` (mint or refresh token) |
| After H5 submit | Status shows `已提交` / broker_review state |
| Rate limit | Max 1 Status Card per status request; dedup within 30s window |

**Forbidden:** Status request creating new Claim; Status Card with Start Card content mixed in.

---

## D. 后台异步 (Async evolution)

### Phase 1 — Synchronous hardening (Claim H5 MVP)

| Path | Behavior |
|------|----------|
| H5 field PATCH | Sync write to Postgres; 200 before UI advance |
| H5 submit | Sync phase transition; 200 before Done screen |
| WeCom callback | Existing sync path (`WECOM_INBOX_QUEUE=0`) |
| Customer ack | Immediate from handler or H5 UI |

**Goal:** Correctness and idempotency first. Latency acceptable for pilot volume.

### Phase 2 — Callback quick ack + queue worker

| Path | Behavior |
|------|----------|
| WeCom inbound | Immediate 短确认; enqueue processing |
| Worker | Extract, append timeline, update facts as **provisional/draft** |
| Status Card | On demand or post-worker |

**Customer contract unchanged:** always get quick ack; Status Card may lag seconds.

**Structured Task First:** Async worker must not advance `claim_phase` or mark H5 steps complete from chat alone. Extracted facts remain provisional until H5 PATCH/submit or broker Workbench confirmation.

### Phase 3 — Full async with retry / dead-letter

| Component | Behavior |
|-----------|----------|
| Queue | Durable (existing `inbox_queue` / PG) |
| Retry | Exponential backoff; max 5 |
| Dead-letter | Admin visibility; no silent loss |
| H5 | Remains sync for writes (form trust) |

**H5 submit stays sync through Phase 3** — broker handoff must be atomic from customer perspective.

---

## E. Loading / disabled state (H5)

| State | UI |
|-------|-----|
| Idle | Primary button enabled |
| Submitting | Button `disabled`; spinner; label「提交中…」|
| Success | Navigate to Done; button stays disabled |
| Network error | Re-enable button; show「提交失败，请重试」|
| Already submitted (409) | Redirect to Done; no error alarm |

**Never** let user wonder if click worked. Minimum 300ms loading visibility even on fast responses (prevent double-tap race).

**Apply to:** every step「下一步」, photo upload, final submit.

---

## F. Reply dedup (WeCom cards)

| Card type | Dedup rule |
|-----------|------------|
| Start Card | One per case creation; `msg_id` + case_id key |
| Confirm Card | One pending per collision/lane-switch state |
| Status Card | Per request; suppress duplicate within 30s |
| End Card | One per `broker_done`; idempotent replay = no send |
| C1 basics complete | One per phase transition |

**Leverage:** `reply_dedup.py`, `message_processed.py`, `claim_end_card_state` in PG extra.

---

## G. Idempotency keys (definitions)

### Message-level key

```text
wecom_msg:{channel_id}:{msg_id}
```

- **Scope:** Inbound WeCom message processing
- **Store:** `message_processed` table / cache
- **TTL:** 7 days
- **Effect:** Second process → no-op

### Action-level key

```text
wecom_action:{external_userid}:{action_type}:{case_id}:{payload_hash}
```

- **Scope:** msgmenu button clicks (injury, collision choice, lane switch)
- **TTL:** 24h
- **Effect:** Repeat tap → 短确认 or silent no-op

### Form-submit key

```text
h5_submit:{case_id}:{flow}:{submit_intent_id}
```

- **Scope:** `POST /api/h5/tasks/{token}/submit`
- **Client:** Generate `submit_intent_id` (UUID) on first click; reuse on retry
- **Effect:** Duplicate → 200 + current phase; no duplicate timeline

### Step-field key

```text
h5_field:{case_id}:{step}:{field}:{value_hash}
```

- **Scope:** `PATCH /api/h5/tasks/{token}/fields`
- **Effect:** Same value re-posted → 200 no-op timeline (or merge)

### Photo-upload key

```text
h5_photo:{case_id}:{slot}:{content_sha256}
```

- **Scope:** `POST /api/h5/tasks/{token}/upload`
- **Effect:** Same bytes → return existing attachment id; no duplicate GCS object

### Broker-done key

```text
broker_done:{case_id}
```

- **Scope:** `POST /api/inbox/cases/{id}/broker-done`
- **Effect:** Already done → 200 idempotent; one End Card attempt

---

## H. Known risky interactions

### 1. User taps WeCom shortcut 3 times

| Layer | Behavior |
|-------|----------|
| **Expected** | One case created; subsequent taps → 短确认 or Status hint |
| **User-facing** | `事故记录已开始，请继续下一步。` (no 3 Start Cards) |
| **Backend** | `message_processed` + Start Card dedup on case_id |
| **Test** | Triple `我要理赔` within 10s → 1 case, 1 Start Card |

### 2. User sends same text twice

| Layer | Behavior |
|-------|----------|
| **Expected** | Append once or second merge no-op if identical hash within window |
| **User-facing** | `已收到，正在为您整理，请稍等。` |
| **Backend** | Timeline dedup in `append_claim_timeline_event` |
| **Test** | Duplicate narrative → 1 timeline text event |

### 3. User submits H5 twice

| Layer | Behavior |
|-------|----------|
| **Expected** | One broker handoff |
| **User-facing** | First → Done screen; second → Done screen (no error) |
| **Backend** | `h5_submit` key + phase guard |
| **Test** | Double-click submit → 1 `customer_submitted_intake` event |

### 4. User uploads same photo twice

| Layer | Behavior |
|-------|----------|
| **Expected** | One slot attachment (or replace) |
| **User-facing** |「照片已上传」|
| **Backend** | `h5_photo` content-hash key |
| **Test** | Same file twice → 1 attachment record |

### 5. WeCom callback retries

| Layer | Behavior |
|-------|----------|
| **Expected** | Process once |
| **User-facing** | Single reply (if any) |
| **Backend** | `wecom_msg:{msg_id}` |
| **Test** | Replay same callback payload → no duplicate case |

### 6. Network timeout after backend success

| Layer | Behavior |
|-------|----------|
| **Expected** | Client retry succeeds idempotently; user sees success |
| **User-facing** | Retry → Done screen |
| **Backend** | Submit key returns 200 with `already_submitted: true` |
| **Test** | Mock timeout after 200 → client retry → no duplicate |

### 7. Browser back/refresh after submit

| Layer | Behavior |
|-------|----------|
| **Expected** | Show Done state from server read, not blank form |
| **User-facing** | `GET /intake` → `submitted: true` → render Step 9 |
| **Backend** | Phase `broker_review` or post-submit flag in intake response |
| **Test** | Refresh on Done → still Done; back button → Review read-only |

### 8. Customer uses chat while H5 in progress

| Layer | Behavior |
|-------|----------|
| **Expected** | Chat appends to same case; H5 refresh shows merged facts |
| **User-facing** | Chat 短确认; H5 Review updates on next load |
| **Backend** | `known_facts` merge; H5 primary for structured fields |
| **Test** | H5 step 3 + chat location → both visible in Review |

### 9. Status Card during H5 active edit

| Layer | Behavior |
|-------|----------|
| **Expected** | Status reflects last committed server state |
| **User-facing** | May lag unsaved H5 draft — acceptable |
| **Backend** | Status reads DB only, not client draft |
| **Test** | Unsaved H5 field → Status shows missing until PATCH |

### 10. Token expired mid-trip

| Layer | Behavior |
|-------|----------|
| **Expected** | Graceful regen via WeCom |
| **User-facing** |「链接已过期，请回复『进度』获取新链接」|
| **Backend** | `进度` → Status Card + re-mint token (72h TTL) |
| **Test** | Expired token → 401 + recovery path documented |

---

## Implementation checklist (Phase 1 MVP)

- [ ] **Principle (production):** Production-grade workflow product — idempotent, recoverable, evidence-backed; not AI demo
- [ ] **Principle (architecture):** State machine controls phase; H5 structured input authoritative; AI/WeCom supplemental only
- [ ] Client: `submitting` state on all H5 primary buttons
- [ ] Client: `submit_intent_id` UUID per submit attempt
- [ ] Server: submit idempotency store (case_id + intent_id)
- [ ] Server: photo content-hash dedup
- [ ] Server: intake response includes `submitted` flag for refresh handling
- [ ] WeCom: Start Card dedup verified (existing)
- [ ] WeCom: 短确认 copy table implemented for media append
- [ ] Status Card: H5 link footer
- [ ] Tests: risky interactions 1, 3, 5, 6, 7 minimum

---

## Metrics (pilot observability)

| Metric | Alert threshold |
|--------|-----------------|
| Duplicate submit attempts blocked | Log count (healthy) |
| `claim_end_card_failed_v1` | >0 in demo → fix send env |
| H5 submit 5xx | Any → page |
| Avg H5 step PATCH latency | >2s p95 → investigate |
| Status/H5 phase mismatch reports | Any → bug |

---

*Complements P19H-3g-5 WeCom smooth UX; H5 idempotency is new scope for P19H-3h implementation.*
