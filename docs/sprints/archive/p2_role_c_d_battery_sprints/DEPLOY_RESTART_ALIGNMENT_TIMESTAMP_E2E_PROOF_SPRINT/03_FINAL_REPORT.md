# Final Report — DEPLOY / RESTART ALIGNMENT + TIMESTAMP E2E PROOF

## Outcome

**PASS** on local runtime after backend restart.

## Runtime

- Stopped prior uvicorn on `127.0.0.1:8001`, started fresh `uvicorn services.fiqa_api.app_main:app --host 127.0.0.1 --port 8001`.
- Polled `/readyz` until `ok: true`.
- Repo HEAD at run: `cf16a01` (branch `chen-kui-insurance`, dirty tree — timestamp logic in `case_store.py` unchanged by this sprint).

## Proof

- `scripts/test_inbox_triage_api.py --url http://127.0.0.1:8001` — all tests passed, including formal submit + append block.
- Supplemental httpx run: after formal submit, `formal_submitted_at == created_at == updated_at`; after 1s + append, `formal_submitted_at` unchanged, `updated_at` advanced; `lifecycle_status` `handed_off` → `office_followup`.

## Frontend / Vercel

- **Not deployed** in this sprint. CORS log referenced `https://ui-smoky-beta.vercel.app`; production timeline UI must be verified after Andy pushes UI and Vercel build completes.

## Gaps to close

1. Same sequence against **Cloud Run** (or staging) URL if that is the trial backend.
2. Visual confirmation on **Vercel** that two-line timing matches API fields.
