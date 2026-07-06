# P19D-1.6 — Pure WeCom Chat vs H5 Guided Task Page UX Recon

**Date:** 2026-07-06  
**Type:** Channel strategy / UX comparison recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19D implementation agents  
**Prerequisite:** P19A (media intake) ✅ · P19B (Workbench) ✅ · P19D-1 (strict chat guardrail) ✅ · P19D-1.5 (H5 UX simulation) ✅

**Core question:** If we **do not** build an H5 guided task page, can **pure WeCom/微信客服聊天** alone complete Insurance Case Builder intake — and what % of Spark Driver-style guided workflow does each approach reach?

**This loop:** No code. No deploy. No schema migration.

---

## 0. Executive Summary

Two architectures compared:

| | **A. Pure WeCom Chat** | **B. WeCom Chat + H5** |
|---|------------------------|-------------------------|
| **Photo capture** | Customer sends in chat; P19D-1 quarantine | H5 `count:1` + preview confirm |
| **Prevention model** | Reactive (triage after send) | Proactive (block before send) |
| **Spark-like (overall)** | **~35–45%** | **~75–85%** |
| **Spark-like (text steps)** | **~80%** | **~80%** (same — chat owns text) |
| **Spark-like (photo steps)** | **~15–25%** | **~75%** |
| **Broker cleanup load** | High on photo lanes | Low–medium |
| **Chen Kui pilot fit** | Demo / broker-handheld only | **Recommended production pilot** |

**Verdict:**

| Question | Answer |
|----------|--------|
| Pure chat as pilot? | **Conditional HOLD** — OK for **demo + text-heavy** paths; **not GO** as sole photo intake for paid pilot |
| Pure chat max risk | **Album bulk + wrong slot + privacy leak** — guardrail mitigates damage, not UX |
| Chat-only MVP must-have guardrails | P19D-1 ✅ + current-slot prompts + upload-intent buttons + one-flow rule + quarantine Workbench |
| Still recommend H5? | **Yes** — for any photo-proof slot in Add Vehicle / Premium / Claim / Coverage |
| Mini program timing | After H5 validates slot UX — not instead of H5 |
| Code / deploy | **No** |

---

## 1. Architecture Definitions

### 1.1 Scheme A — Pure WeCom Chat

```text
Customer ──► WeCom KF chat
               ├── text dialogue
               ├── Start Card / msgmenu buttons
               ├── images sent directly in chat thread
               └── backend: strict upload guardrail (P19D-1)
                        promote / quarantine / pause
                        case bind by external_userid
               ──► Workbench broker review
```

**What A has today (post P19D-1):** Media pipe, binding, quarantine badges, safe replies, lane intent, Start Card partial.

**What A cannot do:** Disable album multi-select; preview before server receive; enforce `current_slot` before shutter.

### 1.2 Scheme B — WeCom Chat + H5 Guided Task Page

```text
Customer ──► WeCom chat (entry, text, notify, trust)
               └── signed link ──► H5 one-slot wizard
                                    preview · confirm · slot bind
               ──► same backend GCS + case JSON
               ──► Workbench review
```

**Chat guardrail (P19D-1)** remains **safety net** for customers who ignore links and send chat images anyway.

---

## 2. Spark Driver Benchmark (What We Are Measuring)

Spark Driver guided loop:

```text
current task → current step → current object → single proof → verify → next
```

| Capability | Weight for insurance intake |
|------------|:---------------------------:|
| One active task / one flow | High |
| System prompts **only next gap** | High |
| **Single action** per proof step | High |
| **Verify before submit** (preview) | High |
| **Block bulk / wrong object** proactively | High |
| Exception branch (retry / manual) | Medium |
| Visible progress | Medium |
| Broker final review | High (already Workbench) |

Scoring uses weighted average: photo-heavy lanes weight proof steps more; text fields score similarly in A and B.

---

## 3. Per-Lane Analysis — Can Pure Chat Complete the Task?

“Complete” = broker receives enough **promoted** evidence to process the case without unacceptable manual recovery. Not “zero broker work.”

### 3.1 Add Vehicle (`add_car`)

| Requirement | Pure chat (A) | Chat + H5 (B) |
|-------------|:-------------:|:-------------:|
| Start / intent | ✅ Start Card | ✅ Same |
| VIN photo | ⚠️ Possible; high mis-slot risk | ✅ Strong |
| VIN text fallback | ✅ **Better in chat** | ✅ Chat |
| Registration photo | ⚠️ Often bulk-sent with VIN | ✅ Strong |
| Insurance card (opt) | ⚠️ | ✅ |
| delivery_date, zip, phone | ✅ **Chat ideal** | ✅ Chat |
| Broker can finish case? | **Yes, with cleanup** | **Yes, cleaner** |

**Pure chat completion verdict: YES — functionally completable,体验差.**

Typical pure-chat failure modes:

| Failure | Frequency (est.) | Guardrail effect |
|---------|:----------------:|------------------|
| Customer sends VIN + reg + old car photos in one album pick | High | 1 promote + N quarantine → customer confused |
| Registration photo bound to wrong slot | Medium | `unknown_document` → broker reclassify |
| Customer sends spouse's car photos | Medium | Wrong case if multi open → binding rules |
| Customer types VIN while bot asks for photo | Low | OK — text path exists |

**Spark % (Add Vehicle overall):** A **~40%** · B **~80%**

---

### 3.2 Premium Review (`policy_review`)

| Requirement | Pure chat (A) | Chat + H5 (B) |
|-------------|:-------------:|:-------------:|
| Intent + no-quote copy | ✅ | ✅ |
| Renewal notice / dec page photo | ⚠️ Multi-page → album dump | ✅ Sub-steps in H5 |
| Premium amount, renewal date text | ✅ **Chat ideal** | ✅ Chat |
| Vehicle context | ✅ Text | ✅ Chat |
| Broker can finish case? | **Yes if customer cooperates** | **Yes** |

**Pure chat completion verdict: YES for cooperative customers; fragile for document photo.**

Renewal notices are often **2–3 page photos** or PDF screenshots. Pure chat:

- Customer selects multiple pages at once → P19D-1 quarantine on pages 2–3
- Customer sends last year's notice → slot binding wrong, broker catches late
- Customer sends screenshot of email — single image OK

**Spark % (Premium overall):** A **~45%** · B **~75%**

---

### 3.3 Claim Lite (`claim_lite`)

| Requirement | Pure chat (A) | Chat + H5 (B) |
|-------------|:-------------:|:-------------:|
| Safety confirm (Start Card) | ✅ **Chat ideal** | ✅ Chat |
| Accident time, location, injury text | ✅ **Chat ideal** | ✅ Chat |
| Accident photos (multi) | ⚠️ P19D-1 allows 5/batch but **no preview** | ✅ Batch wizard with per-photo confirm |
| Police report (opt) | ⚠️ | ✅ |
| Broker can finish case? | **Yes — highest photo chaos** | **Yes** |

**Pure chat completion verdict: YES under stress, but worst UX and highest privacy risk.**

Claim is the lane where customers **most** bulk-upload (10+ scene photos). P19D-1:

- Promotes up to 5 per batch in `claim_lite`
- Quarantines 6+
- Cannot stop customer from including **unrelated personal photos** in album

**Spark % (Claim overall):** A **~30%** · B **~70%** (batch H5 wizard)

---

### 3.4 Coverage Risk (`coverage_risk`)

| Requirement | Pure chat (A) | Chat + H5 (B) |
|-------------|:-------------:|:-------------:|
| High-risk copy, no driving advice | ✅ **Chat critical** | ✅ Chat |
| DMV / cancellation notice photo | ⚠️ Single doc often OK | ✅ |
| Policy number, notice date text | ✅ Chat | ✅ Chat |
| "能开车吗" escalation | ✅ Chat keyword → manual | ✅ Chat |
| Broker can finish case? | **Yes — stakes high on wrong doc** | **Yes** |

**Pure chat completion verdict: YES for single-notice upload; unacceptable error cost if wrong image promoted.**

One photo of DMV notice is **the best-case** pure-chat photo step. Risk is not bulk but **wrong document** (registration sent instead of DMV letter) — no preview confirm in chat.

**Spark % (Coverage overall):** A **~50%** · B **~78%**

---

### 3.5 Lane summary table

| Lane | Pure chat completable? | Pure chat quality | H5 value add |
|------|:----------------------:|:-----------------:|:------------:|
| **Add Vehicle** | Yes | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Premium Review** | Yes | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Claim Lite** | Yes | ⭐ | ⭐⭐⭐⭐⭐ |
| **Coverage Risk** | Yes | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 4. Where Pure Chat Experience Is **Good Enough**

Pure chat is **the right or equal channel** for:

| Use case | Why A wins or ties B |
|----------|---------------------|
| **First contact / trust** | Customer already in 微信; "陈总会人工确认" |
| **Start Card / lane selection** | `msgmenu` tap — low friction |
| **Short text fields** | VIN typing, ZIP, date, phone, accident time/location |
| **Safety & emotional intake (Claim)** | Stay in chat after accident — don't send link first |
| **Coverage red-line copy** | Must not advise driving/coverage in any channel — chat is where questions appear |
| **Status notify / End Card** | KF push is natural return surface |
| **Human escalation** | "联系陈总" — chat native |
| **Secondary topic deferral** | B0 one-flow rule — chat message sufficient |
| **Cooperative customer, single careful photo** | One image + P19D-1 promote — broker effort low |
| **Broker-demo / hand-held walkthrough** | Chen Kui on phone: "请现在只发一张 VIN" — social guardrail supplements tech |

**Rule of thumb:** If the step is **language, intent, or consent** — pure chat is **≥80% Spark-like**. If the step is **camera proof** — pure chat is **≤25% Spark-like**.

---

## 5. Where Pure Chat Is **Not Enough**

| Gap | Platform limit | P19D-1 helps? | H5 fixes? |
|-----|----------------|:-------------:|:---------:|
| **Album multi-select** | WeChat native picker | Reactive quarantine | ✅ `count:1` |
| **Preview before send** | Image sends on picker confirm | ❌ | ✅ |
| **Bind slot before capture** | Server sees image after send | Partial (prompt text) | ✅ Token encodes `slot_id` |
| **Progress stepper UI** | Chat scroll buries steps | Copy only | ✅ Page header |
| **Block wrong doc type at capture** | No client UI | ❌ | Medium (slot-specific example image) |
| **Claim multi-angle without flood** | Chat encourages batch | 5-promote cap | ✅ Sequential wizard |
| **Privacy: unrelated photos in album** | User picks whole album | Quarantine after | ✅ Never offered multi |
| **Proactive "one step one image"** | Cannot enforce | Copy + punish after | ✅ Enforced in UI |

**Fundamental ceiling (documented in P19D-0.5):** WeCom chat is **reactive triage**, not **proactive prevention**. Customer experience under stress: *"I sent 12 photos and got a warning"* vs *"the page only let me send one."*

---

## 6. Risk Deep-Dive — Pure Chat Only

### 6.1 Multi-image mis-upload (多图误传)

| Scenario | A: Pure chat | B: + H5 |
|----------|:------------:|:-------:|
| Add car: 9 album photos | 1 promote, 8 quarantine, pause copy | Unlikely — H5 single pick |
| Premium: 3-page notice | Pages 2–3 quarantined | 3 H5 sub-steps or widened slot |
| Claim: 15 scene photos | 5 + 5 promote across batches if patient; else quarantine pile | Wizard with batch confirm |
| Customer retries after pause | More chat images → more quarantine | Returns to H5 link |

**Broker cost:** Quarantine review time scales with chat-image volume. Chen Kui pilot at **~5–15 min/case cleanup** vs **~2–5 min** with H5-primary.

### 6.2 Privacy mis-upload (隐私误传)

| Risk | A | B |
|------|---|---|
| Family photos in album batch | Stored to GCS before quarantine | Not selected |
| Child / unrelated ID in camera roll | Customer scroll-picks wrong thumb | Slot example reduces error |
| Old case photos resent | Bound to active case opportunistically | Token scoped to current case+slot |
| Sensitive non-insurance images | **Permanent GCS storage** even if quarantined | Lower incidence |

**Note:** Quarantine does **not** delete GCS objects (P19D-1 constraint). Privacy risk = **what gets uploaded at all**. Pure chat uploads more irrelevant bytes.

### 6.3 Slot binding errors (slot 绑定错误)

| Cause | A likelihood | B likelihood |
|-------|:------------:|:------------:|
| No `current_slot` UI — customer sends reg when asked for VIN | High | Low |
| Upload-intent button not tapped | Medium | N/A — link encodes slot |
| Out-of-order photos | High — opportunistic fill | Low — sequential |
| `unknown_document` default | Very common in A | Rare in B |
| Multi open cases → unassigned | Medium (binding rules) | Same for chat; H5 token validates case |

### 6.4 Old case / flow confusion (旧 case 混乱)

| Scenario | A | B |
|----------|---|---|
| Customer has open add_car + old claim | Binding ambiguity → unassigned or wrong case | Token tied to **active** case_id |
| Customer resumes after 2 weeks | Chat history long; re-sends old photos | New link for empty slot only |
| Customer starts new topic mid-flow | B0 deferral — OK in chat | Same |
| Holding `wecom_media_intake` case | Orphan photos accumulate | H5 bypasses holding lane |

**Pure chat amplifies** "everything in one thread" cognitive load — customer cannot see **which case** they are feeding.

---

## 7. Spark Driver Experience — Percentage Estimates

### 7.1 Methodology

Weighted by step type across a **representative Add Vehicle + Claim** mix:

| Step type | Share of customer effort | A score | B score |
|-----------|:------------------------:|:-------:|:-------:|
| Entry / Start | 10% | 85% | 85% |
| Text fields | 25% | 80% | 80% |
| Photo proof (normal slot) | 40% | 20% | 78% |
| Photo proof (claim batch) | 15% | 25% | 70% |
| Progress / orientation | 5% | 30% | 75% |
| Exception / human | 5% | 60% | 65% |

**Blended:**

| Architecture | Spark-like % | Interpretation |
|--------------|:------------:|----------------|
| **A — Pure chat** | **~35–45%** | Good messenger; poor proof camera |
| **B — Chat + H5** | **~75–85%** | Industry-standard broker pilot |
| **Native mini program (future)** | **~85–92%** | Best WeChat-ecosystem ceiling |
| **Spark native app** | 100% reference | Not comparable channel |

### 7.2 What pure chat **does** achieve

Pure chat + P19D-1 **fully achieves** Spark semantics for:

- ✅ One active business flow (B0)
- ✅ Broker final review gate
- ✅ Safe customer copy (no auto-policy-change)
- ✅ Finite lane intent (Start Card)

Pure chat **partially achieves**:

- ⚠️ One step one evidence (server-side only, customer feels punished not guided)
- ⚠️ Verify step (broker verifies, not customer preview)

Pure chat **cannot achieve**:

- ❌ Proactive bulk block
- ❌ Client-side preview confirm
- ❌ Task shell without context switch (H5 also has switch — but controlled shell)

---

## 8. If H5 Is Delayed — Minimum Chat Guardrails (Must-Have)

P19D-1 is **necessary but not sufficient** for chat-only pilot. Additional **chat-side** requirements (some design-only, some future implementation):

### 8.1 Already shipped (P19D-1) ✅

| Guardrail | Status |
|-----------|--------|
| Rolling 120s bulk detection | ✅ |
| Promote vs quarantine | ✅ |
| Claim 5-per-batch exception | ✅ |
| Customer safe copy (no OCR) | ✅ |
| Workbench quarantine badges | ✅ |
| `msg_id` dedup | ✅ P19A |

### 8.2 Must add for chat-only MVP (minimum)

| # | Guardrail | Purpose | Priority |
|---|-----------|---------|:--------:|
| 1 | **`current_slot_id` in case JSON** + bot prompts **only that slot** | Reduce binding errors | **P0** |
| 2 | **Upload-intent `msgmenu` buttons** per slot (`upload_vin_photo`, etc.) | Slot hint before image arrives | **P0** |
| 3 | **Explicit one-photo copy** before each photo step | Social prevention | **P0** |
| 4 | **Checklist-driven next prompt** (not generic ack) | Spark "next item" | **P0** |
| 5 | **E2 partial End Card** with `missing_list_zh` | Resume without confusion | **P1** |
| 6 | **「继续」intent** re-sends current slot instruction | Breakpoint resume | **P1** |
| 7 | **Broker Workbench: promote quarantine → slot** (manual) | Recovery path | **P1** |
| 8 | **Reject chat photos when H5 link active** (optional policy) | Force discipline | P2 |
| 9 | **Slot assignment on promote** from `current_slot_id` | Metadata accuracy | **P0** |
| 10 | **Activity log: quarantine reason visible to broker** | Faster triage | **P1** |

### 8.3 Chat-only MVP operating model

If H5 slips, Chen Kui pilot becomes **broker-assisted chat**:

```text
Bot:  strict prompts + guardrail
Customer:  often ignores one-photo rule
Broker:  daily quarantine triage + phone follow-up
```

**Acceptable only if:** pilot N < 30 customers, Chen Kui accepts **extra 10 min/case**, demo stakeholders understand this is **not** scaled product UX.

---

## 9. Side-by-Side Comparison Matrix

| Dimension | A: Pure Chat | B: Chat + H5 | C: Mini Program (future) |
|-----------|:------------:|:------------:|:------------------------:|
| Dev time to pilot | **Shortest** | Medium | Longest |
| Photo control | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Text intake | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Customer trust | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Broker cleanup | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Spark-like % | **~40%** | **~80%** | **~90%** |
| Privacy risk | High | Medium | Medium |
| Scales past pilot | ❌ | ✅ | ✅✅ |
| Depends on P19D-1 | Yes (only defense) | Yes (safety net) | Yes |

---

## 10. Decision Framework — Which Scheme When?

```text
                    photo-heavy?
                         │
            ┌────────────┴────────────┐
            NO                        YES
            │                         │
     Pure chat OK              Need guided surface
     (text lanes)                      │
                          ┌───────────┴───────────┐
                     pilot speed?            brand MP ready?
                          │                         │
                     H5 first ✅              Mini program
                     (B)                         (C)
```

| Situation | Recommendation |
|-----------|----------------|
| Demo next week, no H5 time | A + heavy broker coaching — **label as demo not product** |
| Chen Kui paid pilot (real customers) | **B** — H5 for every photo slot |
| Customer refuses links | A fallback with P19D-1 — expect quarantine |
| 6 months, proven volume | **C** — MP mirrors H5 slot machine |
| Text-only gap fill (phone, ZIP) | **A** always — no H5 needed |

---

## 11. Final Recommendations

### 11.1 Can pure chat serve as pilot?

| Pilot type | Verdict |
|------------|---------|
| **Internal demo / investor** | **GO (A)** — P19A+B+D-1 sufficient to show pipe + guardrail |
| **Chen Kui real customers, photo required** | **HOLD (A alone)** — use **B** or accept high broker tax |
| **Text-only intake week** (no photos) | **GO (A)** |
| **Claim-heavy week** | **NO (A)** — claim photos need H5 wizard |

**One-line:** Pure chat is a **valid demo pilot**, not a **valid photo-intake product pilot**.

### 11.2 Pure chat maximum risk

**Customer bulk-uploads sensitive unrelated images into GCS; guardrail quarantines but damage is done — broker loses trust, customer feels accused.**

Secondary: **slot mis-binding** → wrong VIN/reg on quote → rework before carrier submission.

### 11.3 Chat-only MVP must-have guardrails

Minimum beyond P19D-1:

1. `current_slot_id` + slot-scoped prompts  
2. Upload-intent buttons  
3. Checklist-driven next-step messages  
4. Slot metadata on promote from active slot  
5. Broker quarantine review workflow (Workbench)  

Without these, pure chat drops to **~25% Spark-like** on photo lanes.

### 11.4 Still recommend H5?

**Yes.** H5 is not optional for product-quality photo intake — it is the **shortest path** to proactive Spark-like proof steps. P19D-1 makes chat **safe**; H5 makes chat **smooth**.

Recommended stack:

```text
Now:     Chat (entry + text) + P19D-1 guardrail (chat photo safety net)
Next:    + H5 guided task (photo primary)
Later:   + Mini program (if metrics warrant)
Never:   Chat-only for scaled photo intake
```

### 11.5 Pure Chat vs Chat+H5 vs Mini Program

| Option | Recommendation |
|--------|----------------|
| **Pure Chat (A)** | Demo / text steps / fallback only |
| **Chat + H5 (B)** | **✅ Chen Kui pilot default** |
| **Mini Program (C)** | Post-pilot; copy H5 state machine |

---

## 12. Constraints This Loop

| Item | Status |
|------|--------|
| Code changed | **No** |
| Deploy | **No** |
| Schema migration | **No** |

---

## 13. GO / HOLD Summary

| Gate | Verdict |
|------|---------|
| Pure chat as **sole** photo pilot | **HOLD** |
| Pure chat as **demo** + broker-handheld | **GO** |
| Chat + H5 as paid pilot | **GO** |
| Defer H5, rely on P19D-1 only | **HOLD** — broker cost + privacy risk too high |
| This recon loop | **COMPLETE — STOP** |

---

## Appendix A — Example: Same Customer, Two Paths

**Customer:** 「我要加车，明天提车」

### Path A (pure chat)

```text
1. Start Card → tap 开始
2. Bot: 请发 VIN 照片（一次一张）
3. Customer selects 8 photos from album
4. P19D-1: 1 promoted, 7 quarantined, pause copy
5. Customer: 「我发了啊为什么说不行？」
6. Chen Kui: Workbench quarantine triage, 15 min
7. Phone call to get VIN again
8. Eventually complete — NPS ↓
```

### Path B (chat + H5)

```text
1. Start Card → tap 开始
2. Bot: [上传 VIN 照片] link
3. H5: one photo, preview, confirm
4. Chat: VIN 已收到，第 2 步 行驶证 [链接]
5. H5: registration confirmed
6. Chat: 请发提车日期和邮编（打字即可）
7. E1 收齐 → Chen Kui Workbench: 2 clean h5_task attachments
8. Broker review 5 min — NPS neutral/↑
```

---

*End P19D-1.6 — no code, no deploy.*
