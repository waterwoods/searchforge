# Agent Entry Point — California Auto Insurance Broker Assistant

**For Cursor / OpenClaw:** Read this first when working on the broker project. This file is the single default entry point.

## P20 Product North Star — Mandatory

“We are optimizing the customer journey, not maximizing the feature count.

Build the simplest system that reliably solves the user’s problem.

Smoothness first. Complexity only when proven necessary.”

Chinese product interpretation:

“我们优化的是用户旅程，不是功能数量。

先做最简单、能稳定解决问题的系统。

先保证丝滑；只有真实需求证明必要时，才增加复杂度。”

**Governing SSOT:** `docs/product/p20_product_north_star.md`
**Required worksheet:** `docs/product/p20_production_loop_template.md`
**Founder QA order:** `docs/product/p20_founder_qa_checklist.md`  
**Production acceptance (release / demo / pilot):** `docs/product/p24f_golden_production_qa_flow.md` — one token, one Camry Case, full customer + broker journey. Not prototypes.

Before every P20 implementation, release, or capability review:

- Read both documents above.
- State exactly one user-facing objective and explicit out-of-scope items.
- Enforce One Task, One Next Action, Smallest Working Solution, Complexity
  Stays Inside, Main-Chain First, No Unsupported Choices, Read-After-Write,
  and Capability Done Means User Done.
- Use at most three one-objective automated loops; stop on PASS, never start
  the next capability automatically, and mark three failed loops with an
  unresolved P0 as **BLOCKED**.
- Evaluate the final diff against Reliability, Simplicity, Smoothness,
  Business Value, Scope Control, and every hard release gate in the SSOT.
- Enforce the **Mini Program Build Gate** (North Star §K) **before** Form,
  Navigation, or physical Preview QA: `cd miniapp && npm run build:gate` must
  PASS. Packaging regressions such as `wx://not-found` are automatic release
  blockers.
- If any customer/broker form changed, enforce the **Founder Form Gate**
  (North Star §I): visible value equals canonical state, all required fields
  enable the CTA, optional/Request More/future fields never block, no hidden
  validation rule without Business Contract justification and a visible reason,
  and a real user can complete it without Cursor guidance. Also enforce the
  **Founder State-to-Payload Gate** inside §I: CTA/missing-hint/submit share one
  validator, sibling fields cannot be wiped, and transport/server errors are
  distinguished (never a single opaque “网络不稳定” for every failure).
- Enforce the **Founder Entry and Navigation Gate** (North Star §J): Home from
  success/result reaches a usable entry, restored sessions cannot strand users
  on stale results, page shell renders before network, and a blank screen is
  an automatic FAIL / release blocker.
- Never mark Capability Done without recorded Founder/manual QA evidence.
- Recommend **Auto** by default. Escalate to **Grok 4.5** only for a genuine
  cross-system blocker. Use **GPT-5.6 Terra Medium** only for architecture or
  Blueprint decisions.
- Never use subagents unless the founder explicitly changes this rule.
- Record future ideas only; do not implement unproven future features.

---

## 1. Read First (≤10 core docs)

Full hierarchy: `docs/PROJECT_DOC_SYSTEM_MAP.md` → **START HERE** table.

| Order | Doc | Purpose |
|-------|-----|---------|
| 1 | `docs/15_MINUTE_ENGINEER_ONBOARDING.md` | **Start here** — agents / new engineers |
| 2 | `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime truth |
| 3 | `docs/goals/insurance_paid_pilot_goal.md` | Master goal, scope |
| — | `docs/runbooks/OPERATOR_SURFACE.md` | **Target surface** — 10 scripts, 10 docs, 5 endpoints, 15-min paths |
| — | `docs/runbooks/OPERATOR_IGNORE_LIST.md` | **Cognitive load** — safe to ignore for paid pilot |
| 4 | `docs/ANDY_QUICK_START.md` | How to run demo, ports, recovery |
| 5 | `docs/SIMPLIFICATION_MASTER_PLAN.md` | Reduction roadmap (not feature work) |
| — | `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro blueprint — **major sprints only**, not daily deploy |

---

## 2. Default Execution Path

| Task | Command |
|------|---------|
| **Mini Program Build Gate** | `cd miniapp && npm run build:gate` (before Form/Nav/Preview QA) |
| **Claim release gate (local)** | `bash scripts/run_claim_release_gate.sh --local` → `READY FOR QA DEPLOY` |
| **Claim release gate (QA)** | `bash scripts/run_claim_release_gate.sh --qa` → `READY FOR FOUNDER QA` (needs `P26H_QA_BASE_URL` + support key) |
| **Golden Customer Flow** | `bash scripts/run_golden_customer_flow.sh --local\|--qa` |
| **Golden Customer UI Journey** | `bash scripts/run_golden_customer_ui_flow.sh --local\|--qa` |
| **Start demo** | `bash scripts/run_demo_local.sh` (default: product-only SaaS; lab: `RUN_DEMO_LAB=1`) |
| **Pre-demo checklist** | `bash scripts/demo_pre_checklist.sh` |
| **Recovery** (503 / embedding_warming) | `bash scripts/restore_8001_readiness.sh` |
| **Validate live** | `bash scripts/demo_quick_validate.sh` (intake API) or `guardrail_inbox_triage.sh` |
| **Unified Intake guardrail** | `bash scripts/guardrail_inbox_triage.sh` |
| **Trial readiness check** | `bash scripts/trial_readiness_check.sh` |
| **Trial launch check** | `bash scripts/trial_launch_check.sh` — single entry before first broker trial |
| **Readiness summary** | `bash scripts/summarize_readiness_posture.sh` |
| **Founder pre-trial** | `bash scripts/founder_pre_trial_checklist.sh` |
| **Unified Intake scenarios** | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| **Unified Intake API test** | `python3 scripts/test_inbox_triage_api.py` (server on 8001) |

---

## 3. Runtime Paths

| Path | Port | When |
|------|------|------|
| **Default** | **8001** | Local dev, demo, validation (run_demo_local.sh) |
| **Docker** | 8000 | `docker compose up rag-api` |
| **Recovery** | 8001 | After `restore_8001_readiness.sh` |

Details: `docs/runbooks/RUNTIME_PATH_STANDARD.md`

---

## 4. Key Docs by Category

| Category | Path | Use |
|----------|------|-----|
| Goals | `docs/goals/` | What we're building |
| Standards | `docs/standards/` | Quality bar before demo |
| Runbooks | `docs/runbooks/` | How to run, meeting pack |
| Guardrails | `docs/guardrails/` | Drift checks, when to run |
| Reports | `docs/BROKER_REPORTS_INDEX.md` | Sprint reports, diagnosis; archive at `docs/archive/` |
| **Trial** | `docs/trial/INDEX.md` | Real broker trial: TRIAL_ONE_PATH, templates |
| **Broker** | `docs/BROKER_ONE_PAGER.md` | Customer-facing one-pager |
| **Founder** | `docs/FOUNDER_ONE_PATH.md` | Single canonical founder path |

---

## 5. Multi-Agent Collaboration

**How Cursor, OpenClaw, ChatGPT, and Andy work together:** `docs/MULTI_AGENT_OPERATING_MODEL_V1.md`

- Roles and responsibilities
- Default working loop
- What to do autonomously vs when to ask Andy

---

## 6. Scope Guardrail

- **In scope:** Broker demo, auto insurance RAG, demo UI, validation scripts, Unified Intake MVP (inbox triage)
- **Out of scope:** Stripe, auth, multi-tenant, other verticals
- **Before changes:** Read relevant goal/standard; prefer small inspect→integrate→retest loops

---

*Full map: `docs/PROJECT_DOC_SYSTEM_MAP.md`*
