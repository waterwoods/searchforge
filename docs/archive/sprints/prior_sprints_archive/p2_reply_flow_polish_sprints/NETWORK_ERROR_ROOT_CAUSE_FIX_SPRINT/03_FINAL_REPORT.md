# NETWORK ERROR ROOT-CAUSE + FIX — Final report

## What was checked

- Read: `docs/PROJECT_TRUTH_SWITCH.md`, master outline, deployment playbook / gotchas, prior sprint notes mentioning Vercel + Cloud Run.
- Code: `ui/src/api/config.ts`, `ui/src/api/request.ts`, `ui/src/api/inboxTriage.ts`, `services/fiqa_api/app_main.py` (CORS).
- Live:
  - `GET`/`POST` patterns against Vercel vs Cloud Run.
  - Scraped production JS for embedded `.run.app` URL.
  - `curl` OPTIONS/POST to Cloud Run with `Origin: https://ui-smoky-beta.vercel.app`.
  - Browser automation: loaded `…/workbench/unified-intake`, triggered submit, inspected network (client-config + triage).

## What was broken

- **At verification time:** Production alias **was not** reproducing Network Error; Add-Car triage **succeeded**.
- **Underlying risk:** Any Vercel build missing or mis-setting `VITE_API_BASE_URL` (especially **localhost** or empty) produces a bundle that will show **Network Error** in the browser for this app.

## What was fixed

- Added **`assertVercelProductionApiBase`** in `ui/vite.config.ts`: when `VERCEL=1` and Vite `mode === "production"`, require `VITE_API_BASE_URL` to be set, **https**, and not localhost/127.0.0.1.

## Deploy

- **Not run from this environment.** No frontend/backend redeploy was required to restore service because production was already healthy.
- **After merging:** next Vercel build will enforce env correctness; ensure **Preview** environments also define `VITE_API_BASE_URL` (same Cloud Run URL is typical).

## Verification summary

| Check | Result |
|--------|--------|
| Cloud Run `/health/live` | 200 |
| CORS preflight triage | 200, allow-origin matches Vercel alias |
| POST `/api/inbox/triage` with valid body | 200 JSON |
| Production JS embeds API URL | `https://fiqa-api-1013093472160.us-west1.run.app` |
| Browser: triage POST | 200 |

## Timing (approximate)

- Sprint execution: ~35–45 minutes wall clock (read-first, live probes, guard + docs).
