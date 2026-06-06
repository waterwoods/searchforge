# P16 Environment Preservation Report

**Date:** 2026-06-05  
**Mission:** P16 Release Freeze — Phase 5  
**Mode:** Read-only audit — **secret values are never listed**  
**Sources:** `configs/demo.env.example`, `.env.cloudrun` (names only), Vercel project `ui`, Cloud Run service `fiqa-api`

---

## Executive summary

Paid-pilot **minimum tuple** is documented, present locally, and live on Cloud Run. Vercel Production has only two dashboard vars; Preview relies on **CLI build flags** at deploy time. Several live Cloud Run vars are absent from `.env.cloudrun` and under-documented in the example template.

| Platform | Posture |
|----------|---------|
| `.env.cloudrun` (local deploy source) | ✅ Pilot tuple complete; validates PASS |
| Cloud Run `fiqa-api` | ✅ Prod-like intake posture; secrets via Secret Manager |
| Vercel Production | ⚠️ Partial — 2 vars in dashboard; product_only may depend on deploy flags |
| Vercel Preview / Development | ❌ No dashboard vars — CLI `-b` flags only |

---

## Required variable matrix

Legend: **Doc** = in `configs/demo.env.example` (active or commented appendix) · **Local** = set in `.env.cloudrun` · **Cloud Run** = live revision `fiqa-api-00085-tn2` · **Vercel** = project dashboard

### Tier 1 — Paid pilot minimum (must survive promotion)

| Variable | Doc | Local (`.env.cloudrun`) | Cloud Run | Vercel |
|----------|:---:|:-----------------------:|:---------:|:------:|
| `ENV` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ | ✅ | ✅ | ⚠️ Prod dashboard only; Preview via `-b` |
| `SERVICE_RECORD_DATABASE_URL` | ✅ | ✅ | ✅ (Secret Manager: `fiqa-service-record-database-url`) | — |
| `UNIFIED_INTAKE_DB_PRIMARY_READS` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_DB_PRIMARY_WRITES` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_JSON_CASE_WRITES` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_JSON_READ_FALLBACK` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_PG_DUAL_WRITE` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_INTAKE_CORE_READINESS` | ✅ | ✅ | ✅ | — |
| `UNIFIED_INTAKE_INTAKE_API_KEY` | ✅ | ✅ | ✅ (plain env) | ⚠️ Optional `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` at build |
| `UNIFIED_INTAKE_SUPPORT_API_KEY` | ✅ | ✅ | ✅ (plain env) | — |
| `OPENAI_API_KEY` | ✅ | ✅ | ✅ (Secret Manager: `fiqa-openai-api-key`) | — |
| `ALLOWED_ORIGINS` | ✅ | ✅ | ✅ | — (backend only) |
| `VITE_API_BASE_URL` | ✅ | — | — | ✅ Production dashboard |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ (via doc cross-ref) | — | — | ✅ Production dashboard |
| `CLOUD_RUN_USE_SECRET_MANAGER` | ✅ | ✅ | ✅ (implicit via secret refs) | — |

### Tier 2 — Live on Cloud Run, optional in docs / local file

| Variable | Doc | Local | Cloud Run | Notes |
|----------|:---:|:-----:|:---------:|-------|
| `GIT_SHA` | ❌ | ❌ | ✅ | Set by `deploy_cloud_run_core.sh` at deploy |
| `SOURCE_REV` | ❌ | ❌ | ✅ | Same as `GIT_SHA` |
| `LLM_GENERATION_ENABLED` | ⚠️ commented | ❌ | ✅ | Implied when OpenAI key present |
| `ENABLE_ASSIST_LAYER` | ✅ optional | ❌ | ✅ | In demo.env.example optional block |
| `DEBUG_TRUTH_GUARDRAILS` | ✅ optional | ❌ | ✅ | |
| `ADD_CAR_CONTRACT_STRICT` | ✅ optional | ❌ | ✅ | |
| `TRANSLATION_ENABLED` | ❌ | ✅ | ✅ | Not in demo.env.example header |
| `TRANSLATION_PROVIDER` | ❌ | ✅ | ✅ | |
| `TRANSLATE_SOURCES_TO_ZH` | ❌ | ✅ | ❌ | Local + deploy source only |
| `QDRANT_API_KEY` | ✅ | ❌ | ✅ (Secret Manager) | Optional for intake-only SaaS |
| `UNIFIED_INTAKE_ALLOW_JSON_DEV_MODE` | ❌ | ✅ | ❌ | Local file only |

### Tier 3 — Documented but not required for current pilot

| Variable | Doc | Local | Cloud Run | Vercel |
|----------|:---:|:-----:|:---------:|:------:|
| `QDRANT_URL` | ✅ | ❌ | ❌ | — |
| `QDRANT_COLLECTION` | ✅ | ❌ | ❌ | — |
| `PILOT_DEPLOY_STRICT` | ✅ | ❌ | ❌ | — |
| `DEMO_MODE` | ✅ (dev only) | ❌ | ❌ | — |
| `WECHAT_*` | ✅ appendix | ❌ | ❌ | — |
| `UNIFIED_INTAKE_BROKER_TOKEN_*` | ✅ appendix | ❌ | ❌ | — |
| `LANGFUSE_*` | ✅ appendix | ❌ | ❌ | — |
| `CLOUD_RUN_MEMORY` / `CONCURRENCY` / `MIN_INSTANCES` | ✅ | ❌ | ✅ (via service spec, not env) | — |

---

## Platform detail

### `.env.cloudrun` (local deploy authority)

**Location:** repo root (git-ignored)  
**Validation:** `PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun` → **PASS** (2026-06-05)

**Variables present (names only):**

```
ALLOWED_ORIGINS
CLOUD_RUN_USE_SECRET_MANAGER
ENV
OPENAI_API_KEY
SERVICE_RECORD_DATABASE_URL
TRANSLATE_SOURCES_TO_ZH
TRANSLATION_ENABLED
TRANSLATION_PROVIDER
UNIFIED_INTAKE_ALLOW_JSON_DEV_MODE
UNIFIED_INTAKE_DB_PRIMARY_READS
UNIFIED_INTAKE_DB_PRIMARY_WRITES
UNIFIED_INTAKE_INTAKE_API_KEY
UNIFIED_INTAKE_INTAKE_CORE_READINESS
UNIFIED_INTAKE_JSON_CASE_WRITES
UNIFIED_INTAKE_JSON_READ_FALLBACK
UNIFIED_INTAKE_PG_DUAL_WRITE
UNIFIED_INTAKE_PRODUCT_ONLY
UNIFIED_INTAKE_SUPPORT_API_KEY
```

**Gap:** Does not include `ENABLE_ASSIST_LAYER`, `DEBUG_TRUTH_GUARDRAILS`, `ADD_CAR_CONTRACT_STRICT`, `LLM_GENERATION_ENABLED` — deploy script adds defaults for assist layer flags; Cloud Run live revision has them.

---

### Cloud Run (`fiqa-api`, `us-west1`)

**Revision:** `fiqa-api-00085-tn2`  
**URL:** `https://fiqa-api-g7zatxrycq-uw.a.run.app`

**Plain env vars (names only):**

```
ADD_CAR_CONTRACT_STRICT
ALLOWED_ORIGINS
DEBUG_TRUTH_GUARDRAILS
ENABLE_ASSIST_LAYER
ENV
GIT_SHA
LLM_GENERATION_ENABLED
SOURCE_REV
TRANSLATION_ENABLED
TRANSLATION_PROVIDER
UNIFIED_INTAKE_DB_PRIMARY_READS
UNIFIED_INTAKE_DB_PRIMARY_WRITES
UNIFIED_INTAKE_INTAKE_API_KEY
UNIFIED_INTAKE_INTAKE_CORE_READINESS
UNIFIED_INTAKE_JSON_CASE_WRITES
UNIFIED_INTAKE_JSON_READ_FALLBACK
UNIFIED_INTAKE_PG_DUAL_WRITE
UNIFIED_INTAKE_PRODUCT_ONLY
UNIFIED_INTAKE_SUPPORT_API_KEY
```

**Secret Manager bindings (names only):**

```
OPENAI_API_KEY          → fiqa-openai-api-key
QDRANT_API_KEY          → fiqa-qdrant-api-key
SERVICE_RECORD_DATABASE_URL → fiqa-service-record-database-url
```

**Runtime sizing (service spec, not env):** memory 1Gi, concurrency 30, min instances 0, max 2.

---

### Vercel (project: `andys-projects-1f411b73/ui`)

**Dashboard environment variables:**

| Name | Environments | Created |
|------|--------------|---------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | Production | 4 days ago |
| `VITE_API_BASE_URL` | Production | 85 days ago |

**Preview / Development:** No dashboard vars — builds depend on operator passing `-b VITE_…` at `vercel deploy` time.

**Documented but not in Vercel dashboard:**

| Variable | Where documented | Risk |
|----------|------------------|------|
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | `P16Z13_API_KEY_RESOLUTION.md` | Preview builds may omit unless `-b` flag used |
| `VITE_APP_ENV` | `ReleaseIdentityBar.tsx` | Optional display only |

---

### `configs/demo.env.example` (committed template)

**Location:** `configs/demo.env.example`  
**Purpose:** Operator template; safe to commit (no secrets)

**Documented variable families:**

- Pilot one-path block (Postgres, product_only, API keys, CORS)
- Local recommended block (`RUN_DEMO_LAB`, intake-core readiness)
- Optional tuning (assist layer, add-car flags)
- Dev-only (`DEMO_MODE`, JSON paths)
- Lab-only (OCR, Google keys)
- Legacy compatibility (JSON dual-write)
- Internal deploy plumbing (`PROJECT_ID`, `REGION`, Cloud Run sizing, Secret Manager, WeChat, Langfuse)

**Variables live on Cloud Run but missing from example header:**

| Variable | Recommendation |
|----------|----------------|
| `GIT_SHA` / `SOURCE_REV` | Add deploy-plumbing note (auto-set by script) |
| `TRANSLATION_ENABLED` | Add optional i18n block |
| `TRANSLATION_PROVIDER` | Add optional i18n block |
| `TRANSLATE_SOURCES_TO_ZH` | Add optional i18n block |

---

## Preservation risks before mainline promotion

| Risk | Severity | Mitigation |
|------|----------|------------|
| `.env.cloudrun` is git-ignored and machine-local | 🔴 | Export var **names** + Secret Manager mapping to runbook; never commit secrets |
| Vercel Preview vars not in dashboard | 🟡 | Document canonical `vercel deploy -b …` incantation in RELEASE_CHECKLIST |
| `ALLOWED_ORIGINS` drift on redeploy | 🟡 | Keep complete list in `.env.cloudrun`; run `guardrail_cloudrun_runtime.sh` after deploy |
| API keys in plain Cloud Run env (not Secret Manager) | 🟡 | `UNIFIED_INTAKE_*_API_KEY` are plain env today; consider Secret Manager migration post-promotion |
| Production Vercel env 85 days old | 🟡 | Verify `VITE_API_BASE_URL` still matches live Cloud Run URL before prod promote |

---

## Missing-from-documentation summary

| Variable | Stored in platform | Action |
|----------|-------------------|--------|
| `GIT_SHA` | Cloud Run | Document as deploy-script output |
| `SOURCE_REV` | Cloud Run | Document as deploy-script output |
| `TRANSLATION_*` | `.env.cloudrun`, Cloud Run | Add to demo.env.example appendix |
| `TRANSLATE_SOURCES_TO_ZH` | `.env.cloudrun` only | Document or remove if unused |
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | Preview CLI builds | Add to DEPLOYMENT_PLAYBOOK frontend table |

---

*End of P16 Environment Preservation Report — Phase 5*
