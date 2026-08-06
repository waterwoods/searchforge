# SearchForge Account and Infrastructure Inventory V1

**Date:** 2026-08-05  
**Purpose:** Safe inventory of external systems for founder ops and FDE portfolio (no secrets).  
**Sources:** `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md`, `docs/ops/GCP_COST_AUDIT_2026-08-03.md`, `configs/demo.env.example`, `configs/cloud_qa.env.example`, freeze evidence packs.  
**Never store:** API keys, tokens, passwords, full connection strings, customer PII.

### Credential owner categories

| Category | Meaning |
|----------|---------|
| Founder | Andy / founder-held console access |
| Shared GCP | Project IAM in `optimal-disk-472305-e2` |
| Secret Manager | Named secrets bound to Cloud Run (values not listed) |
| Vendor console | Third-party dashboard (OpenAI, LangSmith, Vercel, WeChat, GitHub) |

---

## Inventory table

| Provider / platform | Purpose | Environment | Project / service identifier | Config referenced in | Credential owner | Operational dependency | Cost / lock-in risk | Currently required? |
|---------------------|---------|-------------|------------------------------|----------------------|------------------|------------------------|---------------------|---------------------|
| Google Cloud Platform | Hosting, IAM, billing | All cloud | Project `optimal-disk-472305-e2`; billing acct id in cost audit (not a secret) | Deploy scripts, `CLOUD_QA_RESOURCE_NAMES.md` | Shared GCP / Founder | High — all cloud runtime | Medium lock-in; cost audit: actual spend API unavailable | **Yes** for QA/Prod |
| Cloud Run | FastAPI product API | QA | Service `fiqa-api-qa`, region `us-west1` | `.env.cloudrun.qa`, `deploy_cloud_qa.sh` | Shared GCP | High | Low–medium (scale 0–2) | **Yes** for Cloud QA |
| Cloud Run | FastAPI product API | Production | Service `fiqa-api`, region `us-west1` | `.env.cloudrun`, `deploy_paid_pilot.sh` | Shared GCP | High for paid traffic | Low–medium | **Yes** for Production product; **Accident Story enablement not authorized** |
| Cloud Run (lab siblings) | Unrelated MVPs | Mixed | e.g. `mortgage-agent-api`, `airport-mvp-api`, `smartsearchx-api`, vitals-* | Cost audit inventory | Shared GCP | Low for broker product | Cost noise / revision storage | **No** for broker pilot |
| Cloud SQL / Postgres | Case / session SSOT | QA + Prod DBs on one instance | Instance `caseiq-pilot-pg`; DBs `caseiq-qa` / `caseiq` | `SERVICE_RECORD_DATABASE_URL` via Secret Manager | Secret Manager / Founder | Critical | Low–medium (db-f1-micro) | **Yes** for paid/QA pilots |
| Secret Manager | Bind DB / OpenAI / Qdrant / H5 token | QA + Prod | e.g. `fiqa-service-record-database-url-qa`, `…-cloudsql-private`, `fiqa-openai-api-key`, `fiqa-qdrant-api-key`, `fiqa-h5-task-token-secret` | `CLOUD_RUN_SECRET_*` in env examples | Shared GCP | High | Low | **Yes** |
| Cloud Storage (GCS) | Claim media / build artifacts | QA media + build | `caseiq-wecom-media-qa`; build bucket `…_cloudbuild` (large) | Media upload paths; cost audit | Shared GCP | Medium for photo evidence; build bucket is ops debt | Storage growth risk on build/AR | Media: **Yes** for photo claims; build pile: cleanup candidate |
| Artifact Registry / GCR | Container images | Cloud | `gcr.io`, `ssx`, `cloud-run-source-deploy` | Deploy pipeline | Shared GCP | Medium | **High storage cost risk** per cost audit | **Yes** for deploy; needs hygiene |
| OpenAI | LLM extract / triage quality | Local + QA (+ Prod if keyed) | Org/account in Founder OpenAI dashboard; secret name `fiqa-openai-api-key` | `OPENAI_API_KEY`, `ACCIDENT_STORY_LLM` | Vendor console + Secret Manager | Medium — fallback works without live LLM | Usage + vendor lock-in | **Optional** for deterministic path; **required** for live-LLM pilot arm |
| LangSmith | Redacted traces + golden evals | Lab + restricted pilot project | Clean project name `accident-story-restricted-pilot-v1`; flags `ACCIDENT_STORY_LANGSMITH_*` | `accident_story_assistant/tracing.py`, eval scripts | Vendor console / Founder | Low for intake correctness (tracing failure must not break intake) | Medium vendor lock-in; low runtime cost if gated | **Optional** for pilot safety; **required** for eval/portfolio evidence |
| Vercel | Broker Workbench SPA | QA Preview | Host `ui-waterwoods-andys-projects-1f411b73.vercel.app` | `ui/vercel.json`, `DEPLOYMENT_PLAYBOOK.md` | Vendor console / Founder | High for broker UI | Low–medium | **Yes** for Workbench QA |
| Vercel | Broker Workbench SPA | Production | Alias `ui-smoky-beta.vercel.app` | Same | Vendor console / Founder | High for Production UI | Low–medium | **Yes** for Production Workbench |
| WeChat Mini Program / DevTools | Customer claim channel | DevTools + Preview + phone | Mini Program app under `miniapp/`; profiles `config.qa.ts` / local | `miniapp/config*.ts` | WeChat vendor / Founder | High for customer journey | Platform lock-in (WeChat) | **Yes** for customer path |
| GitHub | Source, PRs, history | All | searchforge repository | `.github/`, local git | Founder / collaborators | High for change control | Low | **Yes** |
| Qdrant Cloud | Optional vector retrieval | Lab / notice wedge | Cluster URL via `QDRANT_URL` | `configs/demo.env.example`, Secret `fiqa-qdrant-api-key` | Vendor + Secret Manager | **Optional** for intake-core readiness | Medium if used | **No** for core Claim / Accident Story |
| Neon | Historical alternative DB | None (rejected) | — | Explicit “DO NOT set Neon” in env examples | — | — | — | **No** — deliberately excluded |

---

## Environment separation (must not mix)

| Concern | Cloud QA | Production |
|---------|----------|------------|
| Cloud Run | `fiqa-api-qa` | `fiqa-api` |
| Database | `caseiq-qa` | `caseiq` |
| DB secret | `fiqa-service-record-database-url-qa` | `fiqa-service-record-database-url-cloudsql-private` |
| Workbench | waterwoods Preview | `ui-smoky-beta` |
| Accident Story pilot | Allowed only after Founder GO | Not authorized by freeze |

---

## Feature-flag / kill-switch references (names only)

| Flag | Role |
|------|------|
| `ACCIDENT_STORY_ASSISTANT_ENABLED` | Master kill switch |
| `ACCIDENT_STORY_LLM` | Live LLM arm (default off in code) |
| `ACCIDENT_STORY_OFFICE_ALLOWLIST` | Office restriction |
| `ACCIDENT_STORY_LANGSMITH_TRACING` | Trace gate |
| `ACCIDENT_STORY_LANGSMITH_PROJECT` | Clean pilot project target |
| `UNIFIED_INTAKE_PRODUCT_ONLY` | Hide lab routers |
| `UNIFIED_INTAKE_INTAKE_API_KEY` / `SUPPORT_API_KEY` | Coarse API perimeters |

Code: `services/fiqa_api/inbox_triage/accident_story_assistant/flags.py`.

---

## Cost posture (evidence-bounded)

From `docs/ops/GCP_COST_AUDIT_2026-08-03.md`:

- Actual 30/90-day spend via Billing API: **unavailable** in that audit (APIs/export not enabled).
- Verified shape: small Cloud SQL, Cloud Run minScale 0 / maxScale 2 for `fiqa-api` and `fiqa-api-qa`.
- Material risk called out: Artifact Registry / Cloud Build storage growth — not model spend.
- Do **not** invent monthly dollar savings or AI ROI in founder decisions.

---

## Required vs optional for restricted Accident Story pilot

| Required | Optional / defer |
|----------|------------------|
| GCP + Cloud Run QA + Cloud SQL `caseiq-qa` | Production Accident Story flags |
| Mini Program QA profile | Qdrant |
| Workbench QA Preview | LangSmith (intake works if tracing off) |
| Kill-switch runbook owner | Live OpenAI if running deterministic-only demo |
| Support API key for metrics manifest | Lab Cloud Run siblings |
