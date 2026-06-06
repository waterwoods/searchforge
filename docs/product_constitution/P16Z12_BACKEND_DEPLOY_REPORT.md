# P16-Z12 Phase 3 — Backend Deploy Report

**Date:** 2026-06-02

---

## Deploy status

**NOT EXECUTED** — blocked by Phase 2 (missing `UNIFIED_INTAKE_INTAKE_API_KEY` / `UNIFIED_INTAKE_SUPPORT_API_KEY` in `.env.cloudrun`).

---

## Live service snapshot (unchanged)

| Field | Value |
|-------|-------|
| **Revision** | `fiqa-api-00080-q48` |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Deploy timestamp** | Unknown (pre-sprint; GIT_SHA `0c2ed6d59`) |
| **Env posture** | `DEMO_MODE=true`, legacy dual-write hints, **not** paid-pilot tuple |

---

## Health probes (current)

| Endpoint | HTTP | Notes |
|----------|------|-------|
| `/healthz` | **404** | Not exposed on this service |
| `/readyz` | **200** | `{"ok":true,"status":"ready","intake_core_readiness":true,...}` |

---

## Expected after successful deploy

- New revision name from `gcloud run services describe`
- `GIT_SHA` ≈ `b0d6073` (or current HEAD at deploy time)
- `UNIFIED_INTAKE_PRODUCT_ONLY=1`, `DEMO_MODE` unset/0
- P16-Z10A/Z10B/Z11 triage markers + `office_*` fields on `/api/inbox/triage`
- Re-run acceptance cases against Cloud Run URL

---

*No deploy timestamp recorded for Z12 — manual fix required before retry.*
