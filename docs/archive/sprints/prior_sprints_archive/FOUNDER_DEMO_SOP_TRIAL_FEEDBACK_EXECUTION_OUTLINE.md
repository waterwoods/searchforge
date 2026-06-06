# Founder Demo SOP + Real Trial Feedback — Execution Outline

**Sprint:** Founder Demo SOP + Real Trial Feedback Sprint  
**Created:** 2026-03-14

---

## Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Control docs | Planner | Blueprint, Execution Outline, Acceptance Criteria |
| 2 | Demo SOP | Demo-flow designer | Pre-demo, intro, path, fallbacks |
| 3 | Demo path | Demo-flow designer | Primary path, backup path, top 3 scenarios |
| 4 | Feedback questions | Product critic | 3–5 post-trial questions |
| 5 | Loop 1 rehearsal | Simulation/QA | Rehearse, identify friction |
| 6 | Loop 2 fixes | Frontend/UX | Top 1–3 fixes, rerun checks |
| 7 | Loop 3 (optional) | Release reviewer | One more fix if obvious gain |
| 8 | Final judgment | Release reviewer | SOP ready? Best path? Next move? |

---

## Role Assignment

- **Planner / architect:** Control docs, scope guardrail
- **Demo-flow designer:** SOP, path, scenario order
- **Frontend / UX worker:** Wording, labels, clarity fixes
- **Simulation / QA worker:** Guardrail, smoke check, rehearsal
- **Product critic / buyer-perspective:** Feedback questions, hesitation points
- **Acceptance / release reviewer:** Final judgment, next step

---

## Simulation / Rehearsal Sequence

1. Run `bash scripts/guardrail_inbox_triage.sh` → PASS
2. Run `bash scripts/unified_intake_smoke_check.sh` → PASS
3. Run `cd ui && npm run build` → PASS
4. Manual: Open http://localhost:5173/workbench/unified-intake
5. Rehearse: Load founder demo queue → Cancellation risk first
6. Rehearse: Simulation Assistant → SIM1, SIM2, SIM3
7. Rehearse: Customer Entry → paste cancellation warning, start case
8. Evaluate: What looked strongest? What looked weakest?

---

## Likely Loop Count

- **Loop 1:** Rehearse, identify friction
- **Loop 2:** Fix top 1–3 issues, rerun
- **Loop 3:** Optional, only if obvious gain

---

## What Will Be Judged

- Is the demo SOP clear enough for Andy to use tomorrow?
- Is the primary path the strongest?
- Are the top 3 scenarios convincing?
- Are feedback questions commercially useful?
- What still blocks trial confidence?

---

*See: `docs/sprints/FOUNDER_DEMO_SOP_TRIAL_FEEDBACK_SPRINT_BLUEPRINT.md`*
