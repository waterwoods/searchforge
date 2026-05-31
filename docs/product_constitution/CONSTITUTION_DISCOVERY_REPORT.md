# Constitution Discovery Report — P14-A

**Sprint:** P14-A Constitution Discovery  
**Date:** 2026-05-31  
**Method:** Full-repository scan of product, trial, goal, sprint, standard, runbook, and archive docs. No runtime changes.

---

## Executive Summary

The repository already contains **~70% of a product constitution**, scattered across converged SSOT docs (P8–P11), goals, standards, and one macro blueprint. The **core commercial promise is coherent** across 10+ active sources: *paste messy message → structured case → draft → broker sends*. What is missing is a **single constitution file** that resolves known conflicts and demotes stale RAG-demo artifacts.

**P12 and P13 do not exist** in the repository. P10 (trial prep) and P11 (product reality) are the most recent high-value discovery sprints.

---

## Authority Hierarchy (Discovered)

When documents conflict, this hierarchy is already implied across `PROJECT_DOC_SYSTEM_MAP.md`, `CURRENT_PRODUCT_SHAPE.md`, and sprint README:

| Rank | Document class | Wins on |
|------|----------------|---------|
| 1 | `CURRENT_PRODUCT_SHAPE.md` | Runtime, deployment, persistence |
| 2 | Converged broker/founder paths | Customer-facing truth, trial, demo |
| 3 | `SIMPLIFICATION_MASTER_PLAN.md` | What to hide/archive/delete |
| 4 | `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro direction (major sprints only) |
| 5 | `docs/sprints/P10–P11/` | Discovery audits (historical after convergence) |
| 6 | `docs/goals/insurance_paid_pilot_goal.md` | **Stale** — RAG demo era |
| 7 | `docs/archive/**` | Historical only |

---

## Document Inventory

### Tier A — Active SSOT (Use for Constitution)

| File | Purpose | Audience | Active? | Overlaps | Conflicts | Score |
|------|---------|----------|---------|----------|-----------|-------|
| `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime/deployment/persistence truth | Engineers, operators, founders | **Yes** | SIMPLIFICATION, DEPLOYMENT_READINESS | Master outline on wedge | **10** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/CURRENT_PRODUCT_TRUTH.md` | Customer-facing product truth | Broker, founder, sales | **Yes** | BROKER_ONE_PAGER, P10 trial model | Add-Car vs cancellation | **10** |
| `docs/BROKER_ONE_PAGER.md` | Broker sales one-pager | Broker prospect | **Yes** | CURRENT_PRODUCT_TRUTH | Pricing absent; 5 vs 7 scenarios | **9** |
| `docs/FOUNDER_ONE_PATH.md` | Clone → demo → deploy → trial | Founder | **Yes** | OPERATOR_SURFACE, TRIAL_ONE_PATH | None material | **10** |
| `docs/TRIAL_ONE_PATH.md` | 7-day trial Day 0–7 | Founder, broker | **Yes** | BROKER_TRIAL_PLAYBOOK | Simulation dependency vs hidden UI | **9** |
| `docs/P9_BROKER_SURFACE_PLAN.md` | Customer journey + confusion lists | Product, founder | **Yes** | P9 audit, DEMO_STORY | SIM1–SIM3 in trial section | **9** |
| `docs/PROJECT_DOC_SYSTEM_MAP.md` | Doc hierarchy and START HERE | All roles | **Yes** | AGENTS.md | None | **9** |
| `docs/SIMPLIFICATION_MASTER_PLAN.md` | Reduction roadmap | Engineers | **Yes** | CURRENT_PRODUCT_SHAPE | Platform naming in repo | **8** |
| `docs/CUSTOMER_LANGUAGE_GUIDE.md` | Engineer → broker vocabulary | Engineers, support | **Yes** | UI copy (partially applied) | UI drift | **8** |
| `docs/DEMO_STORY.md` | 15/5/60 sec demo narrative | Founder | **Yes** | BROKER_DEMO_FLOW | Customer Entry optional vs UI default | **8** |
| `docs/BROKER_TRIAL_PLAYBOOK.md` | Broker-facing trial steps | Broker | **Yes** | TRIAL_ONE_PATH | Simulation Assistant required | **8** |
| `docs/BROKER_DEMO_FLOW.md` | Demo walkthrough | Founder | **Yes** | DEMO_STORY | Tab naming drift | **7** |
| `docs/STANDARD_SCENARIO_PACKAGE.md` | 7 sellable scenarios | Founder, sales | **Yes** | BROKER_ONE_PAGER (5 scenarios) | 7 vs 5 scenario count | **7** |
| `docs/trial/INDEX.md` | Trial entry + templates | Founder | **Yes** | TRIAL_ONE_PATH | None | **8** |
| `docs/goals/UNIFIED_INTAKE_MVP_MASTER_GOAL.md` | MVP definition + I/O model | Product, engineers | **Yes** | Standards, triage code | Identity "not in v1" vs master outline | **8** |
| `docs/goals/BROKER_INBOX_TRIAGE_MASTER_GOAL.md` | Triage mission | Product | **Yes** | UNIFIED_INTAKE_MVP goal | Duplicate of above | **7** |
| `docs/standards/BROKER_INBOX_TRIAGE_STANDARD.md` | 6-field output + categories | Engineers, QA | **Yes** | guardrail scripts | UI field naming differs | **9** |
| `docs/standards/UNIFIED_INTAKE_MVP_STANDARD.md` | Workbench quality bar | Engineers, QA | **Yes** | BROKER_INBOX_TRIAGE_STANDARD | None | **8** |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro blueprint, Add-Car wedge | Major sprints | **Partial** | SIMPLIFICATION, P11 | **Add-Car-first vs cancellation-first** | **6** |
| `docs/runbooks/OPERATOR_SURFACE.md` | 10 scripts, 10 docs, 5 endpoints | Operators | **Yes** | FOUNDER_ONE_PATH | None | **8** |
| `docs/runbooks/OPERATOR_IGNORE_LIST.md` | Cognitive load reduction | Operators | **Yes** | SIMPLIFICATION | None | **7** |

### Tier B — Sprint Audits (Discovery Evidence, Not Runtime SSOT)

| File | Purpose | Audience | Active? | Overlaps | Conflicts | Score |
|------|---------|----------|---------|----------|-----------|-------|
| `docs/sprints/P10_REAL_BROKER_TRIAL_PREPARATION_SPRINT/P10_FINAL_AUDIT.md` | Chen Kui trial readiness | Founder | **Yes (evidence)** | P11 | None new | **9** |
| `docs/sprints/P10_REAL_BROKER_TRIAL_PREPARATION_SPRINT/CURRENT_TRIAL_MODEL.md` | Trial truth snapshot | Founder | **Yes (evidence)** | TRIAL_ONE_PATH | UI default tab | **9** |
| `docs/sprints/P10_REAL_BROKER_TRIAL_PREPARATION_SPRINT/FRICTION_AUDIT.md` | 50 friction points | Product | **Yes (evidence)** | P11 TOP_50 | None | **8** |
| `docs/sprints/P10_REAL_BROKER_TRIAL_PREPARATION_SPRINT/DEMO_AUDIT.md` | Demo deliverability | Founder | **Yes (evidence)** | DEMO_STORY | Customer Entry default | **8** |
| `docs/sprints/P10_REAL_BROKER_TRIAL_PREPARATION_SPRINT/PAYMENT_READINESS.md` | Payment blockers | Founder | **Yes (evidence)** | P11 blockers | None | **8** |
| `docs/sprints/P10_REAL_BROKER_TRIAL_PREPARATION_SPRINT/TRIAL_READINESS_SCORE.md` | Script-level readiness | Operator | **Yes (evidence)** | trial_launch_check | Script PASS ≠ broker-ready | **7** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/P11_FINAL_AUDIT.md` | Paid SaaS viability | Founder | **Yes (evidence)** | P10 | None | **10** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/TOP_20_BLOCKERS_TO_PAYMENT.md` | Payment blockers ranked | Founder, sales | **Yes (evidence)** | P10 PAYMENT | None | **9** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/TOP_50_REASONS_A_BROKER_WOULD_NOT_PAY.md` | Churn reasons | Product | **Yes (evidence)** | Friction audit | None | **8** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/COMPETITIVE_AUDIT.md` | Competitive positioning | Founder | **Yes (evidence)** | CURRENT_PRODUCT_TRUTH | None | **8** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/30_DAY_EXECUTION_PLAN.md` | Week-by-week plan | Founder | **Yes (evidence)** | P10 30-day plan | Duplicate plans | **7** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/FOUNDER_REFLECTION.md` | Stop/keep/obsess lists | Founder | **Yes (evidence)** | P10 verdict | None | **9** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/TOP_30_VALUE_POINTS.md` | Value articulation | Sales | **Yes (evidence)** | BROKER_ONE_PAGER | None | **7** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/TOP_30_WORKBENCH_IMPROVEMENTS.md` | UI fix backlog | Product | **Yes (evidence)** | Friction audit | None | **7** |
| `docs/sprints/P11_PRODUCT_REALITY_AUDIT/TRIAL_REALITY_AUDIT.md` | Day 1/7 unsupervised scores | Founder | **Yes (evidence)** | P10 | None | **8** |
| `docs/P9_FINAL_AUDIT.md` | P9 collapse audit | Founder | **Historical** | FOUNDER_ONE_PATH | Pre-P10 findings | **6** |
| `docs/P8_FINAL_AUDIT.md` | Lab isolation audit | Engineers | **Historical** | SIMPLIFICATION | Pre-P9 | **5** |

### Tier C — Stale or Superseded (Archive or Rewrite)

| File | Purpose | Audience | Active? | Overlaps | Conflicts | Score |
|------|---------|----------|---------|----------|-----------|-------|
| `docs/goals/insurance_paid_pilot_goal.md` | Original paid pilot mission | Founder | **Stale** | CURRENT_PRODUCT_SHAPE | **RAG demo vs workbench** | **3** |
| `docs/business_rules/insurance_broker_pilot_rules.md` | RAG demo business rules | Engineers | **Stale** | demo_quick_validate | **Unified Intake not mentioned** | **2** |
| `docs/goals/BROKER_ASSISTANT_MASTER_GOAL.md` | Earlier assistant goal | Historical | **Stale** | BROKER_INBOX_TRIAGE | RAG era | **3** |
| `docs/archive/p9_broker_surface/**` | Pre-P9 broker/trial specs | Historical | **Archived** | TRIAL_ONE_PATH | 12+ duplicate trial paths | **2** |
| `docs/archive/platform/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | Platform/investor fantasy | Investor | **Explicitly not SSOT** | Master outline | Platform vs SaaS | **1** |
| `docs/archive/sprints/**` | Historical sprint execution | Engineers | **Archived** | Many product blueprints | Add-car sprints, workbench specs | **2–4** |
| `docs/pre_trial_review/**` | Pre-trial review sprint | Historical | **Superseded** | trial_launch_check | Duplicate entry | **3** |

### Tier D — Supporting (Reference, Not Constitution Core)

| File | Purpose | Score |
|------|---------|-------|
| `docs/DEPLOYMENT_READINESS.md` | Vercel + Cloud Run checklist | 7 |
| `docs/DEPRECATED_PATHS.md` | Dead code/flag registry | 6 |
| `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` | Agent collaboration | 5 |
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Demo quality bar | 6 |
| `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` | Drift detection | 6 |
| `docs/guardrails/BROKER_INBOX_TRIAGE_GUARDRAILS.md` | Triage guardrails | 7 |
| `docs/runbooks/BROKER_INBOX_TRIAGE_RUNBOOK.md` | Operator runbook | 6 |
| `configs/clients/chen_kui/**` | Client pack (copy, scenarios) | 7 |
| `AGENTS.md` | Agent entry point | 8 |
| `README.md` | Repo overview | 7 |

---

## Missing Sprint References

| Expected | Status |
|----------|--------|
| P12 | **Not found** in repository |
| P13 | **Not found** in repository |
| P10 | Found — trial preparation sprint (complete) |
| P11 | Found — product reality audit (complete) |

---

## Discovery by Constitution Category

| Category | Best existing source | Maturity |
|----------|---------------------|----------|
| Product definition | `CURRENT_PRODUCT_TRUTH.md`, `BROKER_ONE_PAGER.md` | **Strong** |
| Customer definition | `P9_BROKER_SURFACE_PLAN.md`, Chen Kui references | **Strong** |
| Broker definition | Same + `CUSTOMER_LANGUAGE_GUIDE.md` | **Strong** |
| Trial definition | `TRIAL_ONE_PATH.md`, P10/P11 audits | **Strong** |
| Value proposition | P11 TOP_30_VALUE_POINTS, BROKER_ONE_PAGER | **Strong** |
| Commercial model | P11 payment blockers, P10 payment readiness | **Partial** (no pricing on one-pager) |
| Workflow | FOUNDER_ONE_PATH, workbench standards | **Partial** (UI/doc split) |
| Capability definitions | MVP goals + standards + master outline | **Partial** (conflicts) |
| Acceptance criteria | guardrail scripts, trial success criteria | **Strong** |
| Deployment posture | CURRENT_PRODUCT_SHAPE | **Strong** |
| Success metrics | TRIAL_ONE_PATH, P11 blockers | **Partial** (no ROI logging template) |
| Founder goals | FOUNDER_REFLECTION, P11 30-day plan | **Strong** |
| Pilot goals | insurance_paid_pilot_goal (stale) + P11 | **Split** |
| Business rules | insurance_broker_pilot_rules (stale) | **Weak** |
| Anti-goals | CURRENT_PRODUCT_TRUTH §2, P11 WHAT_NOT_TO_DO | **Strong** |
| Roadmaps | SIMPLIFICATION_MASTER_PLAN, P11 30-day | **Partial** |
| North Star | Master outline vs P11 — **conflicted** | **Split** |

---

## Top Overlap Clusters (Consolidation Candidates)

1. **Product promise cluster:** CURRENT_PRODUCT_TRUTH + BROKER_ONE_PAGER + README + P10 trial model → **already 90% aligned**
2. **Trial cluster:** TRIAL_ONE_PATH + BROKER_TRIAL_PLAYBOOK + trial/INDEX + 12 archived trial specs → **converged except archived noise**
3. **Founder path cluster:** FOUNDER_ONE_PATH + OPERATOR_SURFACE + ANDY_QUICK_START → **converged**
4. **MVP definition cluster:** UNIFIED_INTAKE_MVP_MASTER_GOAL + BROKER_INBOX_TRIAGE_MASTER_GOAL + standards → **merge into constitution capability section**
5. **Scenario cluster:** BROKER_ONE_PAGER (5) + STANDARD_SCENARIO_PACKAGE (7) + demo queue (13) → **needs single scenario list**

---

## Recommended SSOT After P14-A

| Domain | Proposed SSOT |
|--------|---------------|
| Runtime/deploy | `CURRENT_PRODUCT_SHAPE.md` (unchanged) |
| Customer product truth | `UNIFIED_INTAKE_V1_CONSTITUTION_PROPOSAL.md` (new) |
| Founder operations | `FOUNDER_ONE_PATH.md` (unchanged, links to constitution) |
| Broker sales | `BROKER_ONE_PAGER.md` (update pricing + tab guidance) |
| Trial | `TRIAL_ONE_PATH.md` (remove Simulation dependency) |
| Macro direction | Master outline (add explicit subordination to constitution) |

---

*End of constitution discovery report*
