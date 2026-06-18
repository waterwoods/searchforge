# Deploy Failure Root Cause — P16 Customer First Recovery

**Sprint:** P16-PHASE1-CUSTOMER-FIRST-DEPLOYMENT-RECOVERY-SPRINT  
**Date:** 2026-06-07  
**Investigator:** Cursor agent (evidence-based; no guessing)

---

## Evidence Collected

| Source | Command / artifact | Result |
|--------|-------------------|--------|
| Git | `git status` | Branch `sprint-a/broker-front-door` @ `b3c8ec3`; Customer First UI **uncommitted** (untracked `CustomerFirstEntryScreen.tsx`, `customerFirstEntry.ts`; modified `CustomerEntryTab.tsx`) |
| Git | `git log --oneline -20` | Latest commit `b3c8ec3`; Customer First work **not in any recent commit** |
| Vercel (root `searchforge` project) | `vercel ls` | Latest 4 Preview deploys **Error** (6–15s duration); last Ready Preview **7d ago** (`dpl_izNfmjojxCpzaVcMGyUuWTXnoeej`) |
| Vercel (canonical `ui` project) | `cd ui && vercel ls` | Latest Ready **20h ago** before this sprint; prior Error on `ui-3bnw3o4fe` (9s) |
| Build logs (error) | `vercel inspect dpl_BLF3umqNzLb7ipUBBNd99ZZJEHte --logs` | Vite ENOENT — see below |
| Build logs (last Ready) | `vercel inspect dpl_izNfmjojxCpzaVcMGyUuWTXnoeej --logs` | Build succeeded in 46s |
| Runtime logs | `vercel logs` on Error deployment | No runtime — build failed before deploy |

---

## Root Cause (Git-triggered `searchforge` project)

**Classification: Build failure — missing source module (not env, not TypeScript checker, not runtime).**

```
[vite:load-fallback] Could not load .../ui/src/features/intake/prototypes/p16z21/evolutionPaths
(imported by src/features/intake/components/CustomerEntryTab.tsx): ENOENT
```

Committed `CustomerEntryTab.tsx` @ `b3c8ec3` imports three prototype modules that **do not exist** in the repository:

- `@/features/intake/prototypes/p16z21/evolutionPaths`
- `@/features/intake/prototypes/p16z21/PathGuidedRail`
- `@/features/intake/prototypes/p16z21/PathTimelineFirstBanner`

Directory `ui/src/features/intake/prototypes/` is **empty / absent**.

| Question | Answer |
|----------|--------|
| Build failure? | **YES** — Vite module resolution ENOENT |
| Missing env? | **NO** — build fails before env-dependent runtime |
| TypeScript failure? | **NO** — Vite load error, not `tsc` |
| Runtime failure? | **NO** — deployment never reached Ready |
| Wrong branch? | **NO** — correct branch `sprint-a/broker-front-door` @ `b3c8ec3` |
| Wrong project? | **Partially** — two Vercel projects exist; founder Preview uses **`ui`** project, not root `searchforge` |
| Wrong output directory? | **NO** — `ui/vercel.json` → `dist` is correct when build succeeds |

---

## Customer First Work Excluded from Git Deploy

| Artifact | In `b3c8ec3` (git deploy source)? |
|----------|-----------------------------------|
| `CustomerFirstEntryScreen.tsx` | **NO** — untracked |
| `customerFirstEntry.ts` | **NO** — untracked |
| `active_case_lookup.py` / phone API routes | **NO** — uncommitted backend |
| Customer First gate in `CustomerEntryTab.tsx` | **NO** — working tree only; committed file still has broken `p16z21` imports |

Git-connected Preview builds therefore **cannot** ship Customer First UI until code is committed **and** prototype import breakage is removed.

---

## Secondary Gap: Cloud Run API (post-UI deploy)

After successful UI deploy, browser verification of Continue flow calls:

`GET https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/customer/active-case?phone=…`

**Response:** `404 Not Found` (with valid `X-Unified-Intake-Api-Key`).

Customer First **backend routes** (`/customer/active-case`, `/customer/start-add-car`) exist in local working tree but are **not yet on Cloud Run**. This blocks Scenario A/B end-to-end flow on Preview; UI shell is unaffected.

---

## Last Successful Ready Deployments

| Project | Deployment ID | URL | Age | Notes |
|---------|---------------|-----|-----|-------|
| `searchforge` (root) | `dpl_izNfmjojxCpzaVcMGyUuWTXnoeej` | `searchforge-mfxdo2bvh-…vercel.app` | 7d | Pre–Customer First; no prototype import in that build era |
| `ui` (canonical) | `dpl_2tzhtecntoYKBRwa7BTfoSVVRThd` | `ui-do075u1o0-…vercel.app` | 20h | Office Visibility era; **no** Customer First bundle markers |

---

## Recovery Action Taken

CLI deploy from `ui/` with **local working tree** (includes Customer First + removed broken imports):

```bash
cd ui
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY=<from .env.cloudrun>
```

Result: **Ready** — `dpl_CUZEuqipbcaLaUoby5owCLbhvLzx`

---

*End of root cause report*
