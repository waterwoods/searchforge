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

## PRIMARY — Current Source of Truth

| Doc | Purpose |
|-----|---------|
| `AGENTS.md` | Single entry point for agents |
| `docs/CURRENT_PRODUCT_SHAPE.md` | **Current** product, deployment, paid-pilot env requirements |
| `docs/SIMPLIFICATION_MASTER_PLAN.md` | **Reduction roadmap** — what to hide/archive/delete; brutally honest inventory |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | **Macro blueprint (north star)** — Unified Intake product direction, business framing, state-driven flow, client-pack strategy, technical evolution; align major sprints |
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
| `docs/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | **Supporting / investor framing only** — not pilot runtime truth; see `SIMPLIFICATION_MASTER_PLAN.md` |
| `docs/CHEN_KUI_TRIAL_PACK.md` | Chen Kui trial pack: scenarios, order, value validation questions, pilot offer |
| `docs/trial/INDEX.md` | **Real Broker Trial Package** — 1-week pilot: blueprint, scope, scenario pack, metrics, workflow, founder notes |
| `docs/trial/TRIAL_EXECUTION_BLUEPRINT.md` | **Trial execution readiness** — last-mile hardening, runbook, handoff spec |
| `docs/trial/FOUNDER_LAUNCH_NOTES.md` | **Trial launch** — single entry: what to do, say, inspect, collect; `bash scripts/trial_launch_check.sh` |
| `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` | Retrieval boundaries: what goes into RAG vs rules/config vs state |
| `docs/CURRENT_SYSTEM_FILE_CLASSIFICATION.md` | File-to-layer mapping, what lives where |
| `docs/CONFIG_EXTRACTION_GUIDE.md` | Config structure, what is extracted, common/industry/client boundary |
| `docs/CLIENT_PACK_FOUNDATION.md` | Package model: common base → industry pack → client pack |
| `docs/DEPLOYMENT_READINESS.md` | Vercel + Cloud Run deployment checklist, env vars, cost notes |
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Release operations: pre/deploy/post, gotchas |
| `docs/runbooks/RELEASE_CHECKLIST.md` | Every-release checklist (use before claiming success) |

---

## Primary vs Supporting (Broker Daily Use)

| Use | Docs |
|-----|------|
| **Primary** — read first | `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md`, `docs/ANDY_QUICK_START.md`, `docs/ANDY_2MIN_BEFORE_DEMO.md` |
| **Supporting** — when needed | `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md`, `docs/BROKER_DEMO_CHECKLIST.md`, `docs/BROKER_MEETING_PACKAGE.md`, `docs/BROKER_DEMO_SCRIPT_15MIN.md`, `docs/broker_value_feedback_form.md`, `docs/FOUNDER_DEMO_SOP.md` (Unified Intake / Chen Kui trial) |

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
