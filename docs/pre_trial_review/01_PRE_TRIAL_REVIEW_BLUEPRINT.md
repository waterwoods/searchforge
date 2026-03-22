# Pre-Trial Review Blueprint

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why Pre-Trial Review Now

The product has evolved from demo → sellable package → scenario hardening → Real Broker Trial Package → Scenario Logic Center. Trial docs, simulation pack, and client-aware wiring exist. **The next step is real broker usage.** Before that, we need a structured review to decide:

- What is strong enough for trial
- What is medium and should be watched closely
- What is weak and should not be trusted yet
- What belongs in fix-now / fix-next / defer
- What exact flows should be in the first real broker trial

---

## 2. What This Sprint Does

| Activity | Purpose |
|----------|---------|
| **Review** | Current system state, trial docs, scenario package, scenario logic center |
| **Classify** | Each major scenario as strong / usable-with-caution / weak |
| **Tighten** | Fix-now / fix-next / defer queue; first trial scope |
| **Summarize** | Founder-readable report; 中文宏观总结 |

---

## 3. What This Sprint Does NOT Do

- Broad new feature development
- Random feature additions
- Platform work beyond trial readiness
- Expanding scope into other verticals

---

## 4. Core Principle

**Review, readiness judgment, and trial scope discipline.** Not feature creep.

---

## 5. Inputs

| Input | Source |
|-------|--------|
| Standard scenario package | `docs/STANDARD_SCENARIO_PACKAGE.md` |
| Realistic simulation results | `scripts/guardrail_inbox_triage.sh` (64/64 rule-based, 41 multi-turn, 27 SIM) |
| Trial package | `docs/CHEN_KUI_TRIAL_PACK.md`, `docs/trial/` |
| Kickoff docs | `docs/trial/kickoff/` |
| Client-aware wiring | Client identity persistence; handoff phrases by client |
| Scenario logic center | `configs/scenario_logic_center.json`, `/workbench/scenario-logic-center` |

---

## 6. Outputs

| Output | Location |
|--------|----------|
| Pre-Trial Review Blueprint | This doc |
| Trial Scope Review Spec | `02_TRIAL_SCOPE_REVIEW_SPEC.md` |
| Scenario Readiness Review Spec | `03_SCENARIO_READINESS_REVIEW_SPEC.md` |
| Fix-Now / Fix-Next / Defer Review Spec | `04_FIX_NOW_FIX_NEXT_DEFER_REVIEW_SPEC.md` |
| Execution Outline | `05_EXECUTION_OUTLINE.md` |
| Acceptance / Trial Review Criteria | `06_ACCEPTANCE_TRIAL_REVIEW_CRITERIA.md` |
| Founder Review Notes | `07_FOUNDER_REVIEW_NOTES.md` |
| Pre-Trial Review Report | `PRE_TRIAL_REVIEW_REPORT.md` |

---

*End of Blueprint*
