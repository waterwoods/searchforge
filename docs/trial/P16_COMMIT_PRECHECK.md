# P16 Commit Precheck — Preview White-Screen Fix

**Date:** 2026-06-07  
**Branch:** `sprint-a/broker-front-door` (ahead of origin by 1 commit)  
**Mission:** Commit focused white-screen fix only; exclude unrelated local work.

---

## Modified files (24 tracked)

| File | Class | Commit? | Notes |
|------|-------|---------|-------|
| `ui/src/features/intake/utils/customerFirstEntry.ts` | **A** | **YES** | Missing `ADD_CAR_FIELD_LABELS` import — root cause of Preview white screen |
| `ui/src/App.tsx` | C | NO | `LabRoutes()` vs `<LabRoutes />` — unrelated to blank page; not in audit |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | C | NO | Office copy-continuation UX — unrelated |
| `ui/package-lock.json` | C | NO | Incidental lockfile drift |
| `services/fiqa_api/routes/inbox_triage.py` | C | NO | Backend route changes — separate sprint |
| `services/fiqa_api/inbox_triage/case_truth_repository.py` | C | NO | Backend — separate |
| `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` (deleted) | C | NO | Backend refactor — separate |
| `configs/clients/chen_kui/ui_copy.json` | C | NO | Copy tweak — unrelated |
| `configs/demo.env.example` | B/C | NO | Example env — not part of UI fix commit |
| `configs/industries/insurance/markers.json` | C | NO | Marker config — unrelated |
| `demo_brain_report.html` (deleted) | C | NO | Local artifact removal |
| `triage.sh` (deleted) | C | NO | Script removal — unrelated |
| `scripts/deploy_paid_pilot.sh` | C | NO | Deploy script — unrelated |
| `scripts/validate_pilot_deploy_env.py` | C | NO | Deploy validation — unrelated |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | B | NO | Doc drift — separate |
| `docs/product_constitution/P16Z*.md` (4 files) | B | NO | Constitution/roadmap — do not change Constitution in this commit |
| `docs/product_constitution/ROADMAP_FROM_CONSTITUTION.md` | B | NO | Roadmap — separate |
| `docs/product_constitution/.p16z24_results/after_results.json` | D | NO | Generated results |
| `docs/runbooks/OPERATOR_SURFACE.md` | B | NO | Runbook — separate |
| `docs/trial/INDEX.md` | B | NO | Index — will update in mission docs separately |

## Untracked files (150+)

Large set of P16 trial/constitution reports, simulation JSON artifacts (`.p16_*_simulation.json`), stress-test configs, and scripts. **None committed in this focused fix commit** except mission verification docs created in this sprint (`P16_COMMIT_*`, `P16_PRE_COMMIT_*`, `P16_QA_*`, `P16_REALISTIC_*`, `P16_COMMIT_AND_QA_*`).

## What will be committed

1. `ui/src/features/intake/utils/customerFirstEntry.ts` — one-line import restore
2. Mission verification docs from this run (post-commit report chain)

## What will NOT be committed

- All backend changes (`inbox_triage.py`, `case_truth_repository.py`, deleted `active_vehicle_resolver.py`)
- `App.tsx`, `BrokerWorkbenchTab.tsx` local edits
- Config/copy/deploy script changes
- Constitution or roadmap docs
- Untracked P16 archive reports (150+ files)
- Any `.env`, `.env.cloudrun`, secrets, or generated junk

## Secrets scan

| Check | Result |
|-------|--------|
| `.env` / credentials in diff | None |
| API keys in staged paths | None planned |
| `demo.env.example` adds placeholder keys only | Excluded from commit |

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Commit includes unrelated backend | **High if unfocused** | Stage only `customerFirstEntry.ts` |
| White screen returns | **Low** | Import verified in local build; Preview alias already on fixed bundle `index-Bs99AAgT.js` |
| False 已提交办公室 on incomplete cases | **Medium** | Live smoke test Cases A–C after commit |
| Secrets in commit | **Low** | Single TS import + markdown docs only |

**Precheck verdict:** Safe to proceed with **one-file code commit** + mission docs.

---

*End of P16 Commit Precheck*
