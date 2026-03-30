# Deploy and smoke spec

## Deploy path

- **Script:** `bash scripts/deploy_rag_demo.sh` from repo root.
- **Prereqs:** `.env.cloudrun` with at least `QDRANT_URL` (+ optional `QDRANT_API_KEY`), `OPENAI_API_KEY` for LLM-backed Role C, `ALLOWED_ORIGINS` for Vercel CORS if needed.
- **Service:** `fiqa-api`, region `us-west1`, project from gcloud / `.env.cloudrun`.

## Live verification

1. `GET {CLOUD_RUN_URL}/readyz` → **200**, `intake_path_ready` true (aggregate `clients.openai` may still be false; Role C uses direct env key).
2. `POST {CLOUD_RUN_URL}/api/inbox/simulation-role-c-customer` with JSON body:
   - `persona_id`, `optional_note`, `difficulty`, `max_turns` (3–8), `conversation_turns` (array).
   - Expect **200** + `customer_message`, `llm_used`, `model`, `turn_index`, `max_turns`; or **503** with clear `detail` if LLM unavailable.
3. Optional: `POST /api/inbox/triage` with `soft_route: add_car` to confirm same host serves intake.

## Frontend alignment

Production Vercel bundle must use `VITE_API_BASE_URL` pointing at the **same** Cloud Run HTTPS host (see `ui/src/api/config.ts`).
