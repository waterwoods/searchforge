# ROLE C CONTROLLED LLM CUSTOMER SPRINT — Final report

## What was implemented

- **Backend:** `POST /api/inbox/simulation-role-c-customer` generates the next **Add-Car-only** customer line using OpenAI when `OPENAI_API_KEY` or `LLM_API_KEY` is set. Model defaults to `LLM_MODEL` or `gpt-4o-mini`; override with `ROLE_C_SIMULATION_MODEL` if needed. Logic lives in `services/fiqa_api/inbox_triage/role_c_customer_llm.py`.
- **Frontend:** Simulation tab **角色 C** card + controls (persona, optional note, difficulty, max turns 4/6/8). Each step calls the new endpoint, then **`POST /api/inbox/triage`** with `soft_route: add_car`. Right-rail record summary unchanged in structure.
- **Config:** Static `ADD_CAR_C` placeholder removed from `ui/src/config/add_car_scenario_replay.json`; Role C is UI-built like Role D.

## Real LLM path

**Yes**, when the backend has a valid OpenAI API key. The UI does **not** call OpenAI directly.

## Partial / remaining

- **Backend production deploy** was **not** run from this sprint session (Cloud Run / `gcloud` not executed here). Production Role C requires redeploying the API service that serves `/api/inbox/*`.
- No automated E2E test against live OpenAI in CI (manual demo validation only).
- LLM output is not schema-validated beyond empty-check; rare off-topic lines rely on prompt bounds.

## Deploy result

- **Frontend:** `npx vercel --prod --yes` from `ui/` succeeded (see report body for URLs).
- **Backend:** code merged in repo; **deploy not verified** in this session.

## Recommended next sprint

1. Deploy backend + smoke `POST /api/inbox/simulation-role-c-customer` against staging/prod.
2. Optional: lightweight **post-filter** or second-pass self-check for Add-Car relevance if drift appears in demos.
3. Optional: **rate limit** / auth gate for the simulation endpoint if exposed publicly.
