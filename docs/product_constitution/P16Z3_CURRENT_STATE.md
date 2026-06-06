# P16-Z3 Current State Assessment

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Evidence:** P16-Y battery (88.6 avg), P16-Z0 archaeology, repo inspection, P16-Z2 capability map  
**Scoring key:** Each level rated **Implemented · Partial · Hidden · Abandoned · Missing**

---

## Executive summary

| Dimension | Backend | Deployed product UI | Effective for Chen Kui |
|-----------|---------|---------------------|------------------------|
| **Engine maturity** | **L4.5** (strong L1–L4, partial L5–L7) | — | — |
| **Deployed maturity** | — | **L3.5** (L5 UX broken, L6 unwired) | **L2.5** (SSO blocks access) |
| **Battery-verified** | L1–L4 ≈ 88/100 single-turn | L5 multi-turn ≈ 60/100 | — |

**Composite verdict:** The product is a **Level 4 engine deployed as Level 3.5 experience** with **Level 2.5 access** until FP-004 is fixed.

---

## Level-by-level assessment

### L0 — Raw Intake

| Aspect | Score | Evidence |
|--------|-------|----------|
| Text paste | **Implemented** | `BrokerWorkbenchTab.tsx` primary path |
| Multi-message blob | **Implemented** | `triage_conversation()` accepts thread text |
| Attachment upload | **Partial** | Backend + collapsed UI; not primary path |
| Inline image on triage | **Hidden** | API + `inboxTriage.ts` type; no UI caller |
| Voice / PDF primary | **Missing / Abandoned** | Out of scope; PDF stub only |

**Level score:** **Implemented** (text wedge complete)

---

### L1 — Normalization & Classification

| Aspect | Score | Evidence |
|--------|-------|----------|
| Category classification | **Implemented** | Post-P16-Y: address, coverage, add-driver, UW no longer `unclear` |
| Urgency assignment | **Implemented** | low/medium/high/critical on all triage paths |
| Mixed-intent note | **Partial** | `secondary_issue_note` exists; weak in summary |
| Rule + LLM paths | **Partial** | Rules strong; LLM path unverified P16-Y |
| Chinese lane labels in UI | **Partial** | EN fragments remain in glance/queue |

**Level score:** **Implemented** (~85 backend; ~75 deployed copy)

**P16-Y Understanding dimension:** Strong on wedge lanes.

---

### L2 — Field Intelligence

| Aspect | Score | Evidence |
|--------|-------|----------|
| collected_fields | **Implemented** | Add-car, cancel, payment, missing-doc extractors |
| still_needed_fields | **Implemented** | P16-Y missing info library (20 patterns) |
| Deadline extraction | **Partial** | `_extract_deadline_hint()`; Y02 Chinese numeric gap |
| Policy number | **Implemented** | Structured extractors |
| notice_image gap | **Implemented** | `_message_needs_notice_image()` |
| Named insured / carrier | **Partial** | P16-Y P1–P2 gaps |
| bill_sent_claimed (premium) | **Missing** | Y45 fails |

**Level score:** **Implemented** with known partial gaps

**P16-Y Missing Info dimension:** 46.5/100 composite (includes multi-turn penalty).

---

### L3 — Case Distillation

| Aspect | Score | Evidence |
|--------|-------|----------|
| conversation_summary | **Implemented** | Intent lines post-P16-Y |
| case_draft V4 bundle | **Implemented** | `build_v4_case_draft_bundle()` |
| case_usable / handoff_ready | **Implemented** | `evaluate_v5_case_usable()` |
| Case persistence | **Implemented** | `case_store.py` + optional Postgres |
| Full draft card in UI | **Hidden** | API field exists; not shown trial |
| Multi-turn summary merge | **Missing** | P16-Y P0; Y44 fails |

**Level score:** **Partial** — single-turn strong; multi-turn distillation broken

**P16-Y Case Distillation:** 46.5/100 (multi-turn drags score).

---

### L4 — Office Action Generation

| Aspect | Score | Evidence |
|--------|-------|----------|
| broker_next_step generation | **Implemented** | Every triage path; category templates |
| client_prep generation | **Implemented** | Dynamic builders per category |
| client_reply_draft | **Implemented** | Copy-to-WeChat path |
| Chinese specificity | **Partial** | Generic wording flagged P16-Z2; templates needed |
| client_prep in product UI | **Hidden** | Gated `!productOnlyUi` |
| Office Actionability battery | **Implemented** | 25/25 ceiling on all 50 P16-Y cases |

**Level score:** **Implemented** engine / **Partial** deployed wording

**Critical nuance:** Rubric says actionability is perfect; Chen Kui simulation says Chinese specificity is weak. Both true — structure exists, copy tuning needed.

---

### L5 — Continuity (Multi-Turn & Append)

| Aspect | Score | Evidence |
|--------|-------|----------|
| triage_conversation() | **Implemented** | Primary multi-turn entry |
| session_store persistence | **Implemented** | Pre-handoff session binding |
| triage_for_append() | **Implemented** | Full re-triage on append |
| append_follow_up_message() | **Implemented** | `case_store.py` |
| POST append-message route | **Implemented** | Boundary enforcement |
| Append UI discoverability | **Hidden / Broken** | Only after queue reopen; no post-copy CTA |
| CustomerEntryTab multi-turn | **Hidden** | Tab unmounted trial |
| Prior bubble summary merge | **Missing** | P16-Y P0 |
| Correction handling (Y44) | **Partial** | Keyword rules planned |
| Continuity UX score | **Partial** | P16-X: 41/100 |

**Level score:** **Partial** — backend L5; deployed UX L2

**This is the largest maturity gap for retention.**

---

### L6 — Document Intelligence

| Aspect | Score | Evidence |
|--------|-------|----------|
| image_input_pipeline | **Implemented** | Vision API; empty stub without keys |
| parse_ocr_text_to_fields | **Implemented** | VIN, year, zip, insurer heuristics |
| ocr_case_fusion | **Implemented** | Slot fusion with confidence |
| v6_attachment_sidecar | **Implemented** | Saved attachment OCR |
| Inline image on triage API | **Hidden** | No product caller |
| Broker upload UI | **Partial** | Collapsed「附加材料」 |
| OCR in glance | **Missing** | No [OCR] field tags in UI |
| PDF extraction | **Abandoned** | Stub; frozen per constitution |

**Level score:** **Partial / Hidden** — built, not productized

---

### L7 — Confidence & Risk Gating

| Aspect | Score | Evidence |
|--------|-------|----------|
| v4_error_risk_score | **Implemented** | `case_draft_engine.py` |
| v5_handoff_risk_score | **Implemented** | Handoff policy input |
| case_usable / action_ready | **Implemented** | Milestone fields on result |
| truth_field_guardrails | **Hidden** | DEBUG env only |
| assist_layer suggestions | **Hidden** | `ENABLE_ASSIST_LAYER=1` |
| Risk in product UI | **Missing** | TS type only; no renderer |
| error_tolerance_layer | **Implemented** | Backend v6 block |

**Level score:** **Partial** — backend complete, frontend absent

---

### L8 — Lifecycle Execution

| Aspect | Score | Evidence |
|--------|-------|----------|
| case_lifecycle derivation | **Implemented** | `case_lifecycle.py` |
| case_status enum | **Implemented** | new/reviewing/waiting_client/done |
| waiting_on field | **Implemented** | client/broker/carrier/underwriting |
| Status in broker UI | **Partial** | Tags visible; editor partial |
| Follow-up editor | **Hidden** | Gated dev UI |
| Formal submit distinction | **Implemented** | `formal_submitted_at` |
| Activity timeline | **Hidden** | Backend `case_activity`; no trial UI |
| Queue waiting_on glance | **Partial** | Read-only in queue cards |

**Level score:** **Partial** — data model strong, workflow UI thin

---

### L9 — Outcome Guidance

| Aspect | Score | Evidence |
|--------|-------|----------|
| Observation log process | **Partial** | Template exists; log empty |
| Time-saved evidence | **Missing** | No aggregate tracking |
| Outcome recording | **Missing** | No resolved/escalated enum |
| Verified resolution | **Missing** | Not built |
| learning_signals JSONL | **Hidden** | Backend-only; no product path |
| audit_export | **Abandoned** | Stub scaffold |
| Invoice / payment evidence | **Partial** | Commercial docs; IDs empty |

**Level score:** **Missing** — process designed, not executed

---

## Maturity radar (backend vs deployed)

```
Level:  0    1    2    3    4    5    6    7    8    9
        |----|----|----|----|----|----|----|----|----|
Backend ████████████████████░░░░░░░░░░░░  (~L4.5)
Deployed ██████████████░░░░░░░░░░░░░░░░░  (~L3.5)
Chen Kui ████████░░░░░░░░░░░░░░░░░░░░░░  (~L2.5 w/ SSO)
```

---

## Status matrix (all levels)

| Level | Name | Implemented | Partial | Hidden | Abandoned | Missing |
|-------|------|:-----------:|:-------:|:------:|:---------:|:-------:|
| L0 | Raw Intake | ✓ | ✓ | ✓ | | |
| L1 | Classification | ✓ | ✓ | | | |
| L2 | Field Intelligence | ✓ | ✓ | | | ✓ |
| L3 | Case Distillation | ✓ | ✓ | ✓ | | ✓ |
| L4 | Office Action | ✓ | ✓ | ✓ | | |
| L5 | Continuity | ✓ | ✓ | ✓ | | ✓ |
| L6 | Document Intel | ✓ | ✓ | ✓ | ✓ | ✓ |
| L7 | Confidence/Risk | ✓ | | ✓ | | ✓ |
| L8 | Lifecycle | ✓ | ✓ | ✓ | | |
| L9 | Outcome | | ✓ | ✓ | ✓ | ✓ |

---

## Current composite maturity level

| Lens | Level | One-line |
|------|-------|----------|
| **Engine (codebase)** | **L4.5** | Single-turn case + action strong; multi-turn and docs partial |
| **Deployed product** | **L3.5** | Paste → glance → copy works; append and OCR hidden |
| **Chen Kui today** | **L2.5** | SSO + undiscoverable append caps effective value |
| **P16-Y battery** | **L4.0** | 88.6 avg; multi-turn cases drag L3/L5 |
| **Paid pilot readiness** | **L4.0 target** | Fix access + L5 UX → L4 deployed in 7 days |

---

## What changed since P16-Z2 / P16-Z2.5

Nothing structural in code — this sprint **confirms** prior verdicts with maturity framing:

- Engine at L4+ was already documented in P16-Z0/Z2
- L5 UX gap was already P0 in P16-Z2.5 roadmap
- P16-Y improved L1–L2; did not fix L5 merge

**P16-Z3 adds:** Explicit maturity ladder, per-level status columns, and gap-to-level mapping for 30/90-day plans.

---

*End of P16-Z3 Current State Assessment*
