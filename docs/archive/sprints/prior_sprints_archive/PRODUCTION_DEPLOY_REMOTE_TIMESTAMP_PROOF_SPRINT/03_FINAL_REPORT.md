# PRODUCTION DEPLOY + REMOTE TIMESTAMP PROOF — Final report

**Date (UTC):** 2026-03-30

## Outcome

- **Backend:** Deployed `fiqa-api` to Cloud Run; new revision **`fiqa-api-00046-9hl`**; canonical URL **`https://fiqa-api-g7zatxrycq-uw.a.run.app`** (gcloud also reported `https://fiqa-api-1013093472160.us-west1.run.app` for the same service).
- **Frontend:** Vercel production deploy completed; alias **`https://ui-smoky-beta.vercel.app`** → deployment **`https://ui-d8tu7ze6h-andys-projects-1f411b73.vercel.app`**. Build used `-b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app`.
- **Remote API proof:** `scripts/test_inbox_triage_api.py --url https://fiqa-api-g7zatxrycq-uw.a.run.app` — **all tests passed**, including formal-submit + append.
- **Explicit timestamp check:** After create, `formal_submitted_at == updated_at`; after 3s sleep + append, `formal_submitted_at` unchanged, `updated_at` strictly newer (example case `case_91047254c5d1`).
- **Remote UI:** Did not run full browser click-through. Verified: HTML loads, production JS chunk embeds Cloud Run URL and `formal_submitted_at` UI paths; CORS preflight from `https://ui-smoky-beta.vercel.app` to Cloud Run triage returns `access-control-allow-origin` matching Vercel.

## Notes

- Vercel build logs show non-fatal `fatal: not a git repository` during `vite build` (known from prior sprints).
- Consider adding an explicit `updated_at` assertion to `test_inbox_triage_api.py` Test 13 so CI catches regressions without a one-off script.
