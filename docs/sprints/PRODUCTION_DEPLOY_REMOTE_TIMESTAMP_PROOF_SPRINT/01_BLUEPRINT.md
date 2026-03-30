# PRODUCTION DEPLOY + REMOTE TIMESTAMP PROOF — Blueprint

## Goal

Prove on the **real** stack (Cloud Run + Vercel) that:

- First **formal submit** sets `formal_submitted_at` and `updated_at`, persists the case, and reaches an office-visible lifecycle (e.g. `handed_off`).
- A later **customer append** keeps `formal_submitted_at` **unchanged** and advances `updated_at`.

## Non-goals

- No new product features, state redesign, or schema expansion beyond what already exists.
- Local-only proof is insufficient; remote API is the bar.

## Deploy targets

| Layer    | Target        | Commands (this sprint) |
|----------|---------------|-------------------------|
| Backend  | Cloud Run `fiqa-api` | `bash scripts/deploy_rag_demo.sh` |
| Frontend | Vercel `ui` project  | `cd ui && npx vercel --prod --yes -b VITE_API_BASE_URL=<Cloud Run HTTPS URL>` |

## Proof harness

- Full regression: `python3 scripts/test_inbox_triage_api.py --url <Cloud Run base URL>` (includes formal-submit + append Test 13).
- Explicit timestamp invariants: optional one-off HTTP sequence (create → sleep → append) asserting `formal_submitted_at` equality and `updated_at` strict increase (ISO compare).

## Success criteria

- Deploy completes; `/readyz` OK on the deployed host.
- Remote proof shows stable `formal_submitted_at` and newer `updated_at` after append.
- Vercel production alias loads; bundle bakes correct `VITE_API_BASE_URL`; CORS allows the Vercel origin.
