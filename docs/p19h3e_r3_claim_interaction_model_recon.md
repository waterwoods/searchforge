# P19H-3e-R3 — Claim Interaction Model: Chat vs Buttons vs Task Card Recon

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** UX / product / implementation recon — **no production code, no deploy, no schema migration**  
**Prerequisite:** P19H-3e-R1 best practice · P19H-3e-R2 smooth UX · P19H-3e category strategy · P19H-3d human simulation · P19H-3c-R4 business value  
**Related:** `p19h3e_r2_claim_story_recorder_smooth_ux_recon.md` · `p19h3e_r1_claim_story_recorder_best_practice_recon.md` · `p19h3e_claim_case_builder_category_strategy_recon.md` · `p19h3d_r1_claim_human_simulation_workflow_simplification_recon.md` · `p19h3d_r0_claim_photo_intake_ux_simplicity_recon.md` · `p19h3c_r4_claim_workflow_business_value_alignment_recon.md`

---

## 1. Executive Summary

P19H-3e-R1/R2 established **what** to build (Claim Story Recorder + Case Builder) and **how smooth** it should feel (Spark Driver: one next action, complexity hidden). This recon answers **how customers should interact** in WeChat: pure chat, pure buttons, or hybrid?

**Answer: Hybrid — but asymmetric.**

| Layer | Role |
|-------|------|
| **Free chat / voice** | Narrative — time, place, what happened, emotional context |
| **Smart quick replies (2–3 buttons)** | High-risk structured facts — injury, police, other-party info, new vs same accident |
| **Photos / voice** | Natural attachments — no buttons, warm ack |
| **Lightweight progress card** | **Status reassurance only** — show once after basics, not after every message |
| **H5** | Optional supplement — never hero in normal flow |

**Not pure chat** — unstructured intake loses injury/police facts and creates Chen re-ask.  
**Not pure buttons** — feels like interrogation; narrative cannot be buttonized.  
**Not H5 wizard** — wrong channel at accident scene; contradicts WeChat-native category.

| Question | Answer |
|----------|--------|
| Best interaction model? | **Hybrid: chat + quick replies + sparse task card** |
| Pure chat or buttons? | **Neither alone** — chat for story, buttons for structured facts |
| Customer sees task card? | **Yes, once** after basics complete — not a form, not per-message |
| P19H-3e-1 includes quick replies? | **Option B** — injury quick replies only; full hybrid in 3e-2 |
| P19H-3e-1 core? | Timeline + Brief + Workbench hero + story copy — unchanged from R1/R2 |
| Verdict | **GO** hybrid model · **GO** 3e-1 timeline+brief · **HOLD** full quick-reply suite · **STOP** — no code in this recon |

**One-line thesis:**

> 故事用聊天收，关键判断用两三个按钮收，照片随手发，AI 每次只问一个问题 — 进度卡只用来安抚，不用来布置作业。

---

## 2. Interaction Model Comparison

### 2.1 Comparison table

| Model | Customer smoothness | Data accuracy | Stress friendliness | Duplicate risk | Implementation complexity | Fit for WeChat | Fit for Chen | Verdict |
|-------|--------------------:|--------------:|--------------------:|---------------:|--------------------------:|---------------:|-------------:|---------|
| **1. Pure free chat** | 9/10 | 5/10 | 8/10 | Medium | Low | ✅ Natural | ❌ Re-ask gaps | ❌ Reject as sole model |
| **2. Pure form / H5 wizard** | 3/10 | 8/10 | 2/10 | Low | Medium (exists) | ❌ Browser hop at scene | ✅ Structured | ❌ Reject as primary |
| **3. Button-first flow** | 4/10 | 7/10 | 3/10 | Low | Medium | ⚠️ OK for yes/no | ⚠️ Missing narrative | ❌ Reject as primary |
| **4. Chat + smart quick replies** | 8/10 | 8/10 | 8/10 | Low–Med | Medium | ✅ msgmenu click | ✅ Button-backed facts | ✅ **Core pattern** |
| **5. Chat + lightweight task card** | 7/10 | 6/10 | 7/10 | Low | Medium | ✅ Text card | ⚠️ Can feel like homework | ⚠️ Sparingly only |
| **6. Hybrid: chat + replies + task card** | **9/10** | **9/10** | **9/10** | Low | Medium–High | ✅ Best of all | ✅ Brief + provenance | ✅ **Recommended** |

### 2.2 Per-model deep evaluation

#### Model 1 — Pure free chat

| Criterion | Assessment |
|-----------|------------|
| Reduces cognitive load? | **Yes** — feels like talking to Chen's assistant |
| Improves data completeness? | **No** — injury/police often omitted; extraction errors |
| Avoids repeated upload? | **Partial** — ack copy helps; no structured dedup signal |
| Natural in accident context? | **Yes** — best for stressed narrative |
| Confusion with H5? | **Low** if H5 demoted |
| Chen clerical work? | **High** — must infer missing injury/police from prose |
| Incremental? | **Yes** — current path is mostly this |

**Verdict:** Good for **story only**; insufficient alone for broker-ready brief.

#### Model 2 — Pure form / H5 wizard

| Criterion | Assessment |
|-----------|------------|
| Reduces cognitive load? | **No** — 3-slot + browser = cognitive spike at scene |
| Improves data completeness? | **Yes** for photos; **No** for narrative |
| Avoids repeated upload? | **Yes** — slot state visible |
| Natural in accident context? | **No** — customer at roadside won't open browser |
| Confusion with H5? | **Is** the confusion (R2: three systems) |
| Chen clerical work? | **Low** for photos; **high** if customer abandons |
| Incremental? | **Already shipped** — demote, don't expand |

**Verdict:** Keep as **optional supplement** only.

#### Model 3 — Button-first flow

| Criterion | Assessment |
|-----------|------------|
| Reduces cognitive load? | **Only for yes/no** — fails on「怎么发生的」 |
| Improves data completeness? | **Structured fields yes**; story thin |
| Avoids repeated upload? | **Neutral** |
| Natural in accident context? | **No** — feels like IVR / government form |
| Confusion with H5? | **Medium** — another menu layer |
| Chen clerical work? | **Medium** — must phone for story |
| Incremental? | **Yes** — msgmenu click exists |

**Verdict:** Use buttons **surgically**, not as spine.

#### Model 4 — Chat + smart quick replies

| Criterion | Assessment |
|-----------|------------|
| Reduces cognitive load? | **Yes** — one tap for injury vs typing under stress |
| Improves data completeness? | **Yes** — button = explicit `known_facts` entry |
| Avoids repeated upload? | **Yes** — when combined with dedup ack |
| Natural in accident context? | **Yes** — chat frame + optional taps |
| Confusion with H5? | **Low** — buttons are in-chat, not browser |
| Chen clerical work? | **Low** — facts land in brief with source |
| Incremental? | **Yes** — WeCom `msgmenu` click pattern shipped (add_car, claim_contact_broker) |

**Verdict:** **Best ROI** for structured facts.

#### Model 5 — Chat + lightweight task card

| Criterion | Assessment |
|-----------|------------|
| Reduces cognitive load? | **Sometimes** — reassures「系统收到了」 |
| Improves data completeness? | **Indirect** — shows gaps may prompt customer |
| Avoids repeated upload? | **Yes** if card shows「照片：已收 3 张」 |
| Natural in accident context? | **Risky** — checklist vibe under stress |
| Confusion with H5? | **Medium** if card lists slot names |
| Chen clerical work? | **Low** — customer self-orients |
| Incremental? | **Yes** — text-only card first; no new infra |

**Verdict:** **Status card once**, not ongoing checklist.

#### Model 6 — Hybrid (recommended)

Combines 4 + 5 + free narrative + photo-as-attachment.

| Criterion | Assessment |
|-----------|------------|
| Reduces cognitive load? | **Yes** — right tool per fact type |
| Improves data completeness? | **Yes** — buttons for critical; chat for story |
| Avoids repeated upload? | **Yes** — dedup + progress ack |
| Natural in accident context? | **Yes** — matches how people talk after crash |
| Confusion with H5? | **Low** if H5 only in card tail as optional |
| Chen clerical work? | **Lowest** — brief has facts + sources |
| Incremental? | **Phased** — 3e-1 brief backbone; 3e-2 full hybrid UX |

**Verdict:** **Target end state.** Ship backbone first, layer interaction polish second.

---

## 3. Recommended Interaction Principle

### 3.1 Core principle (verified and refined)

```text
Use free chat for narrative.
Use quick replies for structured yes/no/unknown facts.
Use photos/voice as natural attachments.
Use a lightweight progress card only as status — not as a form.
Use H5 only for optional guided supplement.
AI asks exactly one question at a time.
Unknown is always a valid answer.
```

### 3.2 Decision matrix

| Question type | Open text / voice | Quick reply buttons | Rationale |
|---------------|:-----------------:|:-------------------:|-----------|
| Safety / injury | | ✅ | Highest priority; tap under stress |
| Accident narrative (when/where/what) | ✅ | | Cannot buttonize; one open prompt |
| Police involved | | ✅ | Small answer space; legally relevant |
| Other party info obtained | | ✅ | 3-way choice sufficient |
| New accident vs same accident | | ✅ | Identity disambiguation |
| Wants Chen contact now | | ✅ | Escape hatch |
| Location detail | ✅ | | Often in narrative; re-ask only if missing |
| Photo upload | ✅ (send) | ❌ |「直接发到这里」— no upload button nag |
| Fault / responsibility | ❌ | ❌ | Broker domain; defer |
| Coverage | ❌ | ❌ | Broker domain; redirect to Chen |
| Photo classification (which slot) | ❌ | ❌ | Chen/system deferred |

### 3.3 Specific answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Should AI ask open questions or buttons? | **Both — by fact type.** Story = open. Injury/police/party = buttons. |
| 2 | Which questions should be buttons? | Injury, police, other-party info, new-vs-same accident, contact Chen. |
| 3 | Which should be free text/voice? | Narrative, location detail, supplemental explanation, photos, voice. |
| 4 | Should customer see a progress card? | **Yes — once** after basics complete or when Chen would want reassurance. |
| 5 | Show checklist/progress to customer? | **Soft progress only** — no slot names, no ○/✅ homework. |
| 6 | Should H5 show in normal flow? | **No as hero.** Optional line after basics:「如需分步补充资料，可点下面按钮」. |
| 7 | Prevent repeated photo upload? | `msg_id` dedup + ack「不用重复发同一张」+ suppress H5 nag when photos on case. |
| 8 | Prevent wrong-case photo attachment? | Identity resolver tier A/B/C (shipped); tier B disambiguation buttons. |
| 9 | Prevent interrogation feeling? | One question max; echo facts; silence when enough; unknown OK. |

### 3.4 Anti-interrogation rules

1. **Never** stack button prompt on top of open story prompt in same message.
2. **Never** show more than **one** button group per turn.
3. **Always** allow free-text override — button tap and typed answer are equivalent.
4. **Echo before ask** —「已记录：昨晚 Costco 被追尾」then one gap question.
5. **Silence is valid** — when basics + injury known + photos received, stop asking.

---

## 4. Hybrid Flow Simulations

### 4.1 Canonical rear-end collision flow (target UX)

```text
Customer: 陈总，我被追尾了。

AI (text + msgmenu):
  请先确认安全：您和车上的人现在都安全吗？
  [没有受伤]  [有人受伤]  [不确定]

Customer taps: [没有受伤]

AI:
  好的，已记录：没有受伤 ✅
  请简单说一下什么时候、在哪里、怎么发生的。
  （一条消息即可，也可以发语音）

Customer: 刚才 7 点 Costco 停车场，我停车时被后面车撞了，后保险杠裂了。

AI:
  好的，已记录 ✅
  时间：刚才 7 点
  地点：Costco 停车场
  经过：停车时被后车追尾，后保险杠受损

  如果方便，可以直接发照片到这里，我会记到同一份记录里。

Customer: [photo] [photo] [photo]

AI:
  收到 3 张照片，已记到这份事故记录里 ✅
  不用重复发同一张。陈总会整理确认后联系您。

AI (one gap — buttons):
  请问当时报警了吗？
  [已报警]  [没报警]  [不确定]

Customer taps: [没报警]

AI (progress card — once):
  ─────────────────────
  事故记录进度
  ✅ 安全情况
  ✅ 时间地点经过
  ✅ 照片（3 张）
  ○ 对方信息（待补充）
  ─────────────────────
  信息已比较完整，陈总会联系您确认。
  如果想到其他细节，随时发到这里就行。

  [联系陈总]
```

**Note:** Progress card appears **once** at milestone — not after every message.

### 4.2 Scenario simulations

#### A — Rear-ended, no injury, photos available

| Dimension | Score | Notes |
|-----------|-------|-------|
| Smoothness | 9/10 | Injury button → story → photos → one police button → done |
| Data completeness | 9/10 | All P0 facts captured with sources |
| Confusion risk | Low | No H5 hero; one conversation |
| Quick replies help? | **Yes** — injury + police faster than typing |

**Flow time:** ~60 seconds customer active effort. Matches R2 CS-1.

#### B — Stressed customer at scene

| Dimension | Score | Notes |
|-----------|-------|-------|
| Smoothness | 8/10 | Photo-first OK; injury button critical before narrative |
| Data completeness | 7/10 | May skip location initially — one follow-up OK |
| Confusion risk | Low–Med | Must accept photos before basics without cold「我要理赔」 |
| Quick replies help? | **Yes** — injury tap while hands shaking |

**Special rules:**
- Photo before claim start → warm ack first, then safety buttons.
- No H5 push at scene.
- No progress card until calm (basics complete).

#### C — Photo-first customer

| Dimension | Score | Notes |
|-----------|-------|-------|
| Smoothness | 8/10 |「收到照片」→ safety buttons → story ask |
| Data completeness | 8/10 | Photos on timeline; story fills gaps |
| Confusion risk | Med if tier C cold start | Soft「如果这是理赔相关，我帮您记录」 |
| Quick replies help? | **Yes** for injury after photo ack |

**Copy:**
```text
照片已收到 ✅ 我先帮您记下。
请问您和车上的人都安全吗？
[没有受伤]  [有人受伤]  [不确定]
```

#### D — Voice-heavy customer

| Dimension | Score | Notes |
|-----------|-------|-------|
| Smoothness | 7/10 | Voice stub + optional text prompt |
| Data completeness | 6/10 in 3e-1 | No ASR — Chen listens; brief shows「语音待确认」 |
| Confusion risk | Low | Don't force text after voice |
| Quick replies help? | **After** voice — injury/police buttons still valuable |

**Rule:** Voice ack → stub timeline event → offer buttons for structured facts only.

#### E — Customer already spoke to Chen by phone

| Dimension | Score | Notes |
|-----------|-------|-------|
| Smoothness | 6/10 in 3e-1 | Redundant basics ask until phone summary ships |
| Data completeness | 7/10 | WeChat photos bind; phone story invisible |
| Confusion risk | Med | Customer repeats what she told Chen |
| Quick replies help? | **Neutral** — doesn't solve phone gap |

**Mitigation:** Brief shows timeline; phone summary in P19H-3c-R5. For 3e-1: accept redundancy gracefully —「好的，我帮您把微信里的信息也记下来」.

### 4.3 Simulation summary

| Scenario | Hybrid beats pure chat? | Hybrid beats button-first? |
|----------|-------------------------|----------------------------|
| A Calm rear-end | ✅ Injury/police buttons | ✅ Narrative richness |
| B Stressed at scene | ✅ Safety buttons | ✅ Photo-first accepted |
| C Photo-first | ✅ Post-photo safety | ✅ No upload wizard |
| D Voice-heavy | ✅ Structured follow-ups | ✅ No IVR feel |
| E Phone-first | ⚠️ Tie until phone summary | ✅ Still better than forms |

---

## 5. Quick Reply / Button Usage Rules

### 5.1 When to use quick replies

Use `msgmenu` **click** buttons only when **all** of:

1. Answer space is **small** (≤3 meaningful options + unknown).
2. Answer is **important** for brief / safety (injury, police, identity).
3. User is likely **stressed** (typing hard).
4. Buttons **reduce** typing without replacing narrative.

### 5.2 Good button questions

| Field | Buttons | `click.id` (proposed) |
|-------|---------|----------------------|
| Injury status | `[没有受伤]` `[有人受伤]` `[不确定]` | `claim_injury_none` / `_yes` / `_unknown` |
| Police involved | `[已报警]` `[没报警]` `[不确定]` | `claim_police_yes` / `_no` / `_unknown` |
| Other party info | `[有保险卡/驾照]` `[只有车牌]` `[没有拿到]` | `claim_party_full` / `_plate` / `_none` |
| Contact Chen | `[联系陈总]` | `claim_contact_broker` (exists) |
| New vs same accident | `[继续这起]` `[新事故]` | `claim_same_case` / `claim_new_case` |

### 5.3 Avoid buttons for

| Topic | Why |
|-------|-----|
| Accident narrative | Must be free-form |
| Location (if narrative incomplete) | Open prompt better |
| Long explanation | Buttons truncate |
| Photo classification | Wrong slot worse than unassigned |
| Fault / responsibility | Broker judgment |
| Coverage | Redirect to Chen |
| Multiple questions at once | Interrogation feel |

### 5.4 Button constraints

| Rule | Value |
|------|-------|
| Max buttons per prompt | **2–3** (+ optional 联系陈总 as escape) |
| Max button prompts in flight | **1** at a time |
| Free text fallback | **Always** — typed「没有受伤」= button tap |
| Mix with open ask | **Never** in same message |
| Unknown option | **Always** include for injury/police |

### 5.5 WeCom implementation mapping

**Existing infrastructure (verified in `reply.py`, `slice.py`, `send_msg.py`):**

| Capability | Status | Example |
|------------|--------|---------|
| `msgmenu` with `type: click` | ✅ Shipped | add_car Start Card, `claim_contact_broker` |
| `msgmenu` with `type: view` | ✅ Shipped | H5 `上传事故照片` |
| Click → intent routing | ✅ Shipped | `intent.py` start_add_car_click |
| Text fallback | ✅ Shipped | `build_h5_vin_start_text_fallback` |

**Proposed abstraction for Claim quick replies:**

```python
# Concept only — not production code in this recon
def build_claim_quick_reply_payload(
    *,
    head_content: str,
    buttons: list[tuple[str, str]],  # (click_id, label)
    tail_content: str = "",
) -> dict:
    return {
        "head_content": head_content,
        "list": [
            {"type": "click", "click": {"id": click_id, "content": label}}
            for click_id, label in buttons
        ],
        "tail_content": tail_content,
    }
```

**Intent handling:** Map `claim_injury_*` clicks → `known_facts.injury_status` + timeline event `customer_button_answer` with `source_ref`.

**Fallback:** If msgmenu unavailable, plain text with numbered options — same as add_car fallback pattern.

---

## 6. Lightweight Task Card Decision

### 6.1 Example card (customer-facing)

```text
【事故记录进度】

✅ 安全情况
✅ 时间地点经过
○ 对方信息
✅ 照片（3 张）

您可以继续直接发微信，或等陈总联系。
```

### 6.2 Decision

| Question | Answer |
|----------|--------|
| Should this appear to customer? | **Yes — sparingly** |
| When? | **Once** after `accident_basics_complete` OR when customer asks「还要什么」 |
| Helpful or too much? | Helpful as **reassurance**; harmful if every turn |
| Workbench-only? | **No** — customer benefits from「系统收到了」 |
| Replace H5? | **No** — H5 remains optional supplement in card tail |
| Only after basics complete? | **Yes** — never before first story captured |
| Avoid checklist pressure? | **Yes** — no slot names; max 4 lines; no ○ guilt for optional items |

### 6.3 What NOT to show

| Avoid | Why |
|-------|-----|
| `customer_damage_photo` slot names | Internal jargon |
|「第 2 步 / 共 4 步」| Wizard anxiety |
| Card after every photo ack | Noise |
| Card before injury confirmed | Wrong priority |
| Equal weight H5 button in card head | Three-systems regression |

### 6.4 Workbench vs customer card

| Surface | Content |
|---------|---------|
| **Customer card** | 4 soft milestones: 安全 / 经过 / 对方 / 照片 |
| **Workbench Brief** | Full `missing_info[]`, `next_best_question`, timeline, photo count |

Customer card is **subset** of brief — never the source of truth for Chen.

### 6.5 Phasing

| Sprint | Task card |
|--------|-----------|
| P19H-3e-1 | **Defer** — brief on Workbench first |
| P19H-3e-2 | **Ship** — one milestone card after basics |

---

## 7. Data Quality Strategy

### 7.1 How to get accurate info without forms

| Layer | Mechanism |
|-------|-----------|
| **Narrative capture** | Free text/voice → timeline `customer_message` → keyword extraction to `key_facts` |
| **Structured capture** | Button tap → `known_facts` with `source: button` + high confidence |
| **Echo correction** | AI repeats extracted facts; customer can correct in next message |
| **Unknown valid** | `injury_status: unknown` — never re-ask same turn |
| **One next question** | `next_best_question` from gap priority engine (R1) |
| **Event sourcing** | Every inbound → `claim_timeline[]` append |
| **Brief recompute** | `build_claim_case_brief()` on every event |
| **Source references** | Timeline event ID on each fact in brief |
| **Conflict handling** | New fact vs old → brief shows conflict; Chen resolves |

### 7.2 Quality invariants

| Invariant | Implementation |
|-----------|----------------|
| User identity correct | Identity resolver tier A/B/C (shipped) |
| Same accident case | Single open claim <72h; tier B disambiguation |
| No duplicate messages | `wecom_msg_id` idempotency (shipped) |
| No repeated uploads | Dedup ack + H5 nag suppression (R7) |
| No wrong claim attachment | Tier B blocks auto-bind; broker confirm |
| No hallucinated facts in brief | Deterministic extraction in 3e-1; only cite timeline sources |
| Chen can verify source | Timeline + `source_ref` per fact; last 3 events in brief |

### 7.3 Fact confidence model

| Source | Confidence | Brief display |
|--------|------------|---------------|
| Button tap | **High** |「受伤：没有受伤」 |
| Customer text keyword | **Medium** |「受伤：待确认（客户提到'没事'）」 |
| Extracted from narrative | **Medium** | Show value +「待陈总确认」 |
| Inferred / missing | **None** | `missing_info[]` only |

### 7.4 Gap priority (unchanged from R1)

```text
P0 injury → P1 time → P1 location → P2 other party → P3 photos (soft)
```

Button questions align to P0–P2 gaps. Photos never forced via button.

---

## 8. Anti-confusion / Anti-duplicate Rules

### 8.1 Rule table

| # | Situation | Recommended behavior | Copy |
|---|-----------|---------------------|------|
| 1 | Same photo twice | `msg_id` dedup; same warm ack |「这张照片已经记下了，不用重复发。」 |
| 2 | Multiple photos quickly | Batch ack with count |「收到 {n} 张照片，已记到这份事故记录里 ✅」 |
| 3 | Photo before「我要理赔」 | Warm ack → safety buttons → story |「照片已收到 ✅ 如果这是理赔相关，我帮您记下来。请问您和车上的人都安全吗？」 |
| 4 | Multiple open claims | Disambiguation buttons |「您有不止一起进行中的记录。[继续上一起] [新事故]」 |
| 5 | H5 then WeChat photos | Merge to same case; suppress H5 nag |「微信照片已记下，不用再点按钮上传。」 |
| 6 | Voice then text same story | Both on timeline; don't re-ask |「好的，文字和语音我都记下了。」 |
| 7 | New accident | Explicit button |「好的，我帮您开始一份新的事故记录。」 |
| 8 | Coverage/fault question | Redirect — no buttons |「理赔范围和责任需要陈总根据保单判断。我先帮您记录事故，陈总会联系您。」 |
| 9 | Wants human Chen | Immediate handoff |「好的，您可以点下面「联系陈总」或直接拨打陈总电话。紧急情况请先拨打 911。」 |

### 8.2 Photo attachment safety

```text
Tier A (single open claim):     auto-bind → timeline photo event
Tier B (multiple claims):       ask [继续这起] [新事故] before bind
Tier C (no claim):              quarantine → ack → start claim flow
```

### 8.3 Voice + text dedup

- Same story in voice + text → **two timeline events**, brief merges facts.
- Do **not** ask customer to repeat story in text after voice.
- Brief note:`语音 1 条（待陈总确认）`.

---

## 9. P19H-3e-1 Impact

### 9.1 Options evaluated

| Option | Scope | Risk | Effort | Smoothness impact | Brief distraction |
|--------|-------|------|--------|-------------------|-------------------|
| **A** | Timeline + brief only; quick replies later | Low | Focused | 7/10 | None — core deliverable |
| **B** | + injury quick replies only | Low–Med | +1–2 days | 8/10 | Minimal |
| **C** | Full hybrid quick replies | Med | +3–5 days | 8.5/10 | Splits sprint focus |
| **D** | + lightweight task card | Med | +2 days | 7.5/10 | Card without brief = hollow |

### 9.2 Recommendation: **Option B**

**P19H-3e-1 = timeline + brief + Workbench hero + story copy + injury quick replies only.**

| Reason | Detail |
|--------|--------|
| **Risk** | Injury is P0 safety; button-backed fact highest value / lowest scope |
| **Effort** | Reuses existing `msgmenu` click pattern; 3 buttons + intent map |
| **Smoothness** | Big win for Scenario B (stressed at scene) |
| **Brief focus** | Injury lands in `key_facts` with source — directly feeds brief |
| **Defer** | Police/party buttons, task card, auto-send gap question → 3e-2 |

### 9.3 What P19H-3e-1 should build (refined)

**Must include (from R1/R2, unchanged):**

1. `claim_timeline[]` append + dedup
2. Text / image / voice stub timeline events
3. `build_claim_case_brief()` deterministic
4. `key_facts` + `missing_info` + `next_best_question`
5. Workbench `ClaimCaseBriefPanel` hero
6. Story-centric copy patch (no H5 hero on first message)
7. Evidence checklist collapsed by default
8. Photo count in brief (decoupled from slots)
9. Tests

**Add from R3 (injury quick replies only):**

10. Safety prompt with `msgmenu` click: `[没有受伤]` `[有人受伤]` `[不确定]`
11. Intent handlers → `known_facts.injury_status` + timeline `customer_button_answer`
12. Free-text injury keywords still work (no regression)
13. `manual_handle` path on `[有人受伤]` — existing safety gate

**Defer to P19H-3e-2:**

- Police / other-party quick replies
- Customer-facing progress card
- Auto-send `next_best_question` to customer
- Full timeline UI

---

## 10. Final Recommendation

### 10.1 Interaction model verdict

| # | Question | Answer |
|---|----------|--------|
| 1 | Best interaction model? | **Hybrid: chat + smart quick replies + sparse task card** |
| 2 | Pure chat or buttons? | **Neither alone** — asymmetric hybrid |
| 3 | Where should buttons be used? | Injury, police, other-party info, case disambiguation, contact Chen |
| 4 | Where should free text/voice be used? | Narrative, supplemental detail, photos, voice messages |
| 5 | Should customer see a task card? | **Yes, once** after basics — 3e-2; not per-message |
| 6 | How to prevent duplicate/repeated info? | `msg_id` dedup + batch photo ack + H5 nag suppression + echo |
| 7 | How to keep data accurate? | Button-backed P0 facts + timeline sourcing + echo + unknown OK + brief recompute |
| 8 | Should quick replies be in P19H-3e-1? | **Injury only (Option B)** — not full hybrid |
| 9 | What exactly should P19H-3e-1 build? | Timeline + Brief + Workbench hero + story copy + **injury quick replies** |
| 10 | GO/HOLD/STOP? | **GO** 3e-1 · **HOLD** full hybrid UX to 3e-2 · **STOP** form-first / FNOL / OCR / ASR gates |

### 10.2 GO / HOLD / STOP

| Verdict | Scope |
|---------|-------|
| **GO** | Hybrid interaction model as north star |
| **GO** | P19H-3e-1: timeline + brief + hero + copy + injury buttons |
| **HOLD** | Police/party buttons, customer task card, auto-gap-ask → 3e-2 |
| **HOLD** | H5 as optional supplement only — demote in copy |
| **STOP** | Pure button flow, H5 wizard as primary, slot checklist as customer UX |
| **STOP** | OCR, ASR required path, fault/coverage bots, production code in this recon |

### 10.3 Strategic alignment

This recon **confirms** R1/R2 direction and **adds** interaction-layer specificity:

```text
R1/R2:  WHAT to build (timeline + brief)
R3:     HOW customers interact (hybrid, phased)
```

User prediction **confirmed:** 自由聊天收故事 + 快捷按钮收关键判断 + 轻量进度卡少量出现.  
P19H-3e-1 scope **refined:** timeline + brief first, **injury quick replies bundled** — not full hybrid.

---

## Appendix A — Interaction Model ASCII

```text
                    ┌─────────────────────────────────┐
                    │         Customer WeChat          │
                    └─────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
    ┌───────────┐              ┌─────────────┐              ┌───────────┐
    │ Free text │              │ Quick reply │              │ Photo /   │
    │ + voice   │              │ buttons     │              │ voice att │
    └─────┬─────┘              └──────┬──────┘              └─────┬─────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      ▼
                    ┌─────────────────────────────────┐
                    │      claim_timeline[] append       │
                    │      (idempotent, sourced)         │
                    └─────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │    build_claim_case_brief()        │
                    │    key_facts + missing_info        │
                    └─────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
          ┌─────────────────┐               ┌─────────────────┐
          │ Customer:        │               │ Chen Workbench:  │
          │ one question OR  │               │ Brief hero 10s   │
          │ milestone card   │               │ timeline + gaps  │
          │ (sparse)         │               │                  │
          └─────────────────┘               └─────────────────┘
```

---

## Appendix B — Code Evidence

| File | Relevant today | R3 implication |
|------|----------------|----------------|
| `reply.py` | `msgmenu` click + view; claim C1 H5 hero | Add injury click buttons; demote H5 |
| `claim_basics.py` | Text → `known_facts`; C1 builder | Wire button → `injury_status` |
| `media_intake.py` | Image bind + dedup | Batch ack copy; timeline event |
| `claim_identity.py` | Tier A/B/C | Disambiguation buttons for tier B |
| `claim_workbench_display.py` | Evidence summary only | Brief shows button-sourced facts |
| `slice.py` | msgmenu reply routing | New claim_injury_* intents |

---

*P19H-3e-R3 complete. UX recon only. No production code. No deploy.*
