# Reusable Configuration Inventory Spec

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18

---

## 1. High-Value Configurable Areas

| Area | Current | Target layer | Priority |
|------|---------|--------------|----------|
| Scenario package inclusion | STANDARD_SCENARIO_PACKAGE.md (doc) | Industry config | Medium |
| Intent markers | markers.json | Industry | **Done** |
| Document item labels | markers.json document_items | Industry | **Done** |
| Reply templates (first-turn) | reply_templates.json | Industry | **Done** |
| Handoff phrases | handoff_phrases.json | Client | **Done** |
| Reply overrides | reply_overrides.json | Client | **Done** |
| Add-car next-step prompts | add_car_rules.json | Industry | **Done** |
| **broker_next_step** | triage.py _get_category_templates | Industry | **High** |
| **client_prep** | triage.py _get_category_templates | Industry | **High** |
| Welcome copy | Hardcoded UI | Client | Medium |
| Handoff phrasing in UI | Hardcoded UI | Client | Medium |
| Workbench labels | Hardcoded UI | Client | Medium |
| Trust/reassurance copy | Hardcoded UI | Client | Low |
| Package/trial labels | Hardcoded | Industry + Client | Low |
| Scenario next-step text | Hardcoded triage | Industry | Medium |
| Quick-start button labels | Hardcoded UI | Industry (ids) + Client (labels) | Medium |
| Status/badge labels | Hardcoded UI | Industry | Low |

---

## 2. Already Configurable (No Change)

- `configs/industries/insurance/markers.json`
- `configs/industries/insurance/reply_templates.json`
- `configs/industries/insurance/add_car_rules.json`
- `configs/clients/chen_kui/handoff_phrases.json`
- `configs/clients/chen_kui/reply_overrides.json`

---

## 3. Top Extraction Targets (This Sprint)

1. **broker_next_step + client_prep** → `configs/industries/insurance/category_templates.json`
2. **Common fallbacks** → `configs/common/workflow_defaults.json`
3. **UI copy (office, handoff, welcome)** → `configs/clients/chen_kui/ui_copy.json` (or similar)

---

## 4. Intentionally Deferred

- VALID_CATEGORIES, VALID_URGENCIES (schema; low value)
- Handoff thresholds (rules; complex to extract)
- FORMAL_DRAFT_MARKERS, UNSENDABLE_DRAFT_MARKERS (draft quality; could move to common later)
- Full scenario package as config (doc is sufficient for now)

---

## 5. Risky to Extract Now

- Classification logic (core rules; stays in code)
- LLM prompt structure (separate concern)
- Case store schema (state; not config)

---

*See also: 04_CONFIGURATION_MIGRATION_EXTRACTION_SPEC.md*
