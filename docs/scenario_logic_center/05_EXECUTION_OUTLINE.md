# Scenario Logic Center — Execution Outline

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Workstreams, implementation order, loop plan, validation approach.

---

## 1. Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Control docs | Planner | Blueprint, Inventory, Visibility, Health, Acceptance, Founder Notes |
| 2 | Scenario inventory data | Config worker | configs/scenario_logic_center.json |
| 3 | API endpoint | Backend | GET /api/scenario-logic-center |
| 4 | UI page | Frontend | ScenarioLogicCenterPage.tsx |
| 5 | Navigation | Frontend | Add to AppSider under Unified Intake |
| 6 | Validation | QA | guardrail_inbox_triage.sh, npm run build |

---

## 2. Implementation Order

1. **Phase A** — Create all 7 control docs (Blueprint, Inventory, Visibility, Health, Execution, Acceptance, Founder Notes)
2. **Loop 1** — Build scenario inventory JSON + doc index; minimal API or static load
3. **Loop 2** — Add logic/health/config visibility to each scenario card
4. **Loop 3** — Founder/review hardening (summary header, grouping, status chips)

---

## 3. Loop Plan

| Loop | Target | Validation |
|------|--------|------------|
| 1 | Centralize top scenario inventory; founder mental map lighter | Docs exist; JSON valid |
| 2 | Route, ask-next, handoff, broker_next_step; strong/medium/weak; common/industry/client | UI shows all |
| 3 | Summary header; grouping; clearer status; one inspection path | Founder can understand at a glance |

---

## 4. Validation Approach

- `bash scripts/guardrail_inbox_triage.sh` — Must pass
- `cd ui && npm run build` — Must pass
- Manual: Founder opens Scenario Logic Center; can answer "what scenarios exist?" and "what is strong/weak?"

---

*See also: `06_ACCEPTANCE_REVIEWABILITY_CRITERIA.md`, `07_FOUNDER_INSPECTION_NOTES.md`*
