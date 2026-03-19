# Scenario Logic Center — Doc Index

**Purpose:** Single entry point for scenario logic documentation. Use this when you need to understand what scenarios exist, how they work, and what is strong/weak.

---

## 1. Read First

| Order | Doc | Purpose |
|-------|-----|---------|
| 1 | [01_SCENARIO_LOGIC_CENTER_BLUEPRINT.md](01_SCENARIO_LOGIC_CENTER_BLUEPRINT.md) | Why a logic center; what we strengthen; what we defer |
| 2 | [02_SCENARIO_INVENTORY_SPEC.md](02_SCENARIO_INVENTORY_SPEC.md) | Which scenarios; what each card shows |
| 3 | [07_FOUNDER_INSPECTION_NOTES.md](07_FOUNDER_INSPECTION_NOTES.md) | What founder should inspect; how to use |

---

## 2. Specs (When Needed)

| Doc | Purpose |
|-----|---------|
| [03_LOGIC_VISIBILITY_SPEC.md](03_LOGIC_VISIBILITY_SPEC.md) | How to present route, ask-next, handoff, broker_next_step |
| [04_SCENARIO_STATUS_HEALTH_SPEC.md](04_SCENARIO_STATUS_HEALTH_SPEC.md) | Strong/medium/weak; simulation coverage; fix-now/fix-next |
| [05_EXECUTION_OUTLINE.md](05_EXECUTION_OUTLINE.md) | Workstreams; loop plan |
| [06_ACCEPTANCE_REVIEWABILITY_CRITERIA.md](06_ACCEPTANCE_REVIEWABILITY_CRITERIA.md) | Pass criteria for founder, broker, reuse |

---

## 3. Related Project Docs

| Doc | Purpose |
|-----|---------|
| `docs/STANDARD_SCENARIO_PACKAGE.md` | Canonical 7 scenarios; sellable package |
| `docs/MATURE_INTAKE_SKELETON.md` | Detect → ask → enough? → hand off |
| `docs/CHEN_KUI_TRIAL_PACK.md` | Trial scenarios; value validation |
| `docs/CONFIG_EXTRACTION_GUIDE.md` | Config structure; common/industry/client |
| `docs/trial/FIX_NOW_QUEUE_SPEC.md` | Fix now / fix next / defer |

---

## 4. Config Sources

| Config | Purpose |
|--------|---------|
| `configs/industries/insurance/markers.json` | Intent detection markers |
| `configs/industries/insurance/category_templates.json` | broker_next_step, client_prep |
| `configs/industries/insurance/reply_templates.json` | First-turn reply templates |
| `configs/clients/chen_kui/handoff_phrases.json` | Handoff reply strings |
| `configs/inbox_triage_scenarios.json` | Regression test scenarios |
| `configs/simulation_assistant_scenarios.json` | Simulation Assistant flows |

---

## 5. UI Entry

**Scenario Logic Center page:** `/workbench/scenario-logic-center`

- In AI Workbench menu: **Scenario Logic**
- Shows: scenario inventory, maturity, fix status, route/ask-next/handoff/broker step
- Config layer: common / industry / client

---

*End of index*
