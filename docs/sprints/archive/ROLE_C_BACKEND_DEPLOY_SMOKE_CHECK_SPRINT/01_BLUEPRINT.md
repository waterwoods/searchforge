# ROLE C BACKEND DEPLOY + SMOKE CHECK — Blueprint

## Goal

Deploy the **fiqa-api** backend revision that includes `POST /api/inbox/simulation-role-c-customer`, confirm **OPENAI_API_KEY** (or `LLM_API_KEY`) is effective for Role C, and **smoke-verify** the live URL so Andy can test Role C from Vercel.

## Why narrow

Prior work added Role C in code; production returned **404** on the new route until a **Cloud Run redeploy** shipped that code.

## Read-first (this sprint)

- `services/fiqa_api/inbox_triage/role_c_customer_llm.py`
- `services/fiqa_api/routes/inbox_triage.py` (route registration on existing `inbox_triage` router)
- `scripts/deploy_rag_demo.sh` (canonical fiqa-api deploy; uses `.env.cloudrun`)
- `ui/src/api/inboxTriage.ts` (`fetchSimulationRoleCCustomer`)

## Out of scope

Frontend changes, simulation UX, triage logic changes, unrelated services.
