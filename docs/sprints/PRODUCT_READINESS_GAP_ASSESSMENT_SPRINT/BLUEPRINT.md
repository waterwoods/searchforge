# PRODUCT_READINESS_GAP_ASSESSMENT_SPRINT — Blueprint

**Product:** SearchForge → **Unified Intake** (inbox triage engine + customer entry + broker workbench).

**Sprint type:** Document-driven readiness assessment (no major feature build).

**Created:** 2026-03-25

---

## 1. Purpose

Give the founder a **honest, evidence-based** picture of where Unified Intake stands relative to **near-term paid pilot productization**, after multiple hardening and externalization sprints.

**This sprint answers:**

- What already exists vs partially exists vs missing?
- What should be prioritized next vs explicitly deferred?
- How close is the product to a **narrow, chargeable** pilot?

---

## 2. Why now

Recent work has strengthened **engine behavior**, **client-pack boundaries**, **append/handoff copy**, **positioning docs**, and **regression batteries**. Without a consolidated readiness read, the next work risks **duplication**, **scope creep**, or **overselling** in sales conversations.

**Principle:** More building is not automatically better. **First know the baseline.**

---

## 3. In scope

- Repo and sprint-doc inspection (productization, client pack, acceptance, positioning, operating manual, isolation, append/boundary, residual copy).
- Scoring **12 macro goals** (see `ASSESSMENT_FRAMEWORK_SPEC.md`).
- Gap mapping tied to **sellability**, **broker credibility**, **replication**, **engineering stability**, and **deferrals**.
- Prioritized roadmap + **recommended next 3 sprints** (hypotheses, evidence-linked).
- Founder-facing notes in English + **mandatory simple Chinese summary** in `FINAL_REPORT.md`.

---

## 4. Out of scope

- Implementing new product features or large refactors.
- Production deploy execution (Cloud Run / Vercel verification) — only assessed as a **readiness gap** if evidence shows it is blocking.
- Multi-tenant, Stripe, CRM, carrier APIs (explicit non-goals per `docs/goals/insurance_paid_pilot_goal.md`).

---

## 5. Evidence sources (minimum)

| Area | Primary evidence |
|------|------------------|
| Engine contract | `services/fiqa_api/inbox_triage/triage.py` (`REQUIRED_FIELDS`, `WORKFLOW_STATE_KEYS`) |
| Config / hot-plug | `services/fiqa_api/inbox_triage/config_loader.py`, `configs/clients/*`, `configs/industries/insurance/*` |
| API surface | `services/fiqa_api/routes/inbox_triage.py` |
| Persistence stance | `services/fiqa_api/inbox_triage/case_store.py` (JSON, demo-safe) |
| UI | `ui/src/pages/UnifiedIntakePage.tsx`, `ui/src/api/clientConfig.ts` |
| Regression | `scripts/guardrail_inbox_triage.sh` and referenced Python runners |
| Positioning / pilot | `docs/sprints/NARROW_POSITIONING_AND_OPERATOR_VALUE_SPRINT/`, `docs/STANDARD_SCENARIO_PACKAGE.md`, `docs/trial/`, `docs/sprints/PRE_BROKER_TARGETED_ACCEPTANCE_SPRINT/05_FINAL_REPORT.md`, `docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/FINAL_REPORT.md` |

---

## 6. Deliverables (this folder)

1. `BLUEPRINT.md` (this file)
2. `ASSESSMENT_FRAMEWORK_SPEC.md`
3. `PRODUCT_READINESS_SCORECARD.md`
4. `GAP_ANALYSIS_SPEC.md`
5. `PRIORITY_ROADMAP_SPEC.md`
6. `EXECUTION_OUTLINE.md`
7. `FOUNDER_INSPECTION_NOTES.md`
8. `FINAL_REPORT.md` — single entry for founder + full report structure + 中文总结

---

## 7. Success criteria

- [ ] All 12 macro goals scored with **evidence pointers** and **honest** completion estimates.
- [ ] Gaps classified (sellability / credibility / replication / stability / can wait).
- [ ] Explicit **“do not do yet”** list.
- [ ] Three **next sprint** recommendations with business value + risk + why not alternatives.
- [ ] Chinese summary answers: 做到哪、缺什么、别做什么、下一步最值、离收费试点多远.

---

*End of blueprint*
