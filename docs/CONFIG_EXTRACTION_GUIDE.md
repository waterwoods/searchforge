# Config Extraction Guide

**Purpose:** Define what was extracted, what remains hardcoded, and how to adapt for a new client or industry.

**Created:** 2026-03-09 — Config Extraction Sprint  
**Updated:** 2026-03-09 — Reply Template Extraction Sprint, Core Reply Template Expansion Sprint

---

## 1. Config Structure

```
configs/
├── common/                    # Shared across clients
│   ├── README.md
│   └── workflow_defaults.json   # Fallbacks: broker_next_step, client_prep, client_reply_draft
├── industries/
│   └── insurance/             # Insurance industry pack
│       ├── README.md
│       ├── markers.json        # Intent detection markers
│       ├── reply_templates.json  # First-turn reply templates
│       ├── category_templates.json  # Per-category broker_next_step, client_prep
│       └── add_car_rules.json  # Add-Car Quote next-step prompts
├── clients/
│   └── chen_kui/              # Chen Kui client pack
│       ├── README.md
│       ├── handoff_phrases.json  # Handoff reply strings
│       ├── reply_overrides.json  # Optional reply template overrides
│       └── ui_copy.json        # Client UI copy (target for future UI loading)
├── inbox_triage_scenarios.json   # (unchanged) Regression tests
├── chen_kui_proxy_calibration_cases.json
└── ...
```

---

## 2. What Is Extracted (Config-Driven Now)

| Layer | File | What | Used by |
|-------|------|------|---------|
| **Common** | `configs/common/workflow_defaults.json` | Fallbacks: broker_next_step, client_prep, client_reply_draft | `triage.py` via `config_loader.py` |
| **Industry** | `configs/industries/insurance/markers.json` | Intent markers (add_vehicle, payment, cancellation, dmv_help, etc.), document_items | `triage.py` via `config_loader.py` |
| **Industry** | `configs/industries/insurance/reply_templates.json` | Reply templates: cancellation_warning, add_car, payment_lapse_expiration, missing_document, etc. (zh/en) | `triage.py` via `config_loader.py` |
| **Industry** | `configs/industries/insurance/category_templates.json` | Per-category broker_next_step, client_prep | `triage.py` via `config_loader.py` |
| **Industry** | `configs/industries/insurance/add_car_rules.json` | Add-Car Quote next-step prompts (ask_vehicle, ask_zip, ask_delivery_driver) | `triage.py` via `config_loader.py` |
| **Client** | `configs/clients/chen_kui/handoff_phrases.json` | Handoff reply strings (add_car / other, zh / en) | `triage.py` via `config_loader.py` |
| **Client** | `configs/clients/chen_kui/reply_overrides.json` | Optional overrides for industry reply templates | `config_loader.py` merges into templates |
| **Client** | `configs/clients/chen_kui/ui_copy.json` | Client UI copy (app title, office label, quick-start). Loaded by GET /api/inbox/client-config; UI fetches and renders. | **Wired** (Client Configuration Wiring Sprint) |

---

## 3. What Remains Hardcoded

| Area | Location | Why |
|------|----------|-----|
| Other category reply templates (missing_signature, underwriting, renewal, dmv, unclear, etc.) | `triage.py` `_build_client_reply_draft` | Next extraction candidate |
| broker_next_step, client_prep for customer_question | `triage.py` `_build_customer_question_*` | Dynamic per sub-intent; stays in code |
| Handoff thresholds (add-car enough when year+model+zip) | `triage.py` `_add_car_enough_for_handoff` | Rules; could move to config later |
| VALID_CATEGORIES, VALID_URGENCIES | `triage.py` | Schema; low value to extract |
| FORMAL_DRAFT_MARKERS, UNSENDABLE_DRAFT_MARKERS, ROBOTIC_DRAFT_MARKERS | `triage.py` | Draft quality; could move to common later |
| Classification logic | `triage.py` `_classify_with_guardrails` | Core rules; stays in code |
| UI copy (办公室, 陈奎, etc.) | `UnifiedIntakePage.tsx`, `AppLayout.tsx` | Config structure in ui_copy.json; UI loading deferred |

---

## 4. Common / Industry / Client Boundary

| Layer | What belongs | Example |
|-------|--------------|---------|
| **Common** | Shared workflow defaults, generic labels | (Future) max_turns_before_handoff, generic fallback wording |
| **Industry** | Insurance-specific markers, document types, scenario reply templates | add_vehicle, payment, dmv_help; add_car reply, payment_lapse reply, missing_document reply |
| **Client** | Chen Kui office phrasing, tone, optional reply overrides | "报价资料已收集，办公室会尽快出价"; reply_overrides.json to tweak industry templates |

**Reply template boundaries:**
- **Industry** (`reply_templates.json`): Base wording for insurance scenarios (add-car, payment risk, missing document, english notice confusion, premium review, remove vehicle). Reusable across insurance brokers.
- **Client** (`reply_overrides.json`): Override specific keys when this broker wants different phrasing. Empty = use industry defaults.

**Per-template placement:**
- `english_notice_confusion`: Industry default — common when Chinese-speaking clients get English notices; any broker may tweak tone.
- `premium_review`: Industry default — premium-too-high concern; client may want softer/stronger reassurance.
- `remove_vehicle`: Industry default — same pattern as add_car; client may vary phrasing.

**Hot-swap implication:**
- New insurance client → replace `configs/clients/chen_kui/` with `configs/clients/new_broker/` (handoff_phrases + optional reply_overrides)
- New industry (e.g. food) → replace `configs/industries/insurance/` with `configs/industries/food/` (markers + reply_templates) and adapt triage logic

---

## 5. How to Add a New Client

1. Create `configs/clients/<client_id>/`
2. Add `handoff_phrases.json` with `add_car` and `other` keys, each with `zh` and `en` strings
3. Optionally add `reply_overrides.json` with `overrides` key; e.g. `{"add_car": {"zh": "自定义加车回复"}}` to override industry template
4. (Future) Add env or runtime switch to select client; today triage loads `chen_kui` by default

---

## 6. How to Add a New Industry

1. Create `configs/industries/<industry>/markers.json`
2. Mirror the structure of `configs/industries/insurance/markers.json`
3. Adapt `config_loader.py` to accept industry parameter; today it loads `insurance` only

---

## 7. Fallback Behavior

If config files are missing or invalid, triage falls back to hardcoded defaults. No runtime failure.

---

*End of guide*
