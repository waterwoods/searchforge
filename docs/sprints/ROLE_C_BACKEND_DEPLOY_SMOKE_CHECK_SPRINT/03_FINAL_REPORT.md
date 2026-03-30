# ROLE C BACKEND DEPLOY + SMOKE CHECK — Final report

## Deploy

- **Command:** `bash scripts/deploy_rag_demo.sh`
- **Result:** Success. Revision **fiqa-api-00043-qb4** (traffic 100%).
- **Public URL (alias used in repo/scripts):** `https://fiqa-api-g7zatxrycq-uw.a.run.app`

## Pre-deploy baseline

- Same URL returned **404** for `POST /api/inbox/simulation-role-c-customer` (route not on running revision).

## Post-deploy smoke

- **`GET /readyz`:** 200, `intake_path_ready: true`. Note: `clients.openai` still **false** in JSON (startup client aggregate); does not block Role C when `OPENAI_API_KEY` is set on the service.
- **`POST /api/inbox/simulation-role-c-customer`:** **200**, non-empty `customer_message`, `llm_used: true`, `model: gpt-4o-mini`, `turn_index: 1`, `max_turns: 6`.
- **`POST /api/inbox/triage`** (add_car sample): **200**, structured triage JSON.

## Founder takeaway

Andy can test Role C from Vercel **if** the production build’s `VITE_API_BASE_URL` is this Cloud Run HTTPS URL (or equivalent routing to the same service).

## Next

- Optionally reconcile `/readyz` `openai` flag with actual key-backed paths (cosmetic ops clarity only).
