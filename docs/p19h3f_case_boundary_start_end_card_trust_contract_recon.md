# P19H-3f — Case Boundary + Start/End Card Trust Contract Recon

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Product / workflow / trust contract recon — **no production code, no deploy, no schema migration**  
**Prerequisite:** P19H-3e Claim Story Recorder (timeline + brief shipped) · P19H-3d WeCom image binding · P19H-3c Identity Resolver · P19H-3e-R3 interaction model  
**Related:** `p19h3e_r3_claim_interaction_model_recon.md` · `p19h3e_r2_claim_story_recorder_smooth_ux_recon.md` · `p19h3e_r1_claim_story_recorder_best_practice_recon.md` · `p19h3e_claim_case_builder_category_strategy_recon.md` · `p19h3d_r1_claim_human_simulation_workflow_simplification_recon.md` · `p19h3d_r0_claim_photo_intake_ux_simplicity_recon.md` · `p19h3c_r2_claim_identity_resolution_duplicate_prevention_recon.md` · `p19h3c_r4_claim_workflow_business_value_alignment_recon.md` · `p19h0_claim_case_builder_state_machine_recon.md` · `evidence/p19h3e1_claim_story_timeline_case_brief_foundation_2026_07_09.md` · `evidence/p19h3d_deploy_wecom_image_binding_smoke_2026_07_09.md`

---

## 1. Executive Summary

P19H-3e shipped the **story recorder spine**: `claim_timeline[]`, `claim_case_brief`, Workbench Brief hero, WeCom photo binding, injury quick replies, and multi-entry surfaces. That work assumes a **formal claim case already exists**. It does not yet answer the more fundamental trust question:

> **When does a real case begin — and when must the system refuse to create one?**

Customers in WeChat will chat casually, ask one-off questions, send random or wrong photos, mention old accidents, ask general insurance questions, or formally say「我要理赔」. If the system treats all of these as case creation, both customer and broker lose trust:

| Confusion | Who feels it |
|-----------|--------------|
| 我是不是已经正式开始了？ | Customer |
| 这张照片是不是已经进入理赔？ | Customer |
| 陈总是不是已经在处理？ | Customer |
| 这个 case 是正式的，还是系统误建的？ | Broker |
| 哪些是闲聊，哪些是提交材料？ | Both |

**Product goal:** Build trust and save time — not create phantom cases.

### Hard product rule (north star)

```text
Random chat / random photo does not automatically create a case.
A case begins only through explicit intent or controlled task entry.
```

| Question | Answer |
|----------|--------|
| Core problem? | **Case boundary is implicit** — narrative + markers + buttons can create `service_lane=claim` without customer understanding they「开始了」 |
| What is a formal case? | One `case_id` with `service_lane=claim` that customer and broker agree is **this accident's active record** |
| What is NOT a formal case? | Casual chat, insurance Q&A, unconfirmed photos, `wecom_media_intake` quarantine rows |
| Start Card role? | **Trust ceremony** — customer-visible「事故记录已开始」+ disclaimer; not just a data-collection prompt |
| End Card role? | **Broker handoff ceremony** — customer-visible「陈总已确认收到」; never confused with carrier filing |
| Holding state? | **Pre-case buffer** — messages/photos acknowledged and stored, but no claim case until explicit confirm |
| Next coding sprint? | **P19H-3f-1 Case Boundary Policy** (after this recon) |
| Verdict | **GO** define trust contract · **HOLD** implementation to 3f-1 · **STOP** — no code in this recon |

**One-line thesis:**

> 闲聊和随手发图只进 Holding；只有客户明确说要开始、或从受控入口进入，才建正式 case — Start Card 宣告开始，End Card 宣告陈总已接手，中间每一步都说清楚「记录中 ≠ 已报案」。

---

## 2. The Trust Problem

### 2.1 Why this matters more than the next feature

Claim Story Recorder (P19H-3e) optimizes **what happens inside a case**. Case Boundary (P19H-3f) defines **whether a case should exist at all**. Without the boundary:

- Timeline and Brief **amplify** mistakes (phantom cases get polished briefs)
- Chen sees Workbench rows he cannot explain to the customer
- Customer thinks sending a photo = filing a claim
- Random WeChat traffic pollutes the claim queue

This is the Spark Driver equivalent of **accepting a delivery task** vs **receiving a random text**. Drivers do not get a new delivery from every message in the app.

### 2.2 Three customer mental models (must stay distinct)

| Model | Customer belief | System representation |
|-------|-----------------|----------------------|
| **Consultation** | 我在问陈总办公室问题 | No `claim` case; safe reply only |
| **Holding / 待确认** | 我发了点东西，但还没说要正式整理 | Attachment buffer or `wecom_media_intake`; **no** `service_lane=claim` |
| **Formal record** | 这次事故的资料正在整理，陈总会跟进 | `service_lane=claim` + Start Card acknowledged + timeline active |

**Invariant:** Customer must always know which model they are in. Broker must see the same model on Workbench.

### 2.3 What「formal case」means (product contract)

A **formal claim case** exists when **all** of:

1. Customer has **explicitly started** this accident record (see §4), **or** broker has promoted a holding buffer to formal (future Workbench action).
2. System has sent **Claim Start Card** (or equivalent) with disclaimer.
3. `service_lane=claim` row exists with `claim_started` timeline event.
4. Workbench shows status **记录中** (not 咨询中, not 待确认).

A formal case **does not** mean:

- Carrier FNOL filed
- Coverage confirmed
- Chen has reviewed
- Photos are classified into slots

Copy everywhere: **「记录 / 整理资料」≠「正式报案 / 已受理」**.

---

## 3. Current Behavior Audit (Code-Backed)

### 3.1 What creates a `service_lane=claim` case today

| Trigger | Code path | Creates claim case? | Trust assessment |
|---------|-----------|---------------------|------------------|
| `我要理赔` / `开始理赔` / `我撞车了` / … | `is_claim_guided_start_message()` → `ingest_claim_basics_message()` → `_create_claim_case()` | ✅ Yes | ✅ **Correct** — explicit intent |
| `新事故` / `重新理赔` | `is_explicit_claim_restart()` → new case | ✅ Yes | ✅ **Correct** — explicit restart |
| Narrative with accident facts (time/place/what) + claim markers | `should_route_claim_guided_workflow()` + `has_accident_basics_signals()` + `claim_intake` high confidence | ✅ Yes | ⚠️ **Risk** —「昨晚 Costco 被追尾了」contains `追尾` → case without「我要理赔」 |
| Injury quick-reply button (no open claim) | `ingest_claim_injury_quick_reply()` → `_create_claim_case()` | ✅ Yes | ⚠️ **Risk** — button tap alone starts case |
| Injury quick-reply with open claim | append to existing | ❌ No new | ✅ OK if case was properly started |
| Claim how-to / liability question | `ingest_claim_question_safe_reply()` | ❌ No | ✅ **Correct** |
| Random WeChat photo (no open claim) | `resolve_wecom_media_binding()` tier C | ❌ No claim case | ✅ **Correct** for claim |
| Random WeChat photo (unbound, legacy path) | `_find_or_create_unassigned_intake_case()` | ❌ No claim; creates `wecom_media_intake` | ⚠️ **Broker noise** — still a case row |
| WeChat photo + single open claim (tier A) | bind to existing claim | ❌ No new | ✅ OK if parent case is formal |
| H5 upload with signed token | binds to token `case_id` | ❌ No new | ✅ OK — controlled entry on existing case |
| Active claim basics continuation | append to open claim | ❌ No new | ✅ OK |

### 3.2 Key code evidence

**Explicit start markers** (`claim_basics.py`):

```python
CLAIM_GUIDED_START_MARKERS = (
    "我要理赔", "开始理赔", "我撞车了", "出事故了", ...
)
```

**Implicit start via narrative** (`claim_basics.py`):

```python
def should_route_claim_guided_workflow(...):
    ...
    if is_claim_guided_start_message(text):
        return True
    return has_accident_basics_signals(text)  # ← can create case without explicit start
```

**Injury button creates case** (`claim_basics.py`):

```python
if not case_id:
    created = _create_claim_case(normalized, injury_mentioned=(value == "yes"))
```

**Intent markers are broad** (`intent.py`):

```python
_CLAIM_MARKERS = (..., "追尾", "撞了", "事故", "理赔", "受伤", ...)
```

**Tier C photo — correct boundary** (`reply.py`):

```text
照片已收到。如果这是理赔相关，请简单回复「我要理赔」，我会帮您开始整理。
```

**Media quarantine case** (`media_intake.py`):

```python
# Creates service_lane=wecom_media_intake — NOT claim, but still a Workbench row
_find_or_create_unassigned_intake_case(...)
```

### 3.3 Gap summary

| Gap | Severity | Example |
|-----|----------|---------|
| Narrative auto-starts case | **High** | Customer vents「刚被追尾了，气死了」→ formal case |
| Injury button auto-starts case | **Medium** | Customer taps button from wrong context / mis-tap |
| `wecom_media_intake` rows look like work | **Medium** | Chen sees extra queue items for random photos |
| No customer-visible「已开始 / 未开始」state | **High** | Start Card reads like a form, not a boundary ceremony |
| No True End Card shipped for Claim | **Medium** | Customer unsure when Chen has「 taken over」 |
| Stage Complete C1 conflated with「done」 | **Medium** |「第 1 步完成」feels like filing progress (P19H-3e-R2 already flagged) |

---

## 4. Case Boundary Policy

### 4.1 When a formal claim case **MAY** be created

| # | Gate | Examples | Rationale |
|---|------|----------|-----------|
| G1 | **Explicit verbal start** | `我要理赔` · `开始理赔` · `我撞车了` · `出事故了` · menu `2` / `claim` | Customer names the task |
| G2 | **Explicit restart** | `新事故` · `重新理赔` · `another accident` | New accident boundary |
| G3 | **Holding confirm button** | After Holding ack, customer taps `[开始记录这次事故]` | Confirms ambiguous narrative |
| G4 | **Controlled task entry** | H5 opens from signed token on **existing** formal case | Token implies case already exists |
| G5 | **Broker promotion** (future) | Chen clicks「确认为本次事故正式记录」on Workbench | Human authority for edge cases |

**Rule:** G1/G2/G3 create case. G4 never creates — only appends. G5 is post-MVP broker tool.

### 4.2 When a formal claim case **MUST NOT** be created

| # | Situation | System behavior | Customer copy essence |
|---|-----------|-----------------|----------------------|
| B1 | Random photo, no open formal claim | Holding / tier C ack; store media; **no** `claim` case | 「照片已收到。如需整理理赔资料，请回复「我要理赔」」 |
| B2 | Casual chat / greeting | Generic assistant reply | No case |
| B3 | General insurance question | `claim_question_safe_reply` or coverage lane | 「这只是咨询，不代表开始理赔」 |
| B4 |「被追尾了怎么办」/「要不要报保险」 | Question path — no guided case | Safe advice + optional「开始记录」button |
| B5 | Narrative vent without start confirm | Holding — echo + confirm button | 「听起来像事故。您是要开始整理这次事故的资料吗？」 |
| B6 | Old accident photo / wrong image | Ack + do not bind to active case without confirm | 「这张照片我先记下。是这次事故的吗？」 |
| B7 | Photo during Add Vehicle | Lane switch prompt — no silent claim | Existing `claim_lane_switch` pattern |
| B8 | Multiple open claims ambiguous | Tier B broker confirm — no auto-bind | 「陈总会确认后整理」 |
| B9 | Injury mention in question context | Safe reply first; case only after G1/G3 | No case from「撞了怎么办」alone |
| B10 | Low-confidence intent | Menu or clarify — no case | No case on `unclear` |

### 4.3 Holding state (new product concept)

**Holding** = customer-visible pre-case buffer.

| Property | Value |
|----------|-------|
| Purpose | Acknowledge inbound without formal case |
| Storage | Prefer attachment metadata + optional short-lived buffer on `wecom_external_userid` (implementation in 3f-1; **no new DB table** — JSONB / existing media intake) |
| TTL | 24–72h; then broker sees orphan media or auto-expire |
| Customer label | **待确认** — not shown as「理赔 case」 |
| Promotion | Customer G1/G3 or broker G5 → bind buffered events to new `claim` case |

**Holding flows:**

```text
Customer: [photo only]
  → Holding ack (tier C)
  → Optional: [开始记录这次事故] [只是发错了] [联系陈总]
  → Only [开始记录] → Create formal case + bind photo

Customer: 昨晚被追尾了，气死了
  → Holding echo + confirm
  → [开始记录这次事故] [只是聊聊] 
  → Only [开始记录] → Start Card + case
```

### 4.4 Random message / photo decision table

| Inbound | Open formal claim? | Action | Creates `claim` case? |
|---------|---------------------|--------|---------------------|
| Text: 你好 | — | Greeting | ❌ |
| Text: 保费多少钱 | — | Policy / generic | ❌ |
| Text: 我要理赔 | — | G1 → Start Card + case | ✅ |
| Text: 昨晚被追尾了 | No | Holding + confirm (B5) | ❌ until confirm |
| Text: 昨晚被追尾了 | Yes (formal) | Append timeline | ❌ |
| Photo only | No | Tier C Holding (B1) | ❌ |
| Photo only | Yes (formal, tier A) | Bind + timeline | ❌ |
| Photo only | Yes (ambiguous, tier B) | Broker confirm ack | ❌ |
| Voice: 20s story | No | Holding stub + confirm | ❌ until confirm |
| Button: 没有受伤 | No | **Should require G3 first** (policy fix) | ❌ until confirm |
| Button: 没有受伤 | Yes | Append fact | ❌ |
| H5 upload | Token case exists | Append slot | ❌ |
| Wrong/old photo | Yes | Ack +「是这次事故的吗？」| ❌ new |

---

## 5. Start Card / End Card Trust Contract

### 5.1 Card taxonomy (Claim)

Learn from Add Vehicle P19E-0: **do not call intermediate milestones「End Card」**.

| Card | When | Customer meaning | Broker meaning |
|------|------|------------------|----------------|
| **Safety Card** | Before or at start; injury unknown | 「先确认安全」 | Urgency gate |
| **Claim Start Card** | Formal case created (G1/G2/G3) | **「事故记录已开始」** | New formal case; Chen queue |
| **Stage Complete Card** (C1…) | Milestone inside formal case | 「这一步记下了」| Phase advance — **not done** |
| **Progress Card** | Customer asks status | 「当前记录进度」| Query view |
| **Broker Review Card** | Materials sufficient for Chen | 「已转陈总确认」| `ready_for_broker_review` |
| **True End Card** | Chen confirms handoff (`broker_done`) | **「陈总已确认收到」** | Case closed for customer action |

### 5.2 Claim Start Card (redesigned contract)

**Job:** Answer「我是不是已经正式开始了？」with a clear **yes**, while denying filing implications.

**Required elements:**

1. **Boundary headline** — `【事故记录已开始】` (not only「理赔资料收集」)
2. **Safety** — injury check (buttons in 3e-1)
3. **One story ask** — time / place / what in one message
4. **Scribe framing** — 「我先帮陈总记录」
5. **Disclaimer** — `这不代表已经向保险公司正式报案`
6. **No H5 hero** on first message (P19H-3e-R2/R3)

**Target copy:**

```text
【事故记录已开始】

您好，我是陈总办公室的值班助手。

请先确认：您和车上的人现在都安全吗？
[没有受伤]  [有人受伤]  [不确定]

如果安全，请用一条消息告诉我：
大概什么时候、在哪里、发生了什么事。

我会先把信息记到这次事故记录里，陈总会人工确认后联系您。

这只是资料整理，不代表已经向保险公司正式报案。
```

**Customer state after Start Card:** `记录中 — 事故资料整理中`

**Broker Workbench label:** `Claim · 记录中` (not「新 case」without context)

### 5.3 Holding ack card (pre-Start)

When inbound is ambiguous (B5, B1):

```text
【尚未开始事故记录】

照片已收到 ✅

如果您想开始整理这次事故的理赔资料，请点下面按钮或回复「我要理赔」。
如果发错了或只是问问，不用理会这条。

[开始记录这次事故]
[联系陈总]
```

**Customer state:** `待确认 — 尚未开始正式记录`

### 5.4 Stage Complete vs End — customer language

| Shipped today | Problem | Target rename |
|---------------|---------|---------------|
| `【理赔资料 · 第 1 步完成 ✅】` | Sounds like claim filing steps | `【事故信息已记录 ✅】` |
| C1 H5 button hero | Implies photo upload = core task | `补充事故资料` secondary |
| (missing) | No terminal customer signal | **True End Card** at broker_done |

**Stage Complete C1 (inside formal case only):**

```text
【事故信息已记录 ✅】

时间：{accident_datetime}
地点：{accident_location}
经过：{accident_description}

您可以继续发微信补充或发照片，都会记到同一份记录里。
如需分步补充，可点下面「补充事故资料」。

这不代表理赔已提交，陈总会联系您确认。
```

### 5.5 True End Card (BrokerDone)

**Trigger:** `broker_confirmed_at` set OR `derive_claim_phase() == broker_done` — **Chen action only**, never auto.

```text
【本次事故记录 — 陈总已确认】

陈总已确认收到您这次事故的资料。
我们会通过电话或微信跟进后续步骤。

我们不能判断事故责任，也不能代替您向保险公司正式报案。
如有紧急情况，请直接联系陈总。
```

**Customer state:** `已交接 — 等待陈总跟进`  
**Broker state:** `BrokerDone` — case remains visible but not「collecting」

**Forbidden on End Card:** 已报案 · 理赔完成 · 保险公司已受理

### 5.6 Card send rules

| Rule | Detail |
|------|--------|
| Start Card once per formal case | Idempotent on `claim_started` timeline event |
| No Start Card on Holding | Holding uses pre-Start ack only |
| Stage Complete max 1 per milestone | No spam after every photo |
| Progress Card on inquiry only | Customer asks「进度」「还差什么」 |
| True End Card once | Idempotent on `broker_done` |
| Injury → manual handle | Safety ack replaces checklist; may skip to Broker Review Card |

---

## 6. Customer & Broker State Clarity

### 6.1 Customer-visible states

| State | Chinese label | When | What customer should understand |
|-------|---------------|------|--------------------------------|
| `idle` | （无） | No interaction | 还没开始任何事故记录 |
| `holding` | 待确认 | Photo / ambiguous text | 系统收到了，但还没开始正式记录 |
| `consultation` | 咨询中 | Question-only path | 只是问问题，不是理赔 |
| `recording` | 记录中 | After Start Card | 这次事故正在整理，陈总会确认 |
| `broker_review` | 待陈总确认 | Enough material | 资料已转陈总，等回电 |
| `handed_off` | 已交接 | True End Card | 陈总已确认收到，等跟进 |

**Channel invariant:** Same state whether customer uses WeChat, H5, or future mini-program — one formal case per accident.

### 6.2 Broker Workbench labels

| Today | Problem | Proposed |
|-------|---------|----------|
| `Claim` | Too generic | `Claim · 记录中` / `Claim · 待确认开始` |
| `WeCom Media Intake` | Jargon | `微信待分类` — **filter separate from Claim queue** |
| `Claim Lite` | Unclear boundary | `咨询备忘` — not formal claim |
| Phase only in JSON | Chen can't scan | Badge: **正式记录** vs **待确认** vs **咨询** |

**Claim drawer header (proposed):**

```text
李女士 · Claim · 记录中 · 昨晚 Costco 追尾
边界：正式事故记录（未报案） · 开始于 7/8 19:02
```

**Formal vs Holding indicator on Brief:**

```text
⚪ 待确认开始  →  no Start Card yet; broker should not treat as active claim
🟢 记录中      →  formal case; Brief is source of truth
🔵 已交接      →  broker_done; read-only customer-facing
```

### 6.3 What each party knows (trust matrix)

| Question | Customer knows via | Broker knows via |
|----------|-------------------|------------------|
| 我开始了吗？ | Start Card / Holding ack state label | `case_boundary_status` badge |
| 这张照片算进去了吗？ | Photo ack tier copy | Timeline + attachment count |
| 陈总在处理吗？ | Broker Review / End Card | Queue + phase |
| 这是正式理赔吗？ | Disclaimer on every card | Workbench「未报案」flag |
| 这是闲聊吗？ | No Start Card; consultation reply | Lane ≠ `claim` |

---

## 7. Interaction with P19H-3e Story Recorder

Case Boundary is **upstream** of Story Recorder:

```text
           ┌──────────────────────────────────────┐
           │  Case Boundary (P19H-3f)              │
           │  Holding · Consultation · Formal start  │
           └──────────────────┬───────────────────┘
                              │ only if formal
                              ▼
           ┌──────────────────────────────────────┐
           │  Story Recorder (P19H-3e)             │
           │  timeline · brief · injury buttons     │
           └──────────────────────────────────────┘
```

| P19H-3e feature | Boundary rule |
|-----------------|---------------|
| `claim_timeline[]` append | Only on **formal** case (or promote Holding → formal first) |
| `claim_case_brief` | Only for formal cases; Holding shows「待确认」stub |
| Injury quick replies | **After** formal start OR after Holding confirm — not auto-create |
| WeCom photo bind tier A | Only if parent case is formal |
| Workbench Brief hero | Hide or collapse for `holding` / `wecom_media_intake` |
| Hybrid interaction (R3) | Quick replies inside formal case; Holding gets confirm buttons only |

**No regression:** Tier C photo behavior (P19H-3d) is the **template** for boundary — extend to narrative auto-start.

---

## 8. Scenario Simulations

### 8.1 A — Customer formally starts

```text
Customer: 我要理赔
AI: 【事故记录已开始】Safety + injury buttons + story ask
System: service_lane=claim created · claim_started event
Chen: Workbench · Claim · 记录中
```

✅ Clear boundary.

### 8.2 B — Random photo first

```text
Customer: [damage photo]
AI: 【尚未开始事故记录】照片已收到 · [开始记录这次事故]
System: NO claim case · media in Holding
Customer: [开始记录这次事故]
AI: 【事故记录已开始】+ bind photo to new case
Chen: One formal case with photo on timeline
```

✅ Target behavior (partially shipped — tier C ack exists; confirm button not yet).

### 8.3 C — Casual narrative (current risk)

```text
Customer: 昨晚 Costco 被追尾了，气死了
TODAY: claim_intake (追尾) + has_accident_basics_signals → case created ❌
TARGET: Holding echo + [开始记录] [只是聊聊] → no case until confirm ✅
```

### 8.4 D — Insurance question

```text
Customer: 出事故了要不要报保险？
AI: claim_question_safe_reply — no case
Optional: [开始记录这次事故] at tail only
```

✅ Already correct (`ingest_claim_question_safe_reply`).

### 8.5 E — Wrong photo on active case

```text
Customer: [child's school photo] (formal claim open)
AI: 照片已收到。这是这次事故相关的吗？
System: attach with flag needs_broker_review; brief notes anomaly
Chen: deletes or ignores in Workbench
```

Defer auto-detection — broker review flag sufficient for pilot.

### 8.6 F — Chen closes loop

```text
Chen: Workbench → Confirm / Mark broker done
Customer: 【本次事故记录 — 陈总已确认】True End Card
System: broker_done · no more gap questions
Customer: 新事故
System: new formal case + new Start Card
```

---

## 9. Policy vs Shipped — Gap List

| Policy | Shipped? | Sprint to fix |
|--------|----------|---------------|
| Random photo → no claim case | ✅ Tier C | — |
| Explicit 我要理赔 → case | ✅ | — |
| Narrative without confirm → no case | ❌ | **P19H-3f-1** |
| Injury button without start → no case | ❌ | **P19H-3f-1** |
| Holding confirm button | ❌ | **P19H-3f-1** |
| Start Card boundary headline | ⚠️ Partial | **P19H-3f-1** copy |
| True End Card | ❌ | **P19H-3f-2** |
| Workbench boundary badge | ❌ | **P19H-3f-1** |
| Separate media intake queue filter | ⚠️ Partial | **P19H-3f-1** UI |
| Holding → formal promotion | ❌ | **P19H-3f-1** |

---

## 10. Core Doc / North Star / Test Integration

### 10.1 Documents to update (when implementing 3f-1)

| Doc | Addition |
|-----|----------|
| `docs/CURRENT_PRODUCT_SHAPE.md` | Case Boundary invariant + customer state table |
| `docs/goals/insurance_paid_pilot_goal.md` | Trust: no phantom cases |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Formal vs Holding vs Consultation |
| `docs/p19h0_claim_case_builder_state_machine_recon.md` | Cross-link §4 boundary gates as upstream of state machine |
| `AGENTS.md` | One-line boundary rule in scope guardrail |

### 10.2 North star addition (canonical)

```text
Case Boundary Invariant:
  Random chat and random photos do not create formal claim cases.
  A formal claim case begins only through explicit customer intent,
  Holding confirmation, or broker promotion.
  Start Card marks the beginning; True End Card marks broker handoff.
  "Recording" ≠ "filing".
```

### 10.3 Acceptance criteria (future tests)

| ID | Criterion | Verification |
|----|-----------|--------------|
| CB-1 | Random photo alone → no `service_lane=claim` | Unit: `ingest_wecom_media_message` tier C |
| CB-2 | `你好` → no case | Intent + slice test |
| CB-3 | `保费多少` → no claim case | Lane isolation |
| CB-4 | `被追尾了怎么办` → question path, no case | `ingest_claim_question_safe_reply` |
| CB-5 | `我要理赔` → exactly one claim case | Scenario sim |
| CB-6 | `昨晚被追尾了` (no start) → Holding, no case | **New** — 3f-1 |
| CB-7 | Holding → confirm → case + photo bind | **New** — 3f-1 |
| CB-8 | Injury button without case → no case until confirm | **New** — 3f-1 |
| CB-9 | Start Card contains disclaimer +「已开始」| Copy assert |
| CB-10 | `broker_done` → True End Card once | **New** — 3f-2 |
| CB-11 | Add Vehicle lane unaffected | Regression |
| CB-12 | Formal case append still works after start | Timeline + brief |

### 10.4 Scenario simulator additions

Extend `workflow_scenario_simulator.py` cases:

- `claim_holding_photo_no_case`
- `claim_narrative_no_auto_start`
- `claim_holding_confirm_then_start`
- `claim_injury_button_requires_start`

### 10.5 Future sprint map

| Sprint | Scope | Depends on |
|--------|-------|------------|
| **P19H-3f-1** | Holding state · narrative gate · injury button gate · Start Card copy · Workbench badge · tests CB-6–9 | This recon |
| **P19H-3f-2** | True End Card · broker_done trigger · customer handed_off state · CB-10 | 3f-1 |
| **P19H-3e-2** | Police/party quick replies · customer Progress Card | 3f-1 boundary |
| **P19H-3c-R5** | Phone summary | formal case only |

---

## 11. GO / HOLD / STOP

| Verdict | Scope |
|---------|-------|
| **GO** | Case Boundary trust contract as defined in this recon |
| **GO** | Holding state + confirm-before-create for narrative and injury button |
| **GO** | Start Card / True End Card semantic separation |
| **GO** | P19H-3f-1 as next boundary sprint |
| **HOLD** | Broker promotion UI (G5) · wrong-photo AI · Holding TTL automation |
| **HOLD** | Mini-program entry — same gates when built |
| **STOP** | Auto-create case from `has_accident_basics_signals` alone |
| **STOP** | Auto-create case from injury button without formal start |
| **STOP** | Treating `wecom_media_intake` as claim |
| **STOP** | OCR / ASR / fault / coverage / carrier filing in this recon |
| **STOP** | Production code in this recon |

---

## 12. Final Recommendation

### 12.1 Answers to prompt questions

| # | Question | Answer |
|---|----------|--------|
| 1 | When can we create a case? | Explicit start (G1/G2), Holding confirm (G3), broker promotion (G5) |
| 2 | When must we not? | Random photo, casual chat, questions, ambiguous narrative, low confidence — §4.2 |
| 3 | Random messages/photos? | Holding ack + optional confirm buttons; tier C for photos; no `claim` case |
| 4 | Start / End Card design? | Start = boundary ceremony「已开始」; End = broker handoff only; stage cards ≠ end — §5 |
| 5 | Customer & broker state clarity? | Six customer states + Workbench badges — §6 |
| 6 | Core docs / tests / sprints? | §10 north star + CB-1–12 + 3f-1/3f-2 map |

### 12.2 Strategic alignment

P19H-3e made the **inside** of a claim case excellent. P19H-3f protects the **door**:

```text
3e:  HOW to record the story (timeline + brief)
3f:  WHEN a story becomes a formal case (boundary + cards)
```

Without 3f, 3e's recorder can **mis-record** — polished briefs for accidents the customer never intended to file.

**User prediction confirmed:** Random chat/photo must not auto-create cases. Explicit intent or controlled entry only.

---

## Appendix A — Boundary Flow (ASCII)

```text
                    ┌─────────────────────────┐
                    │   WeChat / H5 / 小程序   │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        ┌───────────┐    ┌────────────┐    ┌──────────────┐
        │ Consultation│    │  Holding   │    │ Explicit start│
        │ (no case)  │    │ (pre-case) │    │ G1/G2/G3      │
        └───────────┘    └─────┬──────┘    └──────┬───────┘
                               │ confirm          │
                               └────────┬─────────┘
                                        ▼
                    ┌───────────────────────────────┐
                    │  FORMAL CLAIM CASE             │
                    │  Start Card · claim_timeline   │
                    │  Brief · Story Recorder        │
                    └───────────────┬───────────────┘
                                    │ broker_done
                                    ▼
                    ┌───────────────────────────────┐
                    │  True End Card · handed_off    │
                    └───────────────────────────────┘
```

---

## Appendix B — Code Files Referenced

| File | Boundary relevance |
|------|-------------------|
| `claim_basics.py` | Start markers, `should_route_claim_guided_workflow`, `_create_claim_case`, injury quick reply |
| `intent.py` | Broad `_CLAIM_MARKERS` — drives false-positive routing |
| `claim_extractors.py` | `has_accident_basics_signals` — implicit start risk |
| `media_intake.py` | Tier A/B/C binding, `wecom_media_intake` case creation |
| `claim_identity.py` | Append vs create vs broker_confirm |
| `reply.py` | Start Card copy, tier C ack, disclaimers |
| `slice.py` | Routing order: media → claim basics → question safe |
| `case_store.py` | `claim_started` timeline idempotency |
| `claim_workbench_display.py` | Phase labels — needs boundary badge |
| `DocumentIntakeInboxPage.tsx` | Lane display — separate Holding from Claim |

---

*P19H-3f complete. Product recon only. No production code. No deploy.*
