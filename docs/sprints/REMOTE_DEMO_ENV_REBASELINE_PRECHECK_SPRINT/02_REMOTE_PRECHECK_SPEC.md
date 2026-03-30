# REMOTE / DEMO ENV REBASELINE + PRECHECK — Spec

## Demo URL / backend mapping

| Surface | Canonical URL | Notes |
|--------|----------------|-------|
| **Frontend (Vercel alias)** | `https://ui-smoky-beta.vercel.app` | Unified Intake: `/workbench/unified-intake` |
| **Backend (Cloud Run)** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | Same service as `https://fiqa-api-1013093472160.us-west1.run.app` (alternate hostname) |

**Verified (this sprint):** Production JS bundle `index-*.js` on `ui-smoky-beta.vercel.app` embeds `https://fiqa-api-g7zatxrycq-uw.a.run.app`—no frontend redeploy was required after backend-only rebaseline.

## Chosen deploy / restart path

- **Command:** `bash scripts/deploy_rag_demo.sh` from repo root (loads `.env.cloudrun`, Cloud Build + Cloud Run deploy).
- **Prereqs:** `gcloud` authenticated, `.env.cloudrun` present (gitignored).

## Proof expectations

1. **Readiness:** `GET /readyz` → 200, `intake_path_ready: true` (demo stance).
2. **Intent visibility:** `POST /api/inbox/triage` with Add-Car context (e.g. `soft_route: "add_car"`) returns `add_car_turn_intent` as an **object** with at least `intent_family`, `handoff_base_key`, `phrase_storage_key`, `truth_notes`.
3. **Stale vs fresh:** Before deploy, `add_car_turn_intent` was **null** on the same probe; after deploy, **non-null**—direct evidence of revision alignment.

## Smoke expectations (bounded)

- Run `python3 scripts/test_inbox_triage_api.py --url https://fiqa-api-g7zatxrycq-uw.a.run.app` — full script pass on remote.
- **Manual multi-turn (optional minimum):** Add-Car thread → `formal_submit` with non-empty `text` (API rejects empty text) → post-submit question e.g. “大概多久能出报价？” → expect `add_car_turn_intent.intent_family` ≈ timeline-style and reply opens with a **process/timeline-oriented head** (intent-specific prefix).

## Acceptance criteria

| Criterion | Met when |
|-----------|----------|
| Remote rebaselined | New Cloud Run revision deployed from current repo |
| `add_car_turn_intent` visible | Non-null object on representative Add-Car POST |
| Remote API tests | `test_inbox_triage_api.py --url` all PASS |
| Late-turn reply head | At least one remote example shows intent-specific opener on post-submit turn |
| Vercel ↔ API | Production bundle still targets the same Cloud Run host |
