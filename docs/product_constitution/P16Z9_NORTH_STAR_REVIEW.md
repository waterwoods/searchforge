# P16-Z9 Phase 3 — North Star Review

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Reviewed:** P16-Z2/Z2.5 north star · Case Intelligence outline · Case Memory (Z5) · Role D findings

---

## Current North Star (canonical)

> **Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.**

**Source of truth:** `P16Z25_NORTH_STAR.md` (aligns with `CASE_INTELLIGENCE_MASTER_OUTLINE.md`)

**Product soul (companion, not replacement):**

> Unified Intake is the office's **working memory** for client obligations — not a chatbot, not a CRM, not a spell-checker.

---

## Pipeline North Star (architecture)

```
Customer Message → Understanding → Case → Timeline → Next Action → Follow-up → Outcome
```

| Stage | Sprint consensus | Status |
|-------|------------------|--------|
| Message | Text paste wedge; WeChat remains channel | ✅ Implemented |
| Understanding | P16-Y classification breadth | ✅ Engine strong |
| Case | case_store + draft engine | ✅ Implemented |
| Timeline | case_messages stored; Z6 thread UI | ⚠️ Partially deployed |
| Next Action | broker_next_step; Chinese gaps | ⚠️ Partial |
| Follow-up | append API; waiting_on manual | ⚠️ Backend ✅ UX/process ❌ |
| Outcome | Observation log; no product closure UI | ⚠️ Process only |

**Verdict:** Pipeline is **correct**. Do not remove Understanding or Timeline as explicit stages.

---

## Case Intelligence — what to update

| Finding (Y→Z8) | North Star impact | Update |
|----------------|-------------------|--------|
| Single-turn 88.6 avg (P16-Y) | "Under one minute" **holds** for Turn 1 | None |
| Multi-turn Y44/Y45 failures | "Office-executable" **fails** on corrections until merge shipped | Add footnote in MASTER_OUTLINE: *multi-turn requires append + summary merge* |
| Role D 60.7/75 memory, 68.9 reread | "Without re-reading WeChat" is **aspirational** for 3-day cases | Maturity model L5 scorecard, not north star change |
| Claims Turn 1 ready, Turn 2+ weak | Outcome stage needs **evidence fields** eventually | Defer product UI; document in maturity L6 |
| LLM path unverified | North star does not assume LLM | Keep rules-first in SSOT |

**Recommendation:** Keep north star sentence **unchanged**. Update `CASE_INTELLIGENCE_MASTER_OUTLINE.md` risks section only:

1. Building Next Action before Timeline UX → spell-checker trap (**still true**)
2. Marketing "3 days without WeChat" before Role D ≥80 (**new risk**, from Z7)
3. Treating Outcome as UI before observation log works (**still true**)

---

## Case Memory — what to update

P16-Z5 reframed memory as **visible + merged + trusted**:

| Z5 discovery | North Star adjustment |
|--------------|----------------------|
| Backend memory production-grade | North star is **not** "build memory service" |
| Broker memory UX ~41/100 | Continuity loop is part of north star delivery |
| Copy = exit | Add operational sub-loop to soul doc |

**Updated continuity loop (soul doc only):**

```
整理 → 复制发出 → [在等客户] → 客户回复 → 同案追加 → 看得见变了什么 → 再复制
```

This extends P16-Z2.5 soul without changing the one-sentence north star.

---

## Role D findings — what to update

| Role D finding | North Star implication |
|----------------|------------------------|
| 4/10 journeys need WeChat Day 3 | North star **minute** applies to Turn 1; multi-day is **L5 maturity** |
| D08 premium path gold | North star validated on **renewal/premium** wedge |
| D10/D07 payment/remove failures | North star **blocked** on those lanes until Z8 engine slice |
| waiting_on 0% auto | "Time-bound obligation" requires **broker SOP** + heuristic, not north star rewrite |
| Z6 thread UI +8 reread (estimated) | Timeline stage is **necessary** for north star perception |

**Recommendation:** Add to `CASE_INTELLIGENCE_MATURITY_MODEL.md` L5 definition:

> L5 achieved when Role D battery: avg reread ≥80, needs_wechat ≤2/10, with Z6 UI deployed.

---

## What should NOT change

| Item | Why |
|------|-----|
| Core sentence | Stable across Z2, Z2.5, Z3, Z5, Z7, Z8 |
| "Not a CRM/chatbot" positioning | Every sprint reaffirmed |
| Chaos → Case → Next Action ordering | Benchmark-aligned (Zendesk, Intercom, Linear) |
| Text-paste wedge | OCR-first rejected in Z0, Z3, Z8 |

---

## What should change (documentation only)

| Doc | Change |
|-----|--------|
| `CASE_INTELLIGENCE_MASTER_OUTLINE.md` | Add Z7 multi-day risk; Z8 memory domain pointers |
| `CASE_INTELLIGENCE_MATURITY_MODEL.md` | L5 gate = Role D thresholds |
| `P16Z25_PRODUCT_SOUL.md` | Add waiting_on + append beats in loop |
| `P16Z25_NORTH_STAR.md` | No text change — add cross-link to VALIDATION_OS |

---

## Consolidated North Star (approved)

**North star (unchanged):**

> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

**Success metric for 90 days (new, subordinate to north star):**

| Metric | Target | Battery |
|--------|--------|---------|
| Turn 1 paste → copy | <45s cancel wedge | Founder E2E |
| Single-turn intelligence | ≥88 avg | P16-Y |
| Multi-day broker-readable | reread ≥80, ≤2/10 need WeChat | Role D |
| Commercial proof | 3+ logged real multi-turn cases | Observation log |
| Paid pilot access | FP-004 off, cold URL | trial_launch_check |

---

*End of P16-Z9 Phase 3 — North Star Review*
