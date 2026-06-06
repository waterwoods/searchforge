# P16-Z13 Phase 4 — CORS Report

**Date:** 2026-06-02

---

## ALLOWED_ORIGINS (live after revision 00083)

1. `https://ui-smoky-beta.vercel.app`
2. `https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app`
3. `https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app`
4. `https://ui-git-main-andys-projects-1f411b73.vercel.app`
5. `https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app`
6. `https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app`
7. `https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app`
8. `https://ui-waterwoods-andys-projects-1f411b73.vercel.app`
9. `https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app` (Z12 URL)
10. `https://ui-o6ipsmqzv-andys-projects-1f411b73.vercel.app` (**Z13 new deploy**)

---

## Current Preview / Vercel host

| Host | Role |
|------|------|
| `https://ui-o6ipsmqzv-andys-projects-1f411b73.vercel.app` | **Active Z13 Preview** (2026-06-02 deploy) |
| `https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app` | Z12 URL (still in CORS list) |

---

## Probe results (active Preview origin)

**Origin:** `https://ui-o6ipsmqzv-andys-projects-1f411b73.vercel.app`  
**API:** `https://fiqa-api-g7zatxrycq-uw.a.run.app`

| Test | Result |
|------|--------|
| OPTIONS `/api/inbox/triage` | **PASS** — 200, `access-control-allow-origin` matches Preview |
| POST `/api/inbox/triage` (with intake key + Origin) | **PASS** — 200 JSON |
| Browser (credentials + intake header via Vite build) | **PASS** — CORS + key wired in Z13 UI build |

---

## Print

| Field | Value |
|-------|-------|
| **Origin list** | 10 Vercel/production hosts (see above) |
| **PASS / FAIL** | **PASS** (for `ui-o6ipsmqzv`) |

**FAIL** for any **new** `ui-*` Vercel URL until appended to `ALLOWED_ORIGINS` and Cloud Run updated.
