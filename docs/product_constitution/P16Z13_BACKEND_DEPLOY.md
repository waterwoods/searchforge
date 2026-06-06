# P16-Z13 Phase 3 — Backend Deploy

**Date:** 2026-06-02

---

## Status

**EXECUTED** — paid-pilot Cloud Run deploy succeeded.

---

## Revision chain

| Step | Revision | Notes |
|------|----------|-------|
| Initial paid-pilot deploy | `fiqa-api-00081-jhm` | Image `b0d6073`, intake/support keys, CORS 9 origins |
| `LLM_GENERATION_ENABLED=0` | `fiqa-api-00082-565` | Rules path parity with local batteries |
| CORS + new Preview host | `fiqa-api-00083-kng` | 10 origins incl. `ui-o6ipsmqzv` |

**Current serving revision:** `fiqa-api-00083-kng`

---

## Print block

| Field | Value |
|-------|-------|
| **Revision** | `fiqa-api-00083-kng` |
| **GIT SHA** | `b0d6073e5` (from deployment-manifest `git.commit`) |
| **Deploy timestamp** | 2026-06-02T09:04Z (UTC, revision 00083) |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |

---

## Posture verified

| Check | Result |
|-------|--------|
| `DEMO_MODE` | **off** (`demo_mode: false` in manifest) |
| `UNIFIED_INTAKE_PRODUCT_ONLY` | **1** |
| `/readyz` | **PASS** (`intake_core`, `intake_path_ready: true`) |
| `/health/live` | **PASS** (200) |
| `/healthz` | 404 at edge (use `/health/live` on Cloud Run) |
| Intake perimeter | **api_key_required** — anonymous `POST /api/inbox/triage` → **401** |

---

## Commands used

```bash
# After keys + CLOUD_RUN_USE_SECRET_MANAGER=1 in .env.cloudrun
bash scripts/deploy_paid_pilot.sh

gcloud run services update fiqa-api --region us-west1 --project optimal-disk-472305-e2 \
  --update-env-vars "^|^LLM_GENERATION_ENABLED=0"

# CORS for new Vercel host
gcloud run services update fiqa-api ... --update-env-vars "^|^ALLOWED_ORIGINS=<comma-separated list>"
```
