# P16-Z3 Capability Archaeology Deep Dive

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Method:** Repository search + P16-Z0/Z2 cross-reference + 48-module inventory  
**Constraint:** Read-only archaeology — no code changes.

---

## Executive summary

The Case Intelligence engine lives in **`services/fiqa_api/inbox_triage/`** (48 Python modules) orchestrated by **`services/fiqa_api/routes/inbox_triage.py`**. There is no separate case intelligence microservice — and there should not be one.

| Domain | Modules | Backend status | Product UI |
|--------|---------|----------------|------------|
| Case intelligence core | 15+ | **Strong** | Partial |
| Append / continuity | 8 | **Strong** | **Broken UX** |
| OCR / image | 5 | **Partial** | Hidden |
| Next-action generation | 10+ | **Strong** | Partial |
| Risk scoring | 3 | **Strong** | **Not shown** |
| Multi-turn | 6 | **Strong API** | Hidden trial |
| Case lifecycle | 8 | **Strong** | Partial |

---

## 1. Case Intelligence modules

### Core engine

| File | Key symbols | Status | UI visibility |
|------|-------------|--------|---------------|
| `triage.py` (~6.6k lines) | `triage_conversation()` L5545, `triage_for_append()` L3643, `triage_message()` L6598 (legacy) | **Implemented** | Via API only |
| `case_draft_engine.py` | `build_v4_case_draft_bundle()`, `evaluate_v5_case_usable()`, `estimate_v4_error_risk_score()`, `estimate_v5_handoff_risk_score()` | **Implemented** | Indirect (glance fields) |
| `intake_engine.py` | `run_intake_engine()`, `compute_case_lifecycle()` | **Implemented** | Backend-only overlay |
| `case_lifecycle.py` | `_derive_case_lifecycle()` | **Implemented** | Tags in workbench |
| `field_strategy.py` | Declarative add-car field strategy | **Implemented** | Debug |
| `error_tolerance_layer.py` | `apply_error_tolerance()` | **Implemented** | Backend-only |
| `truth_field_guardrails.py` | `should_accept_field()` | **Hidden** | `DEBUG_TRUTH_GUARDRAILS=1` |

### Policy & reply layers

| File | Role | Status |
|------|------|--------|
| `triage_handoff_policy.py` | Handoff timing gates | Implemented |
| `triage_add_car_policy.py` | Add-car quote-ready policy | Implemented |
| `triage_handoff_reply_composer.py` | Customer reply at handoff | Implemented |
| `triage_handoff_reply_policy.py` | Post-handoff phrasing rules | Implemented |
| `add_car_triage_post_submit.py` | Post-submit copy pools | Implemented |
| `conversion_layer.py` | Quote-ready → contact ask | Implemented (customer tab) |
| `reply_template_composer.py` | Template stitching | Implemented |
| `reply_template_policy.py` | Template selection rules | Implemented |
| `append_case_boundary_copy.py` | Append boundary customer copy | Implemented |

### Optional / lab overlays

| File | Role | Status |
|------|------|--------|
| `assist_layer.py` | Post-truth suggestions | **Hidden** (`ENABLE_ASSIST_LAYER=1`) |
| `add_car_llm_slot_candidates.py` | Bounded LLM slot extraction | **Hidden** (env-gated) |
| `learning_signals.py` | JSONL correction memory | **Backend-only** |
| `audit_export.py` | Compliance export | **Abandoned stub** |
| `role_c_simulation_service.py` | Role C LLM customer | **Hidden** (sim tab) |
| `notice_retrieval.py` | Notice doc retrieval | Partial |

### Key extraction functions in triage.py

| Function | Maturity level | Role |
|----------|----------------|------|
| `_extract_deadline_hint()` | L2 | Deadline → summary/collected |
| `_message_needs_notice_image()` | L2/L6 | Gap for screenshot-only cancels |
| `_compute_add_car_collected_still_lists()` | L2 | Structured field lists |
| `_classify_append_case_boundary()` | L5 | same_case / borderline / new_issue |
| `_build_conversation_summary()` | L3 | Intent line for glance |
| `_get_category_templates()` | L4 | broker_next_step templates |
| `_build_customer_question_broker_next_step()` | L4 | Dynamic Q&A next step |
| `_build_missing_document_client_prep()` | L4 | Missing-doc client prep |

---

## 2. Append functionality

### Backend pipeline (complete)

```
Broker reopens case OR append UI
    ↓
appendCaseMessage() [inboxTriage.ts]
    ↓
POST /api/inbox/cases/{id}/append-message [routes/inbox_triage.py L1822]
    ↓
triage_for_append() [triage.py L3643]
    ↓
_apply_append_case_boundary() [triage.py L3538]
    ↓
append_follow_up_message() [case_store.py L1098]
    ↓
Updated case returned to UI
```

| Component | Status | Notes |
|-----------|--------|-------|
| `triage_for_append()` | **Implemented** | Re-triages with prior turns; forces `handoff_ready=True` |
| `_apply_append_case_boundary()` | **Implemented** | Blocks mutation on clear new issue |
| `append_follow_up_message()` | **Implemented** | Persists customer+system messages |
| Boundary enforcement tests | **Implemented** | `test_new_issue_append_enforcement.py` |
| AB scenarios | **Implemented** | `configs/case_boundary_append_scenarios.json` |

### UI (broken discoverability)

| Surface | File | Status |
|---------|------|--------|
| Append card (product) | `BrokerWorkbenchTab.tsx` L1542–1571 | **Partial** — only when `caseView === 'reopened'` |
| Post-copy CTA | — | **Missing** |
| Customer append | `CustomerEntryTab.tsx` L605+ | **Hidden** (tab unmounted trial) |
| Dev append block | `BrokerWorkbenchTab.tsx` L2318 | Hidden behind `!productOnlyUi` |

**Verdict:** L5 backend = **Implemented**. L5 UX = **Hidden/Broken**.

---

## 3. OCR / image paths

### Pipeline

```
Image bytes / attachment / inline base64
    ↓
extract_text_from_image_bytes() [image_input_pipeline.py]
    ↓
parse_ocr_text_to_fields() [parse_ocr_text_to_fields.py]
    ↓
fuse_ocr_into_inferred() [ocr_case_fusion.py]
    ↓
merge_v6_ocr_signals() [v6_attachment_sidecar.py]
    ↓
triage_conversation(..., v6_ocr_signals=...)
```

| Component | Status | Product caller? |
|-----------|--------|-----------------|
| `image_input_pipeline.py` | **Partial** | No — needs Vision API keys |
| `parse_ocr_text_to_fields.py` | **Implemented** | Backend only |
| `ocr_case_fusion.py` | **Implemented** | Backend only |
| `v6_attachment_sidecar.py` | **Implemented** | Attachment upload route |
| Inline image on triage | **Implemented API** | **No UI caller** |
| Attachment upload UI | **Partial** | Collapsed「附加材料」in workbench |
| `_v6_weak_inline_image_intake()` | **Implemented** | Weak-image clarify reply |
| PDF path | **Abandoned stub** | Frozen |

**Tests:** `tests/test_v6_ocr_parse_and_fusion.py`, `tests/test_inline_image_triage_route.py`

**Verdict:** L6 = **Partial/Hidden** — full pipeline exists; product UI unwired.

---

## 4. Next-action generation

### Generation chain

```
triage_conversation()
    ↓
_rule_based_triage() / _llm_triage()
    ↓
_get_category_templates() + dynamic builders
    ↓
configs/clients/chen_kui/ui_copy.json [config_loader]
    ↓
broker_next_step, client_prep, client_reply_draft
```

| Output field | Generator | UI (trial) |
|--------------|-----------|------------|
| `broker_next_step` | Category templates + dynamic builders | **Visible** — queue + glance |
| `client_prep` | `_build_missing_document_client_prep()` etc. | **Hidden** (`!productOnlyUi`) |
| `client_reply_draft` | Reply composers | **Visible** — copy button |
| `conversion_layer` replies | `conversion_layer.py` | Customer tab only |
| `assist` suggestions | `assist_layer.py` | Env-gated |

**Config:** `configs/clients/chen_kui/ui_copy.json` — category-specific Chinese templates.

**Verdict:** L4 = **Implemented** engine; **Partial** deployed (wording + hidden client_prep).

---

## 5. Risk-scoring logic

| Score | Function | File | Computed when | Shown in UI? |
|-------|----------|------|---------------|--------------|
| v4_error_risk_score | `estimate_v4_error_risk_score()` | case_draft_engine.py L858 | Add-car + generic paths | **No** |
| v5_handoff_risk_score | `estimate_v5_handoff_risk_score()` | case_draft_engine.py L563 | Handoff decisions | **No** |
| case_usable | `evaluate_v5_case_usable()` | case_draft_engine.py | Every draft build | Indirect |
| action_ready | intake_engine | intake_engine.py | Milestone field | Partial |

**Lab consumers:** `scripts/run_v5_immediate_handoff_simulation.py`, `scripts/run_analytics_north_star_simulation.py`

**UI contract:** `ui/src/api/inboxTriage.ts` L145 types `v4_error_risk_score` — no renderer.

**Verdict:** L7 = **Implemented backend / Missing frontend**.

---

## 6. Multi-turn handling

| Component | File | Status |
|-----------|------|--------|
| Primary entry | `triage_conversation()` triage.py | **Implemented** |
| Session persistence | `session_store.py` | **Implemented** |
| Session repository | `session_repository.py` | **Implemented** |
| Case binding | `case_binding.py` | **Implemented** |
| Route orchestration | `routes/inbox_triage.py` L1157+ | **Implemented** |
| GET session API | routes L1661 | **Implemented** |
| Customer multi-turn UI | `CustomerEntryTab.tsx` | **Hidden trial** |
| Broker single-turn bias | `BrokerWorkbenchTab.tsx` | **Partial** — paste primary |
| Scenario replay | `ScenarioReplayTab.tsx` | **Hidden** |
| SimulationAssistant | `SimulationAssistant.tsx` | **Orphaned** (zero imports) |

**Critical gap:** Prior customer bubbles not merged into `conversation_summary` on append (P16-Y P0, Y44).

**Verdict:** L5 API = **Implemented**; L5 distillation = **Missing**; L5 UX = **Hidden**.

---

## 7. Case lifecycle handling

| Component | File | Status |
|-----------|------|--------|
| Lifecycle derivation | `case_lifecycle.py` | **Implemented** |
| Route attachment | `_attach_case_lifecycle()` routes L485 | **Implemented** |
| UI labels | `ui/src/components/intake/caseLifecycleDisplay.ts` | **Implemented** |
| Status enum | `case_store.py` CASE_STATUS_VALUES | **Implemented** |
| waiting_on enum | case_store CASE_WAITING_ON_VALUES | **Implemented** |
| PATCH status/follow-up | routes | **Implemented** |
| Truth overlay | `case_truth_repository.py` | **Implemented** |
| PG mirror | `service_record_read.py` | **Implemented** |
| Workbench enrichment | `workbench_enrichment.py` | Dev tags only |
| Follow-up editor | BrokerWorkbenchTab L2349+ | **Hidden trial** |

**Contract doc:** `docs/product_constitution/contracts/CAPABILITY_05_CASE_LIFECYCLE.md`

**Verdict:** L8 = **Partial** — strong data model, thin workflow UI.

---

## Wiring diagram (paste → outcome)

```
┌─────────────────────────────────────────────────────────────────┐
│  BROKER UI (BrokerWorkbenchTab.tsx)                             │
│  Paste → 开始整理 → Glance → 复制给客户                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ POST /api/inbox/triage
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  routes/inbox_triage.py                                         │
│  session read → triage_conversation() → case_store.save_case()  │
│  → _attach_case_lifecycle() → _attach_assist_layer()            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   triage.py         case_draft_engine    intake_engine
   (L1-L4 rules)     (L3 bundle, L7 risk)  (milestones)
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                    TriageResult JSON
                    (category, fields, summary,
                     broker_next_step, case_id, ...)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  APPEND PATH (hidden until reopen)                              │
│  POST .../append-message → triage_for_append() → case_store     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Orphaned / abandoned inventory

| Item | Path | Status | Action |
|------|------|--------|--------|
| `triage_message()` HTTP bypass | triage.py | Orphaned from routes | Keep for scripts |
| `SimulationAssistant.tsx` | ui/src/components/simulation/ | **Abandoned** | Delete |
| Inline image triage | API + inboxTriage.ts | **Orphaned** | Wire or document defer |
| `audit_export.py` | inbox_triage | **Abandoned stub** | Ignore |
| `learning_signals.py` | inbox_triage | Backend-only | Post-L9 |
| ~197 lab scripts | scripts/run_* | Lab | OPERATOR_IGNORE_LIST |
| Mortgage NLU | `mortgage/nl_to_stress_request.py` | **Unrelated vertical** | Out of scope |
| Code intelligence AI | `services/code_intelligence/` | **Unrelated** | Out of scope |

---

## Duplication audit (do not rebuild)

| If tempted to build… | Already exists at… |
|----------------------|-------------------|
| CaseIntelligenceService | `triage.py` + `case_draft_engine.py` |
| Conversation microservice | `triage_conversation()` + `session_store.py` |
| Append backend | `append-message` route + `triage_for_append()` |
| OCR pipeline | `image_input_pipeline.py` + `ocr_case_fusion.py` |
| Risk engine | v4/v5 in `case_draft_engine.py` |
| Customer portal | `CustomerEntryTab.tsx` + `MyRequestsTab.tsx` |
| Simulation UI | `ScenarioReplayTab.tsx` |

---

## Evidence index

| Artifact | Path |
|----------|------|
| Prior archaeology | `P16Z0_CASE_INTELLIGENCE_ARCHAEOLOGY.md` |
| Capability map | `P16Z2_CAPABILITY_MAP.md` |
| Inventory (48 modules) | `P16Z0_CAPABILITY_INVENTORY.md` |
| P16-Y battery | `scripts/run_p16y_case_battery.py`, `configs/p16y_50_cases.json` |
| Guardrail | `scripts/guardrail_inbox_triage.sh` |
| Standard | `docs/standards/BROKER_INBOX_TRIAGE_STANDARD.md` |

---

*End of P16-Z3 Capability Archaeology*
