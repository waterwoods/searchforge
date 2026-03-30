# ADD-CAR PILOT SIMULATION + DEPLOY + FINAL TEST CASE PACKAGE — Blueprint

## Sprint purpose

Bounded pilot release loop for **Unified Intake / Add-Car**: align with master outline and truth switch, run realistic rule-path checks, optionally fix tiny blockers, deploy surfaces, smoke-test, deliver **3–5 manual founder test cases**.

## Alignment (read-first)

- **Product:** Unified customer entry → structured service record → office handoff; **not** full CRM or autonomous carrier execution (`docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`, `docs/PROJECT_TRUTH_SWITCH.md`).
- **Flagship path:** Add-Car / add vehicle quote intake.
- **Stage 1:** Intake + structuring + handoff; pilot-grade persistence (JSON primary; optional Postgres dual-write when configured).

## Out of scope

Broad redesign, new architecture, non–Add-Car expansion, large schema refactors.

## Release target (this sprint)

- **Frontend:** Vercel production; canonical pilot URL alias `https://ui-smoky-beta.vercel.app` → `/workbench/unified-intake`.
- **Backend:** Google Cloud Run service `fiqa-api` (documented URL pattern `https://fiqa-api-g7zatxrycq-uw.a.run.app`); deploy path `bash scripts/deploy_rag_demo.sh` (requires `.env.cloudrun`, `gcloud`, Docker as per script).
- **Assumptions:** `VITE_API_BASE_URL` (or equivalent) set in Vercel for production builds so the browser calls Cloud Run, not localhost; backend `ALLOWED_ORIGINS` includes the Vercel origin for CORS.

## Loops

1. Alignment + release target check  
2. Realistic simulation (subset: happy path, 微信发过了, re-shop, 还缺什么, spouse/household)  
3. Tiny fix only if clearly release-blocking  
4. Frontend deploy (`cd ui && vercel --prod`)  
5. Backend deploy (repo script; verify if credentials/build available)  
6. Smoke (HTTP: UI route, `/readyz`, `client-config`, CORS, sample `POST /api/inbox/triage`)  
7. Manual test case package  
8. Founder summary  

## Success criteria

- Honest report: what was **directly verified** vs **inferred** vs **not run**.
- Guardrail + focused scenarios reviewed for obvious trust/release blockers.
- Deploy commands attempted with captured outcomes where tooling allows.
