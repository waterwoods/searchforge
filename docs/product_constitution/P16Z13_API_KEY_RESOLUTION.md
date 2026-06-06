# P16-Z13 Phase 1 — API Key Resolution

**Date:** 2026-06-02

---

## Why required?

| Key | Purpose |
|-----|---------|
| `UNIFIED_INTAKE_INTAKE_API_KEY` | Coarse perimeter on `/api/inbox/*` (excludes `/api/inbox/support/*` and WeChat OAuth callback). When set, requests must send `X-Unified-Intake-Api-Key` or `Authorization: Bearer`. |
| `UNIFIED_INTAKE_SUPPORT_API_KEY` | Separate perimeter on `/api/inbox/support/*` (deployment manifest, case-head export). |

Consumed in:

- `services/fiqa_api/security/intake_api_gate.py` — intake middleware
- `services/fiqa_api/security/support_export_gate.py` — support middleware
- `scripts/validate_pilot_deploy_env.py` — paid-pilot deploy gate
- `scripts/deploy_cloud_run_core.sh` — passes keys into Cloud Run env bundle

They are **internal operator shared secrets**, not broker IAM or per-customer auth.

---

## Reuse options checked

| Source | Result |
|--------|--------|
| Live Cloud Run (pre-deploy) | ❌ Keys never bound (anonymous_ok) |
| GCP Secret Manager | ❌ No `fiqa-unified-intake-*` secrets exist |
| `.env` / `.env.cloudrun.test` | ❌ Absent |

---

## Action taken

Generated two **distinct** 48-character hex secrets:

```bash
openssl rand -hex 24   # intake
openssl rand -hex 24   # support (second run)
```

**Source:** `openssl rand -hex 24` (run twice).  
**Storage:** `.env.cloudrun` (gitignored) — appended 2026-06-02.  
**Deploy:** Bound on Cloud Run revision `fiqa-api-00083-kng` via `deploy_paid_pilot.sh`.

**Preview wiring:** `ui/src/api/request.ts` sends `X-Unified-Intake-Api-Key` when `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` is set at Vercel build (`vercel deploy -b …`).

---

## Print table

| Key name | Source | Deploy ready |
|----------|--------|--------------|
| `UNIFIED_INTAKE_INTAKE_API_KEY` | `openssl rand -hex 24` → `.env.cloudrun` | **YES** |
| `UNIFIED_INTAKE_SUPPORT_API_KEY` | `openssl rand -hex 24` → `.env.cloudrun` | **YES** |

No placeholder values remain in `.env.cloudrun`.
