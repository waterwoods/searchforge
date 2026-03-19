# Scenario Logic Center — Baseline Audit

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Honest audit of current "logic visibility" state before this sprint.

---

## 1. What Logic Is Already Documented

| Source | What it shows | Visibility |
|--------|---------------|------------|
| `docs/STANDARD_SCENARIO_PACKAGE.md` | 7 canonical scenarios; business value; demo path | **Good** — single doc |
| `docs/MATURE_INTAKE_SKELETON.md` | Detect → ask → enough? → hand off; per-category thresholds | **Good** — design doc |
| `docs/CHEN_KUI_TRIAL_PACK.md` | Trial scenarios; value validation questions | **Good** — trial-focused |
| `docs/CONFIG_EXTRACTION_GUIDE.md` | Config structure; common/industry/client | **Good** — config map |
| `docs/CLIENT_PACK_FOUNDATION.md` | Package model; what is common/industry/client | **Good** — layer doc |
| `configs/category_templates.json` | broker_next_step, client_prep per category | **Scattered** — JSON |
| `configs/industries/insurance/markers.json` | Intent markers | **Scattered** — JSON |
| `configs/industries/insurance/reply_templates.json` | First-turn reply templates | **Scattered** — JSON |
| `configs/inbox_triage_scenarios.json` | Triage regression scenarios | **Scattered** — 60+ items |
| `configs/simulation_assistant_scenarios.json` | Simulation Assistant flows | **Scattered** — JSON |

---

## 2. What Is Still Scattered

| Area | Where it lives | Problem |
|------|----------------|---------|
| **Scenario-to-config mapping** | Mental model; no single doc | Founder must map STANDARD_SCENARIO_PACKAGE → markers → category_templates → triage.py |
| **Handoff thresholds** | triage.py `_add_car_enough_for_handoff`, etc. | In code; not visible in config |
| **Fix-now / fix-next / defer** | docs/trial/FIX_NOW_QUEUE_SPEC.md | Spec exists; no scenario-level mapping |
| **Trial order** | CHEN_KUI_TRIAL_PACK.md, simulation_assistant_scenarios | Two places; not linked |
| **Maturity per scenario** | Sprint reports; inferred | No single "strong/medium/weak" view |

---

## 3. What Is Hard to See in One Place

- **All scenarios at once** — Must open STANDARD_SCENARIO_PACKAGE + MATURE_INTAKE_SKELETON + inbox_triage_scenarios + simulation_assistant
- **Route + ask-next + handoff + broker_next_step** — Spread across MATURE_INTAKE_SKELETON, category_templates, triage.py
- **Common / industry / client** — CONFIG_EXTRACTION_GUIDE explains; no per-scenario view
- **Simulation coverage** — inbox_triage_scenarios has expected_category; simulation_assistant has flow_type; not unified

---

## 4. What the Founder Still Has to Hold in His Head

- Which scenarios are trial-ready vs weak
- Which config file drives which scenario
- What add-car handoff threshold is (year+model+zip)
- When to use fix-now vs fix-next for a given scenario
- How to explain A → B client reuse (what to swap)

---

## 5. What Broker-Side Reviewers Would Still Find Confusing

- No single "here are the scenarios we handle" view
- broker_next_step lives in category_templates; not obvious which scenario maps to which
- Trial order (SIM1–SIM5) vs standard package (7) — relationship unclear

---

## 6. What Future Client Migration Reviewers Would Not Understand

- Without CONFIG_EXTRACTION_GUIDE, unclear what is common vs industry vs client
- No per-scenario "config sources" list
- Handoff phrases are client-specific; reply templates are industry + client override — not visible without reading docs

---

## 7. Classification

| Category | Items |
|----------|-------|
| **Already visible** | STANDARD_SCENARIO_PACKAGE, MATURE_INTAKE_SKELETON, CHEN_KUI_TRIAL_PACK, CONFIG_EXTRACTION_GUIDE |
| **Scattered but recoverable** | category_templates, markers, reply_templates, inbox_triage_scenarios, simulation_assistant |
| **Too hidden** | Handoff thresholds in triage.py; fix-now mapping to scenarios |
| **High-value to centralize now** | Scenario inventory; route/ask-next/handoff/broker_next_step; maturity; config layer |
| **Too detailed / defer** | Full marker lists; LLM prompt text; per-template variants |

---

## 8. Biggest Current Visibility Weakness

**No single Scenario Logic Center.** The founder must mentally assemble from 6+ docs and 5+ config files. No one place answers: "What scenarios exist? What is strong? What does the broker do next? What varies by client?"

---

## 9. Biggest "Too Much in Andy's Head" Problem

**Scenario-to-implementation mapping.** Andy knows: add-car → markers.json add_vehicle + add_car_rules.json + handoff_phrases add_car + triage.py _add_car_enough_for_handoff. But there is no artifact that shows this. A new reviewer or future client migration would need to trace through code and config.

---

## 10. Biggest Review/Reuse Barrier

**Broker audit value.** A broker-side reviewer wants: "Show me what scenarios you handle and what I do next." Today: category_templates has broker_next_step by category, but categories (e.g. customer_question) are umbrella — the real scenarios (add-car, premium review, claim) are sub-intents. The mapping is implicit in triage.py.

---

*End of baseline audit*
