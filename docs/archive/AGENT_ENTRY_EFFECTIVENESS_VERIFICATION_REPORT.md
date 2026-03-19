# Agent Entry Effectiveness Verification Report

**Sprint:** Agent Entry Effectiveness Verification Sprint  
**Date:** 2026-03-07

---

## 1. What was verified

### Entry flow
- **README → AGENTS.md:** Broker Demo section (lines 5–11) clearly says "Read [AGENTS.md](AGENTS.md) first" and lists doc map + quick start. Entry routing works.
- **AGENTS.md reading order:** Table with Order 1–3 (PROJECT_DOC_SYSTEM_MAP, insurance_paid_pilot_goal, ANDY_QUICK_START) is explicit.
- **Default script path:** AGENTS.md §2 lists run_demo_local.sh, demo_pre_checklist.sh, restore_8001_readiness.sh, demo_quick_validate.sh.
- **Runtime path:** AGENTS.md §3 states 8001 default, 8000 Docker; points to RUNTIME_PATH_STANDARD.

### Doc system flow
- **Goals:** `docs/goals/` with INDEX.md; insurance_paid_pilot_goal.md exists and is primary.
- **Standards:** `docs/standards/` with INDEX.md; BROKER_DEMO_QUALITY_STANDARD exists.
- **Runbooks:** `docs/runbooks/` with INDEX.md; BROKER_VALUE_VALIDATION_MEETING_PACK exists.
- **Guardrails:** `docs/guardrails/` with INDEX.md; BROKER_DEMO_DRIFT_GUARDRAIL exists.
- **Reports:** `reports/INDEX.md` exists and points to broker reports in docs/.

### What already works well
- README Broker section is prominent and routes agents to AGENTS.md.
- AGENTS.md is concise (~60 lines) with clear tables.
- PROJECT_DOC_SYSTEM_MAP reinforces AGENTS.md and provides task→doc mapping.
- ANDY_QUICK_START is a single-file quick reference.
- AGENTS.md is in Cursor workspace rules (always applied for broker work).

---

## 2. Friction points found

| Friction | Why it matters |
|---------|----------------|
| **RUNTIME_PATH_STANDARD path mismatch** | AGENTS.md, PROJECT_DOC_SYSTEM_MAP, and docs/runbooks/INDEX.md pointed to `docs/runbooks/RUNTIME_PATH_STANDARD.md`, but the file lived at `docs/RUNTIME_PATH_STANDARD.md`. Agents following links would get 404. |
| **Standards/guardrails INDEX broken links** | docs/standards/INDEX.md and docs/guardrails/INDEX.md linked to `./BROKER_DEMO_*.md` (expecting files in subfolders), but files live in `docs/`. Links would fail. |
| **Reports not in AGENTS.md §4** | AGENTS.md Key Docs table listed Goals, Standards, Runbooks, Guardrails but not Reports. Agents looking for sprint/diagnosis reports had no direct pointer. |

---

## 3. Changes made

| File | Change | Why |
|------|--------|-----|
| `docs/RUNTIME_PATH_STANDARD.md` | **Moved** to `docs/runbooks/RUNTIME_PATH_STANDARD.md` | Matches doc system layout; fixes AGENTS.md, PROJECT_DOC_SYSTEM_MAP, runbooks INDEX. |
| `docs/ANDY_QUICK_START.md` | Updated ref: `docs/RUNTIME_PATH_STANDARD.md` → `docs/runbooks/RUNTIME_PATH_STANDARD.md` | Consistency with new location. |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Same ref update | Consistency. |
| `docs/BROKER_DEMO_CHECKLIST.md` | Same ref update | Consistency. |
| `docs/standards/INDEX.md` | Fixed link: `./BROKER_DEMO_QUALITY_STANDARD.md` → `../BROKER_DEMO_QUALITY_STANDARD.md` | File is in docs root. |
| `docs/guardrails/INDEX.md` | Fixed link: `./BROKER_DEMO_DRIFT_GUARDRAIL.md` → `../BROKER_DEMO_DRIFT_GUARDRAIL.md` | File is in docs root. |
| `AGENTS.md` | Added Reports row to §4 Key Docs: `reports/INDEX.md` | Agents can find sprint/diagnosis reports. |

---

## 4. Effectiveness result

| Aspect | Before | After |
|--------|--------|-------|
| **Entry path** | README → AGENTS.md worked; RUNTIME_PATH_STANDARD link 404 | All links resolve; entry path intact. |
| **Doc system** | 3 broken links (runbooks, standards, guardrails INDEX) | All INDEX links resolve. |
| **Reports discoverability** | Only via PROJECT_DOC_SYSTEM_MAP | AGENTS.md §4 now lists Reports. |
| **Runtime path clarity** | Correct in AGENTS.md; detail link broken | Detail link works. |

**Verdict:** **Better.** Entry path was already good; doc system had fixable broken links. Changes remove friction without adding complexity.

---

## 5. Manual-work reduction

| What Andy no longer needs to explain | Source |
|--------------------------------------|--------|
| Where to start | README → AGENTS.md; AGENTS.md in workspace rules |
| What to read first | AGENTS.md §1 (order 1–3) |
| Default script path | AGENTS.md §2 (run_demo_local, demo_pre_checklist, restore, validate) |
| Default runtime path (8001 vs 8000) | AGENTS.md §3 + docs/runbooks/RUNTIME_PATH_STANDARD.md |
| Where goals/standards/runbooks/guardrails/reports live | AGENTS.md §4 + PROJECT_DOC_SYSTEM_MAP |
| Broker scope (in/out) | AGENTS.md §5 |

**Cursor:** Can infer all of the above from AGENTS.md and linked docs.  
**OpenClaw:** Same; AGENTS.md is the single entry point for both.

---

## 6. Remaining blocker(s)

- None. Entry path and doc system are effective for broker work.

---

## 7. Recommended next sprint

**Target:** Optional `.cursor/rules` reinforcement  
**Why:** AGENTS.md is already in workspace rules. If agents still skip it in practice (e.g., OpenClaw sessions that don’t load workspace rules), add a minimal `.cursor/rules/broker-entry.mdc` with `alwaysApply: true` that says "For broker work: read AGENTS.md first." Only do this if skip behavior is observed.
