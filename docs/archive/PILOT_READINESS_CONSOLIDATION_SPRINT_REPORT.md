# Pilot Readiness Consolidation Sprint Report

**Sprint:** Pilot Readiness Consolidation Sprint  
**Date:** 2026-03-06  
**Focus:** California Auto Insurance Broker Assistant

---

## 1. Issue targeted

**Consolidation issues selected:**

1. **Two prep paths, no single default** — ANDY_2MIN and ANDY_QUICK_START pointed to `demo_prep_one_command.sh`, while BROKER_DEMO_OPERATOR_RUNBOOK said run `guardrail_broker_demo.sh` first, then `demo_pre_checklist.sh`. Andy had to remember which to run and in what order.

2. **Guardrail was separate** — The Runbook required running guardrail as a separate step before the checklist. Easy to forget, and the checklist did not include it.

**Why they mattered most:** They caused the highest cognitive load: "Which command first? Do I run guardrail? Which doc is right?" One clear default path reduces confusion and missed steps.

---

## 2. Changes made

| File | Change |
|------|--------|
| `scripts/demo_pre_checklist.sh` | Added step [0]: run `guardrail_broker_demo.sh` at the start. If guardrail fails, exit 1 before env/validation. Guardrail output saved to `results/demo_pre_checklist/<timestamp>/guardrail_log.txt`. |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | Switched primary prep to `demo_pre_checklist.sh`. Kept `demo_prep_one_command.sh` as "quick path when backend already up". Clarified "Use Live path" vs "Use Offline path" wording. |
| `docs/ANDY_QUICK_START.md` | Same: `demo_pre_checklist.sh` as default, `demo_prep_one_command.sh` as quick option. |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Collapsed "run guardrail" + "run checklist" into one step: "run demo_pre_checklist" (now includes guardrail). Updated Key Paths table; added Meeting pack row. |
| `docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | Added one-line "Pre-meeting (5 min before)" with the default flow and pointer to ANDY_2MIN. |

**Why it helps:** One command (`demo_pre_checklist.sh`) now does guardrail + env + offline pack + validation (if backend up) + writes checklist. Andy no longer needs to remember to run guardrail separately.

---

## 3. Re-test results

**What was tested:**

- `bash scripts/demo_pre_checklist.sh` — guardrail ran first (PASS), then env/offline/backend/validation. Checklist written to `results/demo_pre_checklist/2026-03-06_194136/CHECKLIST.md`.
- `bash scripts/demo_pre_checklist.sh --strict` — same flow; STRICT passed (workflow 5/5, offline pack 5 items).
- `bash scripts/guardrail_broker_demo.sh` — still works standalone.

**Default path clarity:** Before = "run guardrail, then checklist" or "run demo_prep_one_command" depending on doc. After = "run demo_pre_checklist" everywhere.

**Before vs after:**

| Aspect | Before | After |
|--------|--------|-------|
| Prep steps | 2 (guardrail + checklist) or 1 (demo_prep_one_command, no guardrail) | 1 default (demo_pre_checklist = guardrail + checklist) |
| Doc consistency | ANDY_2MIN vs Runbook disagreed | All docs point to demo_pre_checklist as default |
| Guardrail | Separate, easy to skip | Integrated into checklist, fail-fast |

**Result:** Better — one default path, guardrail no longer skippable when using the default.

---

## 4. Operator impact

**What Andy no longer needs to remember:**

- That guardrail must be run before the checklist.
- Which doc says which command (ANDY_2MIN, Runbook, Quick Start now aligned).

**New default paths:**

| Phase | Default path |
|-------|--------------|
| **Pre-demo** | `bash scripts/demo_pre_checklist.sh` |
| **Guardrail** | Included in demo_pre_checklist; standalone `guardrail_broker_demo.sh` still available |
| **Validation** | Included in demo_pre_checklist when backend up; `demo_quick_validate.sh` still available |
| **Fallback / demo-safe** | Checklist output says "Use Offline path" or "Use Live path"; same guidance in ANDY_2MIN |
| **Meeting prep** | `docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md` — pre-meeting line points to demo_pre_checklist → run_demo_local → open URL |

**What Cursor can repeatedly run:** `bash scripts/demo_pre_checklist.sh` as the single pre-demo command.

**What OpenClaw can enforce:** `guardrail_broker_demo.sh` (or demo_pre_checklist, which runs it) for drift checks.

---

## 5. Remaining blocker(s)

- None for this consolidation. Live validation returned 503 during testing (backend/Qdrant availability), but that is environmental, not a consolidation issue. Offline path remains valid.

---

## 6. Recommended next sprint

**Next target:** Reduce doc sprawl — consider a single "Broker Pilot One-Pager" that links to ANDY_2MIN, Runbook, and Meeting Pack, so Andy has one entry point.

**Why:** Multiple docs (ANDY_2MIN, ANDY_QUICK_START, Runbook, Meeting Pack) still exist. A one-pager could be the single "start here" for broker pilot prep, with links to the others for detail.

---

## 7. Future-readiness note (documentation only)

This consolidation suggests:

- **Pilot-readiness pack:** A single script + doc combo (demo_pre_checklist + ANDY_2MIN) could be templated for other pilots (e.g., different verticals or regions).
- **Vertical operator pack:** Broker-specific flow (guardrail, Q1–Q5, copy-to-client) could be a pattern for other verticals with similar "prep → validate → run" flows.
- **Common demo/pilot orchestration base:** `demo_pre_checklist.sh` could later accept a `--vertical=broker` (or similar) to support multiple verticals from one script, without heavy refactoring.

No architecture changes recommended now; these are documentation/pattern notes for future sprints.
