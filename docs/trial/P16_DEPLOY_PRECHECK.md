# P16 Deploy Precheck — Office Visibility

**Sprint:** P16-VERIFY-AND-DEPLOY-OFFICE-VISIBILITY-SPRINT  
**Date:** 2026-06-06  
**Phase:** 0 — Identify Current State

---

## Git snapshot

| Field | Value |
|-------|-------|
| **Branch** | `sprint-a/broker-front-door` |
| **HEAD SHA** | `b3c8ec369fa9f9232e3f663be23cd4f093c985d3` |
| **HEAD message** | `chore(repo): resolve reviewed runtime bundles` |

---

## Office Visibility fix — local presence

| Check | Result |
|-------|--------|
| Fix exists in working tree? | **Yes** — modified `intakePure.ts`, `BrokerWorkbenchTab.tsx` |
| Fix committed to git? | **No** — not in `b3c8ec3` or any ancestor |
| Fix on remote? | **Not verified committed** — changes are local WIP only |

**Conclusion:** The Office Visibility sprint implementation was completed in docs/simulation (`P16_VISIBILITY_IMPLEMENTATION.md`) but **never committed or deployed** before this verify sprint.

---

## Feature → source location (not yet a dedicated commit)

| Feature | Introducing change | Git commit | Status |
|---------|-------------------|------------|--------|
| **`formal_submitted_at` score boost (+165)** | `getRecentFormalSubmissionVisibilityBoost()` in `ui/src/features/intake/utils/intakePure.ts` | **None** — WIP only | Uncommitted |
| **Founder demo queue penalty (−300)** | `getFounderDemoSeedWorkbenchPenalty()` + `FOUNDER_DEMO_SEED_WORKBENCH_PENALTY` in `intakePure.ts` | **None** — WIP only | Uncommitted |
| **Product-only queue card enhancement** | `renderRecentCaseCard()` product-only branch in `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | **None** — WIP only | Uncommitted |

### Related reference commits (not the visibility fix)

| SHA | Message | Relevance |
|-----|---------|-----------|
| `517f728` | `fix(p16): active case choice gate` | Last Preview-aligned baseline (Jun 4 deploy) |
| `901b0df` | `P16-I simplify product-only intake UI` | Product-only shell; pre-visibility cards |
| `b0d6073` | `fix(ui): restore missing getCompactQueuePreview import` | Workbench import fix only |

### Simulation / design artifacts (document the intended fix)

| Doc | Purpose |
|-----|---------|
| `docs/trial/P16_VISIBILITY_IMPLEMENTATION.md` | Declares the two-file UI fix |
| `docs/trial/P16_VISIBILITY_RULE_DESIGN.md` | Boost + penalty constants |
| `scripts/run_p16_office_visibility_simulation.py` | Post-fix ranking battery |

---

## Deploy blockers discovered during precheck

| Blocker | Resolution for this sprint |
|---------|---------------------------|
| Missing `p16z21` prototype imports break `npm run build` on HEAD | Temporarily checked out `CustomerEntryTab.tsx` from `d05e94d` for deploy upload only |
| Preview API requires `X-Unified-Intake-Api-Key` | Restored `ui/src/api/request.ts` intake-key interceptor from stash; baked key via `vercel deploy -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY=…` |

---

## Precheck verdict

**Office Visibility fix was NOT deployed before this sprint.** Local WIP exists; git HEAD and prior Preview bundle (`index-CJ0tCunS.js`) do not contain it.
