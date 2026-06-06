# Project Doc System Map — Broker Assistant

**Scope:** California Auto Insurance Broker Assistant only.

## Agent Entry Point

**Cursor / OpenClaw:** Read [AGENTS.md](../AGENTS.md) first. It defines:
- Default reading order
- Default script path (run_demo_local.sh, demo_pre_checklist.sh)
- Runtime paths (8001 default, 8000 Docker, recovery)
- Scope guardrail

Then use this map to find specific docs.

**Multi-agent collaboration:** `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` — roles, working loop, handoffs.

---

## START HERE — ≤10 docs (operators, founders, support)

Read in this order. **Ignore everything else** until you need a specific task.

| # | Doc | Who |
|---|-----|-----|
| 1 | `AGENTS.md` | Agents / engineers |
| 2 | `docs/CURRENT_PRODUCT_SHAPE.md` | Everyone — what the product is *today* |
| 3 | `docs/goals/insurance_paid_pilot_goal.md` | Founders — scope in/out |
| 4 | `docs/runbooks/OPERATOR_CHEAT_SHEET.md` | Operators — deploy, health, 2am |
| 4a | `docs/runbooks/OPERATOR_SURFACE.md` | Everyone — **target operator surface** (10 scripts, 10 docs, 5 endpoints) |
| 4b | `docs/runbooks/OPERATOR_IGNORE_LIST.md` | Operators — what to ignore (vectors, /ready, sprints) |
| 5 | `docs/runbooks/SUPPORT_TRUTH_MAP.md` | Support — manifest keys, health |
| 6 | `docs/runbooks/DEPLOY_TRUTH_MAP.md` | Operators — which deploy script |
| 7 | `docs/ANDY_QUICK_START.md` | Founders — local demo |
| 8 | `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Operators — release steps |
| 9 | `docs/SIMPLIFICATION_MASTER_PLAN.md` | Engineers — what to delete/hide |
| 10 | `docs/trial/INDEX.md` | Founders — real broker trial |
| — | `docs/BROKER_ONE_PAGER.md` | **Brokers** — what it is, why pay, how to try |
| — | `docs/FOUNDER_ONE_PATH.md` | **Founders** — single canonical path |
| — | `docs/P9_BROKER_SURFACE_PLAN.md` | P9 customer journey + confusion lists |

**Paid pilot only?** Skip platform blueprints below; `CURRENT_PRODUCT_SHAPE` wins over any blueprint.

**Macro product direction (not daily ops):** `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — read before large product sprints, not before every deploy.

---

## PRIMARY — Extended reference (beyond START HERE)

| Doc | Purpose |
|-----|---------|
| `AGENTS.md` | Single entry point for agents |
| `docs/CURRENT_PRODUCT_SHAPE.md` | **Current** product, deployment, paid-pilot env requirements |
| `docs/SIMPLIFICATION_MASTER_PLAN.md` | **Reduction roadmap** — what to hide/archive/delete; brutally honest inventory |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | **Macro blueprint** — product direction for major sprints; **not** deploy/runtime truth (see START HERE) |
| `docs/goals/insurance_paid_pilot_goal.md` | Master goal, scope, deliverables |
| `docs/STANDARD_SCENARIO_PACKAGE.md` | Sellable package: 7 scenarios, broker value, demo path |
| `docs/ANDY_QUICK_START.md` | One file before running demo |
| `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | Broker meeting runbook |
| `docs/runbooks/RUNTIME_PATH_STANDARD.md` | Port 8001/8000, recovery |
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Quality bar before demo |
| `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` | Drift detection, when to run |
| `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` | Roles, working loop, handoffs |
| `docs/MATURE_INTAKE_SKELETON.md` | Shared intake flow: detect → ask → enough? → hand off |
| `docs/sprints/MATURE_SKELETON_COMMERCIAL_INTAKE_BACKBONE/03_PAGE_FLOW_STATE_HANDOFF_BACKBONE_SPEC.md` | **Mature backbone** — page, flow, state, handoff structure; borrow from Stripe/Amazon/Intercom/Zendesk; future-sprint reference |
| `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md` | Lightweight state machine, field progress, follow-up type strategy |
| `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md` | Architecture layers: rules, knowledge, client, state, tests |
| `docs/BROKER_ONE_PAGER.md` | **Broker customer** — one page: what, why pay, try, support |
| `docs/BROKER_DEMO_FLOW.md` | Founder → broker demo steps |
| `docs/BROKER_TRIAL_PLAYBOOK.md` | Broker 7-day trial playbook |
| `docs/FOUNDER_ONE_PATH.md` | **Founder** — run, validate, demo, deploy, trial, support |
| `docs/DEMO_STORY.md` | Demo narrative + 15/5/60 sec variants |
| `docs/TRIAL_ONE_PATH.md` | Trial Day 0–7 — single path |
| `docs/CUSTOMER_LANGUAGE_GUIDE.md` | Engineer → broker vocabulary |
| `docs/trial/INDEX.md` | **Real Broker Trial** — templates + launch command |
| `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` | Retrieval boundaries: what goes into RAG vs rules/config vs state |
| `docs/CURRENT_SYSTEM_FILE_CLASSIFICATION.md` | File-to-layer mapping, what lives where |
| `docs/CONFIG_EXTRACTION_GUIDE.md` | Config structure, what is extracted, common/industry/client boundary |
| `docs/CLIENT_PACK_FOUNDATION.md` | Package model: common base → industry pack → client pack |
| `docs/DEPLOYMENT_READINESS.md` | Vercel + Cloud Run deployment checklist, env vars, cost notes |
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Release operations: pre/deploy/post, gotchas |
| `docs/runbooks/OPERATOR_CHEAT_SHEET.md` | **2am operator path** — deploy, health, env, legacy vs prod |
| `docs/runbooks/DEPLOY_TRUTH_MAP.md` | Deploy scripts: which to run, which to avoid |
| `docs/runbooks/SUPPORT_TRUTH_MAP.md` | Support manifest, keys, health for operators |
| `docs/runbooks/RELEASE_CHECKLIST.md` | Every-release checklist (use before claiming success) |

---

## Future exploration — NOT runtime truth

**Do not implement from these.** Useful for investor framing, historical architecture thinking, or post-revenue exploration. When any of these conflict with `docs/CURRENT_PRODUCT_SHAPE.md`, **CURRENT_PRODUCT_SHAPE wins**.

| Doc | Class | Use |
|-----|-------|-----|
| `docs/archive/platform/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | Investor / platform fantasy | Fundraising narrative — dangerous as a build list |
| `docs/archive/platform/` | Platform blueprints + AutoTuner docs | Archived — not deploy truth |
| `docs/archive/sprint_reports/` | Historical `*_SPRINT_REPORT.md` | Point-in-time — ignore unless debugging history |
| `docs/sprints/archive/FUTURE_SAAS_OPERATING_SYSTEM_SPRINT.md` | Historical architecture | Multi-tenant OS speculation — archived |
| `docs/sprints/archive/FUTURE_SAAS_OPERATING_SYSTEM_FINAL_REPORT.md` | Historical report | Same — not shipped |
| `docs/sprints/archive/LONG_HORIZON_SAAS_OPERATING_SYSTEM_SPRINT.md` | Historical architecture | Long-horizon convergence — not current deploy |
| `docs/sprints/archive/PAID_SAAS_OPERATING_MODEL_ARCHITECTURE_CONVERGENCE_SPRINT.md` | Historical convergence | Superseded by `CURRENT_PRODUCT_SHAPE.md` |
| `docs/sprints/archive/MINIMAL_PAID_SAAS_SURVIVABILITY_SPRINT.md` | Reduction sprint record | Context only — active reduction is `SIMPLIFICATION_*` docs |

**Still operational (not platform fantasy):** `docs/MULTI_AGENT_OPERATING_MODEL_V1.md` — how agents/founders work together today.

---

## Primary vs Supporting (Broker Daily Use)

| Use | Docs |
|-----|------|
| **Primary** — read first | `docs/BROKER_ONE_PAGER.md`, `docs/DEMO_STORY.md`, `docs/BROKER_DEMO_FLOW.md`, `docs/ANDY_QUICK_START.md` |
| **Supporting** — when needed | `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md`, `docs/ANDY_2MIN_BEFORE_DEMO.md` |
| **Archived (P9)** | `docs/archive/p9_broker_surface/` — pre-P9 broker/founder/trial overlap |

Primary = single source of truth. Supporting = lighter summaries or one-purpose docs (checklist, feedback form).

---

## Doc Categories

| Category | Path | Purpose |
|----------|------|---------|
| **goals** | `docs/goals/` | Master goal, pilot mission, scope, Unified Intake MVP |
| **standards** | `docs/standards/` | Quality bar: what must be true before demo |
| **runbooks** | `docs/runbooks/` | How to run demo, ports, meeting pack, Unified Intake MVP |
| **guardrails** | `docs/guardrails/` | Drift detection, scripts, when to run |
| **reports** | `docs/BROKER_REPORTS_INDEX.md` | Sprint reports, diagnosis (index) |
| **archive** | `docs/archive/` | Historical sprint/diagnosis reports |
| **supporting** | `docs/supporting/` | Secondary: PROMPT*, OPERATOR*, STEP* working docs |

## Read First

1. **New to project:** `docs/goals/insurance_paid_pilot_goal.md`
2. **Running a demo:** `docs/ANDY_QUICK_START.md` → `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md`
3. **Before broker meeting:** `docs/ANDY_2MIN_BEFORE_DEMO.md`
4. **Major Unified Intake / product-architecture sprint:** Read `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` first; align sprint blueprints with it. If a sprint direction conflicts with the outline, update the outline or explicitly justify the divergence before implementation.

## Primary for Daily Use

| Task | Doc |
|------|-----|
| Demo prep | `docs/ANDY_QUICK_START.md`, `docs/ANDY_2MIN_BEFORE_DEMO.md` |
| Deploy / 2am ops | `docs/runbooks/OPERATOR_CHEAT_SHEET.md`, `docs/runbooks/DEPLOY_TRUTH_MAP.md` |
| Support / prod debug | `docs/runbooks/SUPPORT_TRUTH_MAP.md` |
| Broker meeting | `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` |
| Ports / runtime | `docs/runbooks/RUNTIME_PATH_STANDARD.md` |
| Quality bar | `docs/BROKER_DEMO_QUALITY_STANDARD.md` |
| Drift check | `docs/BROKER_DEMO_DRIFT_GUARDRAIL.md` |
| Something wrong | `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` |

## Index Files

- `docs/goals/INDEX.md`
- `docs/standards/INDEX.md`
- `docs/runbooks/INDEX.md`
- `docs/guardrails/INDEX.md`
- `docs/BROKER_REPORTS_INDEX.md` — broker sprint/diagnosis reports
- `docs/archive/INDEX.md` — historical reports
- `docs/supporting/INDEX.md` — secondary/working docs (PROMPT*, OPERATOR*, STEP*)

## Archive (Historical)

Sprint reports and diagnosis docs from past work. **Not for daily use.** See `docs/archive/INDEX.md`.

Examples: Documentation Operating System v1, Agent Entry-Point Integration, Runtime Path Standardization, 503 root cause, etc.
