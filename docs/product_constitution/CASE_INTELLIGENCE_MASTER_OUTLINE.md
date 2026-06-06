# Case Intelligence Master Outline

**Date:** 2026-06-02  
**Sprint:** P16-Z3 — Case Intelligence Master Plan  
**Status:** **Single Source of Truth** for Unified Intake product architecture (strategic layer).  
**Constraint:** Describes what exists, what to wire, what to defer — not a build spec for P17.

---

## Deepest product truth (3-year horizon)

If Unified Intake survives, its true product is:

> **A working memory for client obligations** — every inbound message becomes a durable office obligation with time, gaps, next beat, and proof of closure, without replacing WeChat or the AMS.

Not: AI platform · CRM · insurance software · intake system.

---

## North Star pipeline (authoritative)

```
Customer Message
      ↓
Understanding
      ↓
Case
      ↓
Timeline
      ↓
Next Action
      ↓
Follow-up
      ↓
Outcome
```

### North Star review

| Question | Verdict |
|----------|---------|
| **Is this correct?** | **Yes** — matches Zendesk→Linear benchmark pipeline and P16-Y office workflow. |
| **Add** | **Understanding** as explicit stage (classification + urgency before case ID matters); **Timeline** as explicit stage (not implicit in Case). |
| **Remove** | Nothing — do not collapse Timeline into Case or skip Understanding. |
| **Risks** | (1) Building Next Action before Timeline UX → spell-checker trap. (2) Treating Outcome as product UI before observation log works. (3) Skipping Understanding to chase OCR/doc intelligence. |

**One-sentence North Star:**  
> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

---

## Architecture by layer

### Layer 0 — Customer Message (ingress)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Accept chaos without forcing structure first |
| **Current status** | **Implemented** — broker text paste; customer message-first (P16-O); attachment partial |
| **Missing pieces** | Inline image paste UI; voice/PDF primary path |
| **Hidden capabilities** | Inline image on triage API (`inboxTriage.ts` type, no UI caller); `CustomerEntryTab` multi-turn |
| **Duplicated work** | Multiple demo pack runners; SimulationAssistant orphan |
| **Highest ROI improvement** | **FP-004 SSO off** — without ingress, all layers are zero |

**Owner modules:** `BrokerWorkbenchTab.tsx`, `CustomerEntryTab.tsx`, `routes/inbox_triage.py`

---

### Layer 1 — Understanding

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Name lane + urgency before office commits attention |
| **Current status** | **Implemented** — post-P16-Y classification breadth; urgency on all paths |
| **Missing pieces** | LLM path parity unverified; mixed-intent in summary |
| **Hidden capabilities** | `secondary_issue_note`; assist_layer (env-gated) |
| **Duplicated work** | Do not build CaseIntelligenceService — extend `triage.py` |
| **Highest ROI improvement** | Chinese category labels in glance; cancel wedge copy alignment |

**Owner modules:** `triage.py` (`triage_conversation`, classifiers), P16-Y configs

---

### Layer 2 — Case

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Durable record: collected facts, gaps, summary, case ID |
| **Current status** | **Implemented** — `case_store`, v4 draft bundle, persistence |
| **Missing pieces** | Multi-turn summary merge (P16-Y P0); `bill_sent_claimed`; named insured |
| **Hidden capabilities** | Full draft card in API; `case_usable` / `handoff_ready` milestones |
| **Duplicated work** | Rubric "Case Distillation" ≠ separate service — same engine |
| **Highest ROI improvement** | Append summary merge — fixes case truth on corrections |

**Owner modules:** `case_draft_engine.py`, `case_store.py`, `intake_engine.py`

---

### Layer 3 — Timeline

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Ordered thread, deadlines, waiting parties, append history |
| **Current status** | **Partial** — backend strong; **UX 41/100** (P16-X) |
| **Missing pieces** | Post-copy CTA; prominent `waiting_on`; deadline widget; activity UI |
| **Hidden capabilities** | `case_activity` backend; `session_store`; `triage_for_append` complete |
| **Duplicated work** | Re-paste as new case vs append — UX teaches wrong path |
| **Highest ROI improvement** | Post-copy:「客户回复了？追加到此案件」+ summary merge |

**Owner modules:** `triage_for_append`, `append_follow_up_message`, lifecycle in `case_lifecycle.py`

---

### Layer 4 — Next Action

| Attribute | Detail |
|-----------|--------|
| **Purpose** | One office-executable beat + client draft to copy |
| **Current status** | **Implemented** structure; **Partial** Chinese specificity |
| **Missing pieces** | Category templates; generic blocklist; client_prep ungated |
| **Hidden capabilities** | v4/v5 risk scores; `client_prep` behind product_only |
| **Duplicated work** | Re-tuning LLM generation path — rules at 88.6 sufficient |
| **Highest ROI improvement** | Chinese `broker_next_step` naming carrier/doc/deadline |

**Owner modules:** `triage.py` templates, `reply_template_composer.py`, glance UI

---

### Layer 5 — Follow-up

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Client replied → same case → updated action |
| **Current status** | **Backend implemented**; **follow-up discoverability broken** |
| **Missing pieces** | Append on first session; mark-sent workflow; customer 提交补充 on trial |
| **Hidden capabilities** | Customer append flow; follow-up editor (dev-gated) |
| **Duplicated work** | None on API — pure UX/process gap |
| **Highest ROI improvement** | Supervised Day 0 teaching append + observation log append metric |

**Owner modules:** append route, `BrokerWorkbenchTab` reopen flow

---

### Layer 6 — Outcome

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Proof of resolution, time saved, payment, testimonial |
| **Current status** | **Missing** in product; **Partial** in process docs |
| **Missing pieces** | Observation log rows; outcome enum; time-saved field; verified resolution |
| **Hidden capabilities** | `learning_signals.jsonl`; `audit_export` stub (ignore) |
| **Duplicated work** | Re-investigating commercial pack — P16-K complete |
| **Highest ROI improvement** | Execute observation log + invoice — founder, not sprint |

**Owner modules:** `docs/trial/TRIAL_OBSERVATION_*`, manual payment templates

---

## System map (code truth)

```
services/fiqa_api/inbox_triage/   (~48 modules)
        │
        ├── triage.py              ← Understanding + Case + Next Action
        ├── case_draft_engine.py   ← Case packaging + risk
        ├── case_store.py          ← Persistence + append
        ├── case_lifecycle.py      ← Timeline state
        ├── image_input_pipeline   ← Document intel (L6, deferred)
        └── routes/inbox_triage.py ← HTTP surface

ui/src/.../BrokerWorkbenchTab.tsx  ← Deployed soul (paste → glance → copy)
ui/src/.../CustomerEntryTab.tsx    ← Week 3+ soul
```

**Rule:** No new microservices. Extend existing modules only.

---

## Duplication audit (stop rebuilding)

| Already built | Stop investigating |
|---------------|-------------------|
| Append API + boundary tests | "Do we need multi-turn service?" |
| P16-Y 50-case battery | "Do we need new quality framework?" |
| Commercial trial pack | "What should invoice say?" |
| Customer tab + P16-O | "Can customers submit?" |
| OCR fusion pipeline | "Do we need document AI sprint?" |
| guardrail + trial_launch_check | "Are we deploy-ready?" without cold URL |
| ScenarioReplayTab | SimulationAssistant |

---

## ROI-ranked improvements by layer (30-day)

| Rank | Layer | Improvement | Effort | Type |
|------|-------|-------------|--------|------|
| 1 | Ingress | FP-004 off | 5 min | Ops |
| 2 | Timeline | Post-copy append CTA | 0.5 d | Wire |
| 3 | Case | Summary merge on append | 1–2 d | Tune |
| 4 | Next Action | Chinese templates | 1 d | Tune |
| 5 | Understanding | EN/ZH glance | 0.5 d | Copy |
| 6 | Timeline | waiting_on + deadline UI | 0.5 d | Wire |
| 7 | Case | deadline → still_needed | 0.5 d | Tune |
| 8 | Outcome | Observation log + invoice | 1 h | Process |
| 9 | Follow-up | Day 0 supervised protocol | 2 h | Process |
| 10 | Ingress | P16-M demo demotion | 0.5 d | Copy |

---

## Explicit deferrals (90-day)

| Defer | Until |
|-------|-------|
| P17 platform | Never in pilot |
| Stripe billing | 3+ paying offices |
| WeChat API sync | Post-PMF |
| OCR-first intake | Office 2 asks |
| Full P16-M UI sprint | After payment |
| Claims-first GTM | After cancel wedge proven |
| Enterprise routing/SLA | Never for Chen Kui |
| LLM generation path | Battery proves rules insufficient |

---

## Success metrics (SSOT)

| Metric | Week 4 target | Day 90 target |
|--------|---------------|---------------|
| Deployed cold URL works | PASS | PASS |
| Chen Kui unsupervised 2-turn case | 1 logged | 10+ logged |
| Observation log rows | ≥10 | ≥30 |
| Paying offices | **1** | **3** |
| Maturity L1–L4 composite | ≥78 | ≥85 |
| Append used after copy | ≥50% cases | Habitual |

---

## Document hierarchy

| Doc | Role |
|-----|------|
| **This file** | Architecture SSOT |
| `CASE_INTELLIGENCE_MATURITY_MODEL.md` | Commercial maturity ladder |
| `P16Z3_30_DAY_PLAN.md` | First paying office execution |
| `P16Z3_90_DAY_PLAN.md` | Three offices execution |
| `P16Z3_REVERSE_ENGINEERING.md` | Benchmark soul extraction |
| `P16Z3_PAIN_RANKING.md` | Founder pain priority |
| P16-Z0 archaeology | Evidence of what exists (reference) |

---

*End of Case Intelligence Master Outline — P16-Z3 SSOT*
