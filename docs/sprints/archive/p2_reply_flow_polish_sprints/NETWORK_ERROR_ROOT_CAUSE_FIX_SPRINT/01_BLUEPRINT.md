# NETWORK ERROR ROOT-CAUSE + FIX — Blueprint

## Sprint goal

Find the real cause of browser-side **Network Error** on Unified Intake / Add-Car against the deployed UI, fix the smallest correct issue(s), and record evidence.

## Why now

Add-Car is the flagship path (Stage 1, pilot usability). An opaque **Network Error** blocks demos and trials and is often mis-attributed to “backend down” when the failure is **build-time API target** or **browser mixed content**.

## Read-first (aligned)

- `docs/PROJECT_TRUTH_SWITCH.md`
- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` — `VITE_API_BASE_URL`, `ALLOWED_ORIGINS`
- `docs/runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md` — CORS / URL alignment
- Prior notes: `docs/sprints/UNIFIED_INTAKE_FOCUS_MODE_SPRINT_REPORT.md`, `docs/sprints/WORKBENCH_HANDOFF_PROFESSIONALIZATION_TRIAL_HARDENING/DEPLOY_REPORT.md` (Vercel env warnings)

## Scope

- Frontend API base URL behavior (`VITE_API_BASE_URL`, production vs dev)
- Backend reachability and CORS for `https://ui-smoky-beta.vercel.app`
- Request path `POST /api/inbox/triage`
- Small bounded prevention (build guard), no product redesign

## Non-scope

- Database / persistence redesign
- Triage engine / state flow changes
- Broad refactors, unrelated cleanup

## Target outcome

- Documented **confirmed** vs **inferred** root-cause class for axios “Network Error” in this stack
- Confirmed current production alias behavior (browser + curl)
- **Preventive** fix so Vercel cannot ship a production bundle with a broken API base (missing / localhost / non-HTTPS)
