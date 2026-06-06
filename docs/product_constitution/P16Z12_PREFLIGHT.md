# P16-Z12 Phase 1 — Preflight Reality Check

**Date:** 2026-06-02  
**Sprint:** P16-Z12 Backend Deploy + Preview Reality Validation  
**Branch:** `sprint-a/broker-front-door`

---

## Git state

| Item | Value |
|------|-------|
| **Branch** | `sprint-a/broker-front-door` |
| **Commit** | `b0d6073e5cbd51585a965390cea471ad1fa07422` |
| **Latest message** | (see `git log -1`) |
| **Dirty files** | **1675** paths modified/untracked — large doc/archive churn plus intake/triage/UI deltas on this branch; not a clean deploy tree |

---

## Backend env readiness

| Check | Result |
|-------|--------|
| `.env.cloudrun` exists | ✅ |
| `validate_pilot_deploy_env.py` | ❌ **FAIL** |
| `SERVICE_RECORD_DATABASE_URL` | ✅ set (value redacted) |
| `UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ `1` |
| `ALLOWED_ORIGINS` | ✅ set (8 origins) — **does not include** current Preview host `ui-d7pyq2yau` |
| **Backend deploy readiness** | **NO** |

### Missing env vars (validator)

- `UNIFIED_INTAKE_INTAKE_API_KEY` — not set in `.env.cloudrun`
- `UNIFIED_INTAKE_SUPPORT_API_KEY` — not set in `.env.cloudrun`

### Secret Manager

| Secret | Present |
|--------|---------|
| `fiqa-openai-api-key` | ✅ |
| `fiqa-qdrant-api-key` | ✅ |
| `fiqa-service-record-database-url` | ✅ |
| Intake / support API key secrets | ❌ **none** |

`CLOUD_RUN_USE_SECRET_MANAGER=1` binds OpenAI/Qdrant/DB only — not intake perimeter keys.

---

## Live Cloud Run (pre-deploy)

| Item | Value |
|------|-------|
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | `fiqa-api-00080-q48` |
| **GIT_SHA (deployed)** | `0c2ed6d59` — **≠** local `b0d6073` |
| **DEMO_MODE** | `true` (legacy demo posture) |
| **UNIFIED_INTAKE_INTAKE_API_KEY on service** | ❌ not present |
| **UNIFIED_INTAKE_PRODUCT_ONLY** | ❌ not present |

---

## Preview / Vercel

| Item | Value |
|------|-------|
| **Preview URL** | https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| **Bundle** | `index-BbeKEpPA.js` |
| **VITE_API_BASE_URL in bundle** | `fiqa-api-g7zatxrycq-uw.a.run.app` ✅ |
| **Product markers in bundle** | `请把您的需求发给我们`, `原样粘贴微信` ✅ |
| **Vercel dashboard env** | `VITE_*` only on **Production** — Preview relies on deploy `-b` flags (P16-Z11 deploy) |
| **Cold HTTP** | 200 (no SSO wall) ✅ |

---

## Local runtime

| Item | Value |
|------|-------|
| **:8001 /readyz** | 200, `intake_core_readiness: true` |
| **Role D (local module battery)** | reread **82.6**, needs WeChat **0/10**, waiting **9/9**, claims **71%** |

---

## Preflight verdict

Preview UI is reachable and points at Cloud Run, but **backend is stale** and **paid-pilot deploy cannot run** until API keys are in `.env.cloudrun`. CORS will **fail** from this Preview origin until `ALLOWED_ORIGINS` is updated and redeployed.
