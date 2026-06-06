# P16-Z8 Phase 7 — Benchmark Mapping

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Compare:** Unified Intake · Zendesk · Intercom · Salesforce Service Cloud  
**Sources:** P16-Z7 benchmark, P16-Z2 company teardown, P16-Z3 maturity model, Role D battery

---

## Pattern comparison matrix

| Pattern | Zendesk | Intercom | Salesforce | Unified Intake | Gap |
|---------|---------|----------|------------|----------------|-----|
| **Conversation thread UI** | Ticket comments | Inbox thread | Case feed | `case_messages` + Z6 对话记录 | **Closed** post-Z6 deploy |
| **Custom fields on case** | Native | Custom attrs | Field sets | `collected_fields` | **Partial** — merge on append |
| **Responsibility / waiting** | Views, SLA | Team assign | Owner + status | `waiting_on` manual | **Missing auto-inference** |
| **Macro / template replies** | Macros | Saved replies | Quick text | `reply_template_*` | **Built** |
| **Multi-turn merge** | Agent edits fields | Bot + agent | Flow + agent | Rules re-extract | **Behind** on non-add-car |
| **Insurance lane routing** | Manual tags | Manual | Industry clouds | Engine lanes | **Ahead** on Chinese T1 |
| **Payment/lapse workflow** | Agent + fields | Bot flows | Billing integration | Classifier + fields | **Behind** D10 |
| **Claims FNOL** | Form + agent | Bot | Industry template | Paste → checklist | **Ahead** T1; **behind** T2+ |
| **Correction memory** | Full thread visible | Thread | Case history | Summary prepend Z6 | **Parity** D09; **gap** CL02 |
| **Outcome / resolution proof** | Solved ticket | Resolved | Closed case | **Missing** | **Missing** (deferred) |
| **Attachment gallery** | Native | Native | Files | OCR partial | **Behind** |
| **3-day unsupervised memory** | Agent-maintained | Agent-maintained | Agent-maintained | 68.9 reread | **Behind** without fixes |

---

## What pattern are we missing?

### 1. **Structured field hygiene on append** (Zendesk core)

Zendesk agents **manually update fields** but the **UI always shows prior values**. We **recompute and wipe** on lane mismatch.

**Fix:** Generic persisted merge — not a new product category.

### 2. **Responsibility views** (Intercom / Zendesk SLA)

Intercom assigns **team + waiting state**. We have the field (`waiting_on`) but **no inference or default-open UX**.

**Fix:** Triage suggest + collapsed editor promotion — 0.5 day.

### 3. **Thread-as-source-of-truth** (all three)

All benchmarks treat **full thread as hero**. We fixed storage (Z6) but **distillation still overwrites headline** on weak lanes.

**Fix:** Lane guards + summary merge — engine not UI.

### 4. **Industry field packs** (Salesforce Insurance)

Salesforce ships **FNOL field sets** (plate, loss type, $). We have **6 booleans** — no plate #, $, total_loss.

**Fix:** Extend `_extract_claim_fields()` — 4 hours.

### 5. **Verified resolution / outcome** (Zendesk 2024+)

Zendesk added **verified resolution** metrics. We have **no outcome enum** — correctly deferred per constitution.

**Fix:** Observation log first — not engine.

---

## Domain-specific benchmark gaps

| Domain | Zendesk wins because… | Our counter-strength |
|--------|----------------------|----------------------|
| Payment | Agent sets fields manually | Chinese cancel T1 faster (D01 partial) |
| Remove vehicle | Agent retags ticket | — (we lose D07) |
| Collected merge | Fields never silently cleared | add_car merge is strong |
| Waiting on | Native filters/views | Insurance-specific triage text |
| Claims T2+ | Thread always visible | Z6 thread closes view gap |

---

## Strategic position (unchanged from P16-Z3)

| Layer | Level | vs Zendesk |
|-------|-------|------------|
| Engine | L4.5 | Parity on UW, ahead on Chinese lanes |
| Deployed UX | L3.5–4 | Thread card → view parity |
| 3-day memory | L4.0 | **Behind** L4.5 on payment/claims corrections |

---

## Phase 7 verdict

**Missing pattern is not "AI memory platform" — it is field persistence + responsibility inference**, both of which exist as partial implementations. **Do not copy Salesforce field sets wholesale** — add 5 claim/payment tokens only.
