# P16-Z0 Case Intelligence Archaeology

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 4  
**Search terms:** deadline extraction, missing info, case distillation, risk extraction, case intelligence  
**Evidence:** `triage.py`, `case_draft_engine.py`, `P16Y_*`, guardrail batteries

---

## Map: implemented / partial / planned

| Capability | Status | Implementation | Documentation | Deployed trial |
|------------|--------|----------------|---------------|----------------|
| Missing info detection | **Implemented** | Rules + `still_needed_fields` | `P16Y_MISSING_INFO_LIBRARY.md` (20 patterns) | One-shot glance「还缺什么」 |
| Deadline extraction | **Implemented** (partial) | `_extract_deadline_hint()` → `deadline_mentioned` | P16-Y §6 | Indirect via summary/copy; Chinese numeric gap Y02 |
| Notice / image gap | **Implemented** | `_message_needs_notice_image()`, `notice_image` field | P16-Y battery Y38 | Text-only paste on Preview |
| Policy number gap | **Implemented** | Structured extractors | P16-Y | Yes |
| Case draft packaging | **Implemented** | `case_draft_engine.py` — v4 bundle, `case_usable` | — | Fields in glance; not full draft UI |
| Case Intelligence (rubric) | **Metric** | Scored in battery | `P16Y_RUBRIC.md` | 39.1 → **42.1** (+3.0) |
| Case Distillation (rubric) | **Metric** | Understanding + multi-message composite | Same rubric | 43.8 → **46.5** |
| Office Actionability | **Metric** | Broker step quality | Same rubric | 25.0 ceiling — unchanged |
| Risk extraction (v4/v5 scores) | **Implemented** | `estimate_v4_error_risk_score`, `estimate_v5_handoff_risk_score` | Rarely named in docs | **Not shown** in product UI |
| Assist layer | **Partial** | `assist_layer.py` | — | Off unless `ENABLE_ASSIST_LAYER=1` |
| Multi-turn summary merge | **Planned / deferred** | Not built | P16-Y P0 #1 | Y44 fails |
| Premium thread merge | **Planned** | Partial | P16-Y P1 #2 | Y45 fails |
| Interactive gap-fill | **Planned (product)** | Not built | P16-X audit | Report generator, not dialogue |
| LLM path parity | **Planned** | Unverified P16-Y | P16-Y #10 | — |
| Carrier / named insured extract | **Planned** | Weak | P16-Y #5–6 | P2 |
| ML distillation (mortgage) | **Out of scope** | `experiments/gen_approval_distillation_data.py` | — | Unrelated to intake |

---

## 1. Missing information

### Implemented

- **`collected_fields`** / **`still_needed_fields`** on every triage result
- **P16-Y missing info library** — 20 patterns mapped to `still_needed_fields`
- Handoff extractors e.g. `_missing_document_handoff_fields()`
- Glance rendering:「还缺什么（首要）」in broker workbench

### Partial

- System **declares** gaps; does **not** run multi-turn dialogue to collect them (`P16X_CONVERSATION_AUDIT.md`)
- Customer 提交补充 exists but tab **hidden** on trial URL

### Planned (P16-Y backlog)

| # | Gap | Severity |
|---|-----|----------|
| 1 | Multi-turn summary merge (Y44) | P0 |
| 2 | `bill_sent_claimed` when 发你账单了 (Y45) | P1 |
| 3 | Deadline → `still_needed` for cancel/UW | P1 |

---

## 2. Deadline extraction

### Implemented

```text
triage.py → _extract_deadline_hint()
         → deadline_mentioned on result
         → surfaced in conversation_summary / broker copy
```

### Partial

- Chinese numeric deadlines (e.g. emoji cancel "7 days") not always in collected fields (Y02)
- No dedicated **deadline widget** in UI — broker reads prose

### Planned

- P16-Y recommendation: deadline → `still_needed` when category is cancellation/UW and date parseable

---

## 3. Case distillation

**Important:** "Case Distillation" in P16-Y is a **rubric dimension**, not a separate microservice.

Definition (`P16Y_RUBRIC.md`): *Case Distillation = Understanding + Multi-message*

### Implemented (as engine behavior)

- `build_v4_case_draft_bundle()` — packages inferred fields for office
- `conversation_summary` intent lines (post P16-Y)
- Classification breadth (address, coverage, add-driver, UW questionnaire)

### Partial

- Multi-message merge weak on corrections (Y44, Y45)
- `case_draft.completion_message` shown customer-side; broker sees glance not full distillation card

### Planned

- Explicit inject of prior `[客户]` bubbles into summary (append architecture)

---

## 4. Risk extraction

Docs rarely say "risk extraction"; code uses **risk scores**.

| Score | File | In product UI? |
|-------|------|----------------|
| `v4_error_risk_score` | `case_draft_engine.py` | Typed in TS; **not rendered** |
| `v5_handoff_risk_score` | Same | Backend + scripts only |
| Payment/cancellation field extractors | `triage.py` | Via category + fields |

### Status: **Implemented backend, hidden frontend**

Revival = surface score in broker glance (small UI) — **do not rebuild** scoring engine.

---

## 5. P16-Y sprint outcome (reference)

| Index | Before | After |
|-------|--------|-------|
| Overall battery | 85.6 | **88.6** |
| Case Intelligence | 39.1 | **42.1** |
| Case Distillation | 43.8 | **46.5** |

Artifacts:

- `configs/p16y_50_cases.json`
- `scripts/run_p16y_case_battery.py`
- `.p16y_results/*.json` (if present locally)

Explicit non-goals honored: no UI redesign, no P17, no deploy in P16-Y.

---

## Rubric vs code (avoid duplication)

| Name in docs | What it actually is |
|--------------|---------------------|
| Case Intelligence | Rubric + rules + summary quality |
| Case Distillation | Rubric composite (understanding + multi-turn) |
| Office Actionability | Broker `broker_next_step` quality |
| case_draft_engine | Closest code analog to "distillation" |

**Do not build** a second "CaseIntelligenceService" — extend `triage.py` + `case_draft_engine.py`.

---

## Evidence index

| Artifact | Path |
|----------|------|
| Rubric | `P16Y_RUBRIC.md` |
| Missing library | `P16Y_MISSING_INFO_LIBRARY.md` |
| Extraction improvements | `P16Y_EXTRACTION_IMPROVEMENTS.md` |
| Final verdict | `P16Y_FINAL_VERDICT.md` |
| Engine | `services/fiqa_api/inbox_triage/triage.py` |
| Draft engine | `services/fiqa_api/inbox_triage/case_draft_engine.py` |

---

*End of P16-Z0 Case Intelligence Archaeology*
