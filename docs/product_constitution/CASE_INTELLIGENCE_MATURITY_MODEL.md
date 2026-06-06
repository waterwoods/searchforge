# Case Intelligence Maturity Model

**Date:** 2026-06-02  
**Sprint:** P16-Z3 — Case Intelligence Master Plan  
**Constraint:** Strategic documentation only — no code, no deploy, no P17.  
**Sources:** P16-Y, P16-Z0, P16-Z2, P16-Z2.5, P16-X, P16-M, P16-N, P16-O, P16-Z3 archaeology.

---

## Purpose of this model

Answer one question for every investment:

> **Does this move a real office from chaos to a closed obligation — without rebuilding what already exists?**

This is a **commercial maturity** ladder (what Chen Kui experiences), not an engineering feature list. Scores reflect **deployed + taught** value, not backend-only capability.

**Scoring scale (current score):** 0–100 per level. Composite pilot readiness ≈ weighted average with L1–L4 weighted 2× for weeks 1–4.

---

## North Star alignment

```
Chaos → Understanding → Case → Timeline → Next Action → Follow-up → Outcome
```

| Maturity level | North Star stages covered |
|----------------|---------------------------|
| L1 Chaos → Case | Understanding + Case (atomic office moment) |
| L2 Case → Missing Information | Case completeness |
| L3 Case → Timeline | Timeline (thread + time + waiting) |
| L4 Timeline → Next Action | Next Action |
| L5 Follow-up → Outcome | Follow-up + Outcome |

---

## Level 1 — Chaos → Case

### Purpose

Turn an unreadable inbound (WeChat paste, screenshot text, email fragment) into **one named office object** the broker can point at: lane, urgency, human-readable summary — without the broker re-reading the paste to know *what this is*.

### Value

- **Broker:** Stops scanning 50 messages; gets「这是取消案 / 付款案 / 加车案」in one action.
- **Office:** Shared vocabulary — assistant and owner see the same case ID and category.
- **Commercial:** Payment trigger starts here; if L1 fails, broker never returns.

### Implementation status

| Component | Status |
|-----------|--------|
| `triage_conversation()` classification | **Implemented** — post-P16-Y breadth (cancel, payment, add-car, UW, address, coverage) |
| Urgency assignment | **Implemented** |
| `conversation_summary` intent line | **Implemented** |
| Case persistence (`case_store`) | **Implemented** |
| Chinese lane labels in UI | **Partial** — EN fragments in glance/queue |
| Trial URL access (FP-004 SSO) | **Blocking** — effective L1 = 0 until fixed |
| P16-Y battery single-turn | **88.6 avg** — L1 engine strong |

### Current score

| Lens | Score |
|------|-------|
| Engine | **88** |
| Deployed (product_only) | **72** |
| Chen Kui effective today | **45** (SSO + story misalignment) |

### Estimated effort to reach 90+ deployed

| Work | Effort | Owner |
|------|--------|-------|
| FP-004 off + redeploy | 5 min + 0.5 day | Founder + Dev |
| Chinese glance + cancel wedge copy | 0.5–1 day | Dev |
| P16-M TOP5 (demo demotion, trust line) | 0.5 day | Dev |
| Founder cold-URL E2E | 1 hour | Founder |

**Total:** ~2 days

### ROI

**★★★★★** — Highest. Every downstream level is worthless if L1 is inaccessible or slower than「直接回微信」. Revenue path: first supervised paste → copy → client reply.

---

## Level 2 — Case → Missing Information

### Purpose

After the case exists, the office must know **what is already true** and **what is still blocking action** — without opening the raw thread or carrier portal mentally.

### Value

- **Broker:** `还缺什么` replaces re-asking the client for policy number, notice screenshot, SR-22 proof.
- **Office:** Reduces duplicate outreach and compliance risk on cancel/UW deadlines.
- **Commercial:** Differentiates from「AI summary」— actionable gaps, not prose.

### Implementation status

| Component | Status |
|-----------|--------|
| `collected_fields` / `still_needed_fields` | **Implemented** — P16-Y missing info library (20 patterns) |
| `notice_image`, policy, deadline gaps | **Implemented** (rules) |
| Deadline → `still_needed` for cancel/UW | **Partial** — Y02 Chinese numeric gap |
| `bill_sent_claimed` (premium thread) | **Missing** — Y45 |
| Named insured / carrier extract | **Partial** — P2 gaps |
| Multi-turn gap merge on append | **Missing** — corrections drop prior facts (Y44) |
| Customer 提交补充 | **Hidden** on trial URL |

### Current score

| Lens | Score |
|------|-------|
| Engine (single-turn) | **82** |
| Engine (multi-turn) | **58** |
| Deployed glance「还缺什么」 | **75** |

### Estimated effort to reach 85+ deployed

| Work | Effort |
|------|--------|
| P16-Y P0 append summary merge | 1–2 days |
| deadline_mentioned → still_needed | 0.5 day |
| `bill_sent_claimed` heuristic | 0.5 day |
| Blocklist generic broker_next_step | 0.5 day |

**Total:** ~3 days

### ROI

**★★★★★** — Second-highest. Cancel wedge lives or dies on「还缺付款截图 / 还缺通知原件」. Directly reduces carrier-call mistakes.

---

## Level 3 — Case → Timeline

### Purpose

The case is not a snapshot — it is a **time-ordered obligation** with deadlines, waiting parties, and thread growth. Timeline answers: *what happened when, what is due when, who are we waiting on?*

### Value

- **Broker:** Sees「还有3天」without re-hunting emoji cancel text; knows if waiting on client vs carrier.
- **Office:** Prevents silent lapse on UW/cancel; supports assistant handoff without WeChat re-read.
- **Commercial:** Retention — Turn 2+ only makes sense if the **same case** accretes history.

### Implementation status

| Component | Status |
|-----------|--------|
| `deadline_mentioned` extraction | **Partial** — backend yes; UI widget weak |
| `waiting_on` field | **Implemented** — not prominent in glance |
| `case_status` / lifecycle derivation | **Implemented** |
| `case_activity` backend | **Hidden** — no trial timeline UI |
| Append / `triage_for_append` | **Implemented** backend |
| Append UX + post-copy CTA | **Missing / Hidden** — P16-X continuity 41/100 |
| Multi-turn summary merge | **Missing** — timeline intellectually wrong on corrections |
| Session / thread binding | **Implemented** |

### Current score

| Lens | Score |
|------|-------|
| Engine (data model) | **70** |
| Deployed continuity UX | **41** |
| Effective multi-turn office workflow | **50** |

### Estimated effort to reach 75+ deployed

| Work | Effort |
|------|--------|
| Post-copy append CTA + promote append on reopen | 1 day |
| waiting_on pill + deadline countdown in glance | 0.5–1 day |
| P16-Y P0 summary merge (timeline truth) | 1–2 days |
| Mark-sent / waiting state after copy | 0.5 day |

**Total:** ~3–4 days

### ROI

**★★★★★** for retention; **★★★★☆** for Day-0 payment. L3 is the difference between spell-checker popup and office assistant. Biggest gap vs North Star today.

---

## Level 4 — Timeline → Next Action

### Purpose

Given a case with time context, produce **one office-executable next beat** in Chinese — specific enough to copy to WeChat or call the carrier today, not generic「follow up with client.」

### Value

- **Broker:** `办公室下一步` + `复制给客户` = minutes saved per message (2–5 min measured P16-Y).
- **Office:** Aligns owner, assistant, and client on the same action.
- **Commercial:** This is what Chen Kui pays for — **time back**, not software.

### Implementation status

| Component | Status |
|-----------|--------|
| `broker_next_step` generation | **Implemented** — all 50 P16-Y cases pass actionability ceiling |
| `client_reply_draft` / copy-to-WeChat | **Implemented** |
| `client_prep` | **Hidden** — product_only gate |
| Chinese specificity (carrier, doc, deadline named) | **Partial** — templates needed |
| Generic fallback blocklist | **Partial** |
| Risk badge「需核实」| **Hidden** — v4 score computed, not shown |

### Current score

| Lens | Score |
|------|-------|
| Engine structure | **95** |
| Deployed Chinese specificity | **65** |
| Chen Kui trust on real paste | **70** |

### Estimated effort to reach 85+ deployed

| Work | Effort |
|------|--------|
| Category templates (cancel, payment, missing-doc, add-car) | 1 day |
| EN/ZH glance fix | 0.5 day |
| Surface v4 risk as optional badge | 0.5 day |
| Ungate client_prep (optional) | 0.5 day |

**Total:** ~2 days

### ROI

**★★★★★** — Wedge scenarios (cancel, payment, missing doc) monetize here. Must beat manual WeChat draft in **<45 seconds** paste-to-copy.

---

## Level 5 — Follow-up → Outcome

### Purpose

Close the loop: client replied → case updated → broker acted → obligation resolved or escalated — with **evidence** the office can use for payment and improvement.

### Value

- **Broker:** No lost follow-ups; second copy draft without re-paste entire thread.
- **Office:** Observation log → invoice → testimonial; optional customer status without calling.
- **Commercial:** Outcome proof unlocks second office and $50–100/mo renewal story.

### Implementation status

| Component | Status |
|-----------|--------|
| Append pipeline end-to-end | **Implemented** backend |
| Observation log process | **Partial** — template exists; **empty** |
| Invoice / payment IDs | **Partial** — docs complete; IDs empty |
| Customer 我的办理 tab | **Implemented** — week 3 exposure |
| Outcome / resolved enum | **Missing** |
| Verified resolution (Zendesk pattern) | **Missing** |
| Time-saved aggregate | **Missing** |
| learning_signals → product loop | **Hidden** |

### Current score

| Lens | Score |
|------|-------|
| Engine | **55** |
| Process / commercial | **15** |
| Deployed outcome UX | **25** |

### Estimated effort to reach 60+ (pilot-acceptable)

| Work | Effort |
|------|--------|
| Supervised Day 0 + Day 7 protocol | 3 hours founder |
| 10-row observation log discipline | Ongoing |
| Invoice sent + payment follow-up | 1 hour founder |
| Two-turn E2E logged on deployed URL | 1 hour |
| Customer tab (if broker asks) | 2–3 days |

**Total:** ~1 week process + optional 3 days product

### ROI

**★★★★☆** for first payment (process > code). **★★★★★** for month-2 expansion. Cannot skip — docs ≠ executed log.

---

## Maturity summary table

| Level | Transition | Purpose (one line) | Current score | To 85+ effort | ROI |
|-------|------------|-------------------|---------------|---------------|-----|
| **L1** | Chaos → Case | Name the obligation | 72 deployed / 45 Chen Kui | ~2 days | ★★★★★ |
| **L2** | Case → Missing Info | Know gaps without re-read | 75 deployed | ~3 days | ★★★★★ |
| **L3** | Case → Timeline | Thread + time + waiting | 41 UX / 70 engine | ~3–4 days | ★★★★★ |
| **L4** | Timeline → Next Action | Chinese executable beat | 65 specificity | ~2 days | ★★★★★ |
| **L5** | Follow-up → Outcome | Close loop + evidence | 25 overall | ~1 week | ★★★★☆ |

**Composite deployed maturity today:** **~58 / 100** (L1–L4 average, L5 excluded from week-1 gate)  
**Target day 30:** **~78 / 100** (L1–L4 ≥85, L5 ≥60 process)

---

## Investment rule

| If score < 70 at level N | Do not invest heavily in level N+2 until N is fixed |
|--------------------------|-----------------------------------------------------|
| L3 UX < 50 | Do not build customer portal or OCR-first — broker won't return |
| L5 process = 0 | Do not negotiate enterprise pricing — no proof |

---

## What NOT to count as maturity

| Fake progress | Why |
|---------------|-----|
| New microservice | Duplicates `triage.py` |
| P17 platform tab | Constitution block |
| LLM path without battery gate | Unverified |
| More demo scenarios | Competes with L1 on Day 0 |
| Full CRM / status admin | AMS already exists |

---

*End of Case Intelligence Maturity Model — P16-Z3*
