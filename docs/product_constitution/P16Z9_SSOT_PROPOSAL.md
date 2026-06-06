# P16-Z9 Phase 2 — SSOT Proposal

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Sources:** P16-Y through P16-Z8, Role D, CASE_INTELLIGENCE_*, AGENTS.md, CURRENT_PRODUCT_SHAPE

---

## Problem

Between P16-Y and P16-Z8, the team produced **~270 product_constitution markdown files** and rediscovered the same truths (append exists, SSO blocks trial, triage.py is the engine) in **8+ sprints**. New engineers cannot tell which doc is law.

---

## Proposed SSOT stack (three layers + one index)

```
┌─────────────────────────────────────────────────────────┐
│  P16Z9_FOUNDER_SUMMARY.md  — "what we know now" (index) │
└───────────────────────────┬─────────────────────────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
 PRODUCT SSOT          CAPABILITY SSOT        VALIDATION SSOT
 (what it is)          (what exists)          (how we prove it)
```

---

## 1. Product SSOT (what we sell / how it feels)

| Document | Role | Replaces / supersedes |
|----------|------|------------------------|
| **`CASE_INTELLIGENCE_MASTER_OUTLINE.md`** | Layer pipeline: Message → Understanding → Case → Timeline → Next Action → Follow-up → Outcome | P16-Z2 north star essays, scattered architecture |
| **`CASE_INTELLIGENCE_MATURITY_MODEL.md`** | L1–L7 commercial maturity; engine vs deployed vs Chen Kui effective | `P16Z3_MATURITY_MODEL.md` (duplicate — mark historical) |
| **`P16Z25_NORTH_STAR.md`** | One-sentence north star (canonical) | P16-Z2/Z5 duplicate north star paragraphs |
| **`P16Z25_PRODUCT_SOUL.md`** | One-sentence soul + 微信 loop | P16-Z5 soul block |
| **`docs/CURRENT_PRODUCT_SHAPE.md`** | Runtime, env, Postgres, product_only | Any sprint deploy note |
| **`docs/goals/insurance_paid_pilot_goal.md`** | Scope in/out | P17/platform docs |
| **`docs/BROKER_ONE_PAGER.md`** | External broker language | — |

**Update trigger:** Deploy change, maturity level shift, or paid pilot scope change.

---

## 2. Capability SSOT (what is built / hidden / broken)

| Document | Role | Replaces / supersedes |
|----------|------|------------------------|
| **`P16Z0_CAPABILITY_MAP_V2.md`** | Master map: current / hidden / broken / unused / high-value | Re-run quarterly; don't fork new maps |
| **`P16Z0_CAPABILITY_INVENTORY.md`** | Module-level inventory (`inbox_triage/`) | New "capability archaeology" sprints |
| **`P16Z9_CAPACITY_REVIEW.md`** | Seven capacities Tier 1–3 (pilot) | `P16Z25_CAPACITY_RANKING.md` for execution tiers |
| **`P16Z8_CAPABILITY_MAP.md`** | Memory domains A–E (payment, remove-car, merge, waiting, claims) | Post-Z8 engine slice tracking |
| **`P16Z0_DUPLICATION_AUDIT.md`** | Anti-rebuild list | New microservice proposals |

**Code truth (not a markdown SSOT but cited everywhere):**

- `services/fiqa_api/inbox_triage/triage.py`
- `services/fiqa_api/inbox_triage/case_draft_engine.py`
- `services/fiqa_api/inbox_triage/case_store.py`
- `ui/src/components/intake/BrokerWorkbenchTab.tsx`

**Update trigger:** Any sprint that wires, exposes, or deletes a capability.

---

## 3. Validation SSOT (how we know we didn't lie)

| Document | Role | Executable pair |
|----------|------|-----------------|
| **`P16Z9_VALIDATION_OS.md`** | Battery order, gates, observation log | — |
| **`P16Y_RUBRIC.md`** | Single-turn intelligence scoring | `run_p16y_case_battery.py` |
| **`configs/p16y_50_cases.json`** | Case fixtures | same |
| **`ROLE_D_LIBRARY.md`** | Multi-day journey definitions | `run_role_d_memory_battery.py` |
| **`configs/role_d_journeys.json`** | Journey fixtures | same |
| **`ROLE_D_FOUNDER_SUMMARY.md`** | Latest Role D scores (update after each battery run) | `.role_d_results/role_d_battery.json` |
| **`docs/trial/OBSERVATION_LOG*.md`** (if exists) or trial INDEX | Commercial proof | Founder process |

**Operator SSOT (scripts, not docs):**

| Script | Gate |
|--------|------|
| `scripts/operator/guardrail_inbox_triage.sh` | Pre-merge / pre-demo |
| `scripts/trial_launch_check.sh` | Pre-trial |
| `scripts/run_p16y_case_battery.py` | ≥88 avg single-turn |
| `scripts/run_role_d_memory_battery.py` | reread ≥80, needs_wechat ≤2/10 |

**Update trigger:** Any engine or UX change to append, summary, classification, or thread UI.

---

## 4. Execution SSOT (what to do this week)

| Document | Role |
|----------|------|
| **`P16Z9_DEVELOPMENT_OS.md`** | Sprint loop SSOT → Implementation → Validation → Reality → Update SSOT |
| **`P16Z9_90_DAY_FILTER.md`** | Build / don't build for 90 days |
| **`P16Z8_EXECUTION_PLAN.md`** | Active 3-day engine slice (until Z8 ship complete) |
| **`AGENTS.md`** | Default commands |
| **`docs/FOUNDER_ONE_PATH.md`** | Founder ritual |

**Historical execution plans (do not follow in parallel):**

- `P16Z4_EXECUTION_PLAN.md`, `P16Z3_30_DAY_PLAN.md`, `P16Z6_*` day plans — absorbed into Z9 OS

---

## 5. Sprint artifact policy (going forward)

| When sprint ends | Action |
|------------------|--------|
| Final verdict exists | Extract deltas into `P16Z9_FOUNDER_SUMMARY.md` + relevant SSOT |
| Phase 1–9 detail docs | Move to `docs/archive/product_constitution/<sprint>/` after 30 days |
| Duplicate north star / capacity / ROI | **Do not create** — edit SSOT in place |
| New battery | Must declare which SSOT gate it feeds |

---

## SSOT maintenance owners

| Layer | Owner | Review cadence |
|-------|-------|----------------|
| Product | Founder + lead eng | Per deploy |
| Capability | Eng (post-sprint) | Per sprint |
| Validation | Eng (CI) + Founder (observation log) | Weekly during trial |
| Execution | Founder | Weekly |

---

## Documents to demote immediately

| Document | New class | Reason |
|----------|-----------|--------|
| `P16Z3_MATURITY_MODEL.md` | Historical | Duplicate of `CASE_INTELLIGENCE_MATURITY_MODEL.md` |
| `P16Z2_FINAL_VERDICT.md` north star block | Historical | Use `P16Z25_NORTH_STAR.md` |
| `P16M_TOP50_*`, `P16N_*`, `P16X_TOP50_*` | Historical | Themes in Z9 duplicate audit |
| `docs/UNIFIED_INTAKE_*_MASTER_OUTLINE` (macro) | Reference only | Not daily SSOT |
| Platform blueprints in `docs/archive/platform/` | Obsolete | Constitution blocked |

---

## Minimum SSOT for PR review

Reviewer must confirm alignment with:

1. `CURRENT_PRODUCT_SHAPE.md` (env/deploy)
2. `CASE_INTELLIGENCE_MASTER_OUTLINE.md` (layer touched)
3. `P16Z9_90_DAY_FILTER.md` (not building forbidden item)
4. Validation OS (battery run if engine/UX)

---

*End of P16-Z9 Phase 2 — SSOT Proposal*
