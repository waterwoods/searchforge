# P16-Z3 Case Intelligence Maturity Model

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Constraint:** Strategic documentation only — no code, no deploy, no P17.

---

## Purpose

Define a maturity model that answers one question for every capability:

> **Does this help transform messy customer communication into an office-executable case faster, more accurately, and more completely?**

This model replaces the sprint's example ladder. The example was useful but misordered priorities for an insurance broker office pilot.

---

## North Star alignment

Every level must map to the office workflow:

```
Paste → Case Ready → Next Action → Follow-up → Outcome
```

| North Star stage | Maturity levels |
|------------------|-----------------|
| Paste | L0–L1 |
| Case Ready | L2–L4 |
| Next Action | L5 |
| Follow-up | L6–L7 |
| Outcome | L8–L9 |

---

## Why the example model was wrong

The sprint example proposed:

```
L0 Raw → L1 Classify → L2 Extract → L3 Case → L4 Next action → L5 Multi-turn → L6 Risk → L7 Outcome
```

**Problems:**

| Issue | Why it matters |
|-------|----------------|
| Multi-turn at L5 is too late | Insurance offices live in WeChat threads; continuity is not an advanced feature — it is day-2 retention |
| Risk at L6 overweights backend scores | v4/v5 exist but are invisible; OCR and deadline gaps hurt Chen Kui more than risk badges |
| "Case generation" before "next action" splits one atomic office moment | Office asks "what is this AND what do I do?" in one glance — splitting creates false build order |
| No persistence/lifecycle layer | Append without status/waiting_on is a message log, not office workflow |
| No document intelligence level | Cancel notices arrive as screenshots; text-only paste is the wedge, not the ceiling |
| Outcome guidance at top without lifecycle | You cannot guide outcomes without knowing who is waiting on whom |

---

## Revised maturity model (9 levels)

### Level 0 — Raw Intake

**Definition:** System accepts unstructured inbound without rejecting the channel.

| Signal | Office meaning |
|--------|----------------|
| Text paste works | Broker can start from WeChat copy |
| Multi-message blob accepted | Thread paste doesn't crash |
| Attachment accepted | Screenshot can enter the system |

**Not L0:** Understanding anything about the message.

---

### Level 1 — Normalization & Classification

**Definition:** System names what this is and how urgent it is.

| Signal | Office meaning |
|--------|----------------|
| `issue_category` not `unclear` | Lane identified (cancel, payment, add-car, etc.) |
| `urgency` assigned | Office knows if today vs this week |
| Mixed-intent flagged | Secondary ask noted, not lost |

**Benchmark anchor:** Zendesk AI classification, Salesforce Einstein Case Classification, Intercom intent routing.

---

### Level 2 — Field Intelligence

**Definition:** System extracts what is known and what is missing.

| Signal | Office meaning |
|--------|----------------|
| `collected_fields` populated | Office doesn't re-hunt for VIN, carrier, deadline |
| `still_needed_fields` populated |「还缺什么」is actionable |
| Deadline/policy/notice gaps detected | Cancel and UW lanes are safe |

**Benchmark anchor:** Salesforce auto-fill picklists, Stripe `recommended_evidence`.

---

### Level 3 — Case Distillation

**Definition:** Raw paste becomes a structured office-readable case artifact.

| Signal | Office meaning |
|--------|----------------|
| `conversation_summary` intent line | Glance replaces re-reading paste |
| `case_draft` / V4 bundle built | Structural packaging for handoff |
| `case_usable` / `handoff_ready` gates | System knows when office can act |
| Case persisted with ID | Same case can be reopened |

**Benchmark anchor:** Salesforce Wrap-Up, Intercom convert-to-ticket, Linear issue from context.

**Key insight:** This is "Case Ready" — not yet "what to do."

---

### Level 4 — Office Action Generation

**Definition:** System tells the office and customer what to do next, in office language.

| Signal | Office meaning |
|--------|----------------|
| `broker_next_step` specific in Chinese | One operational sentence, not generic |
| `client_prep` lists customer tasks | Broker can copy-paste guidance |
| `client_reply_draft` send-ready | Beat「直接回微信」on speed |
| Category templates tuned per lane | Cancel ≠ add-car ≠ missing doc |

**Benchmark anchor:** Salesforce Next Best Action, Intercom macros, Zendesk Copilot draft.

**Key insight:** Levels 3 and 4 together = **Case Ready + Next Action** in the North Star. They are sequential in the model but must ship as one office moment in the product.

---

### Level 5 — Continuity (Multi-Turn & Append)

**Definition:** Message 2–N updates the same case without re-pasting from scratch.

| Signal | Office meaning |
|--------|----------------|
| Session binds turns pre-handoff | Customer tab / multi-turn works |
| Append API merges new customer text | Turn 2 doesn't create orphan case |
| Prior bubbles in summary | Correction honored (Y44) |
| Boundary detection (same vs new issue) | Office not confused by topic change |
| Post-copy append discoverability | Broker knows to come back |

**Benchmark anchor:** Intercom conversation continuity, Zendesk ticket comments, Linear thread-as-source-of-truth.

**Why L5 not L7:** P16-X, P16-Y, P16-Z2 all prove Turn 1 wins, Turn 2+ loses users. Continuity is retention, not premium tier.

---

### Level 6 — Document Intelligence

**Definition:** Non-text evidence (screenshots, attachments) enriches the case.

| Signal | Office meaning |
|--------|----------------|
| OCR extracts VIN, carrier, deadline | Screenshot cancel notice usable |
| OCR fused into collected_fields | Fields tagged [OCR] when inferred |
| Notice image gap detection | System asks for screenshot when needed |
| Weak-image clarification reply | Customer told what to resend |

**Benchmark anchor:** Stripe dispute evidence merge, Salesforce Files + Einstein.

**Why above risk:** Chen Kui receives cancel notices as images. OCR path exists (`image_input_pipeline.py`, `ocr_case_fusion.py`) but is unwired in product UI.

---

### Level 7 — Confidence & Risk Gating

**Definition:** System quantifies uncertainty and gates handoff when unsafe.

| Signal | Office meaning |
|--------|----------------|
| `v4_error_risk_score` computed | Backend knows extraction confidence |
| `v5_handoff_risk_score` computed | Handoff safety signal |
| Risk surfaced as「需核实」| Broker sees when not to auto-trust |
| Truth guardrails block bad merges | Append doesn't corrupt fields |
| `case_usable` / `action_ready` milestones | Quote-ready vs collecting clear |

**Benchmark anchor:** Salesforce Einstein confidence tiers (auto-fill vs suggest vs show top 3).

**Why not higher:** Scores exist in `case_draft_engine.py` but are backend-only. Surfacing is low-effort revival, not new build.

---

### Level 8 — Lifecycle Execution

**Definition:** Office tracks who waits on whom until resolution.

| Signal | Office meaning |
|--------|----------------|
| `case_status` (new → reviewing → waiting → done) | Queue reflects reality |
| `waiting_on` (client/broker/carrier/UW) | Follow-up target clear |
| `next_contact_by` deadline | Snooze/remind semantics |
| Formal submit vs in-progress distinction | Handoff moment defined |
| Activity/notes on case | Audit trail for office |

**Benchmark anchor:** HubSpot ticket status, Intercom snooze, Salesforce Case Feed.

---

### Level 9 — Outcome Guidance

**Definition:** System helps office close the loop and learn from results.

| Signal | Office meaning |
|--------|----------------|
| Outcome recorded (resolved, escalated, lost) | Payment evidence, renewal anchor |
| Time-to-resolution tracked | ROI proof for invoice |
| Observation log → engine feedback | Friction drives fixes, not guesses |
| Deflection/KB loop (future) | Repeat questions handled faster |
| Verified resolution (Zendesk 2026 pattern) | Trust in AI-assisted closes |

**Benchmark anchor:** Zendesk verified resolution, HubSpot CSAT → KB gap, Stripe dispute win/loss.

**Why top level:** Cannot guide outcomes without L0–L8. Most pilot value is L1–L5; L9 is commercial maturity.

---

## Maturity level summary table

| Level | Name | North Star stage | Pilot critical? |
|-------|------|------------------|-----------------|
| L0 | Raw Intake | Paste | Yes |
| L1 | Classification | Paste → Ready | Yes |
| L2 | Field Intelligence | Case Ready | Yes |
| L3 | Case Distillation | Case Ready | Yes |
| L4 | Office Action | Next Action | Yes |
| L5 | Continuity | Follow-up | **Yes — retention** |
| L6 | Document Intelligence | Follow-up | Week 2+ |
| L7 | Confidence & Risk | Follow-up | Medium |
| L8 | Lifecycle Execution | Outcome | Medium |
| L9 | Outcome Guidance | Outcome | Post-payment |

---

## Composite maturity score (how to read levels)

| Composite | Label | Meaning |
|-----------|-------|---------|
| **L4+ deployed** | Pilot-viable single-turn | Chen Kui can paste → copy on wedge lanes |
| **L5 deployed** | Pilot-viable multi-turn | Broker returns after client reply |
| **L6+ deployed** | Production-grade intake | Screenshots and attachments handled |
| **L8+ deployed** | Office workflow product | Status, waiting, follow-through |
| **L9** | Outcome-priced SaaS | Renewal evidence, verified resolution |

---

## Anti-patterns (not maturity levels)

These are **not** levels — they are distractions:

| Anti-pattern | Why excluded |
|--------------|--------------|
| P17 platform | Not case intelligence |
| Full CRM | Salesforce already exists |
| Voice/IVR | Out of pilot scope |
| LLM chatbot | Violates paste-and-copy soul |
| New microservices | Duplicates `triage.py` |
| Customer portal before broker retention | Cap 4 before Cap 1 proven |

---

## Relationship to P16-Y rubric

| P16-Y dimension | Maturity levels |
|-----------------|-----------------|
| Understanding | L1 |
| Missing Info Detection | L2 |
| Office Actionability | L4 |
| Multi-message Handling | L5 |

P16-Y battery avg **88.6/100** ≈ strong L1–L4 on single-turn; weak L5 on corrections.

---

## Document index

| Phase | Document |
|-------|----------|
| 1 | `P16Z3_MATURITY_MODEL.md` (this file) |
| 2 | `P16Z3_CURRENT_STATE.md` |
| 3 | `P16Z3_ARCHAEOLOGY.md` |
| 4 | `P16Z3_HIDDEN_CAPABILITIES.md` |
| 5 | `P16Z3_REVERSE_ENGINEERING_MAP.md` |
| 6 | `P16Z3_GAP_ANALYSIS.md` |
| 7 | `P16Z3_30_DAY_PLAN.md` |
| 8 | `P16Z3_90_DAY_PLAN.md` |
| 9 | `P16Z3_ONE_CAPABILITY_TEST.md` |
| 10 | `P16Z3_FINAL_VERDICT.md` |

---

*End of P16-Z3 Maturity Model*
