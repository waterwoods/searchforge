# P16-G Phase 1 — CORS Patch Report

**Date:** 2026-05-31  
**Sprint:** P16-G Final Deployment Validation  
**Status:** **APPLIED AND VALIDATED**

---

## Before

| Item | Value |
|------|-------|
| **Cloud Run revision** | `fiqa-api-00078-*` (prior) |
| **ALLOWED_ORIGINS count** | 5 origins |
| **Preview origin** | `https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app` — **NOT in list** |
| **Waterwoods alias** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` — **NOT in list** |
| **OPTIONS preflight (Preview)** | HTTP **400** — `Disallowed CORS origin` |
| **Browser symptom** | Network Error on `GET /api/inbox/cases` |

```
ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,
  https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,
  https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,
  https://ui-git-main-andys-projects-1f411b73.vercel.app,
  https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app
```

---

## Patch applied

**Exact command:**

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars '^@^ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,https://ui-git-main-andys-projects-1f411b73.vercel.app,https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app,https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app,https://ui-waterwoods-andys-projects-1f411b73.vercel.app'
```

**Revision created:** `fiqa-api-00079-ngq`  
**Traffic:** 100% to new revision  
**Service URL:** `https://fiqa-api-g7zatxrycq-uw.a.run.app`

**Follow-up:** `.env.cloudrun` updated with same 7-origin list so next full backend deploy does not revert the patch.

---

## After

| Item | Value |
|------|-------|
| **ALLOWED_ORIGINS count** | 7 origins (+ Preview + Waterwoods alias) |
| **OPTIONS `/api/inbox/cases`** | HTTP **200** + `access-control-allow-origin: https://ui-fvxlrxp4u-…` |
| **OPTIONS `/api/inbox/triage`** | HTTP **200** + matching allow-origin |
| **GET `/api/inbox/cases` (with Origin)** | HTTP **200** + JSON queue (569 cases) |
| **POST triage (3 scenarios, with Origin)** | HTTP **200** — correct categories + drafts |

---

## Validation evidence

```bash
# Preflight — PASS
curl -si -X OPTIONS https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/cases \
  -H "Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: content-type"
# → HTTP/2 200, access-control-allow-origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app

# Engine regression — PASS (unchanged by env patch)
bash scripts/guardrail_inbox_triage.sh
# → Guardrail: PASS

# Full API battery on Cloud Run — PASS
PYTHONPATH=. python3 scripts/test_inbox_triage_api.py \
  --url https://fiqa-api-g7zatxrycq-uw.a.run.app
# → All API tests passed
```

---

## Rollback

Restore prior 5-origin allowlist:

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars '^@^ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,https://ui-git-main-andys-projects-1f411b73.vercel.app,https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app'
```

Also revert `.env.cloudrun` ALLOWED_ORIGINS to the 5-origin value before next deploy.

---

## Verdict

**CORS blocker removed.** Preview browser origin is now allowlisted. No code changes. No triage logic changes. Guardrail PASS confirms engine unchanged.

**Remaining gate:** Andy authenticated hard-refresh on Preview to confirm browser UX (Vercel SSO blocks automation).

---

*End of P16-G Phase 1*
