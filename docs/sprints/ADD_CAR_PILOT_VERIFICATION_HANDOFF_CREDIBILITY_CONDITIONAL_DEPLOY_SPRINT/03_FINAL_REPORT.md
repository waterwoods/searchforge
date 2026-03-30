# ADD-CAR Pilot Verification + Handoff Credibility + Conditional Deploy — Final report

## Executive summary

- **Verified (automated):** Full `scripts/guardrail_inbox_triage.sh` **PASS** (64 scenario pack, multi-turn 69/69, adversarial/complex packs, broker stress **13/13** including already-sent and “微信发过了”, handoff timing **13/13**, case boundary 23/23, cross-client A/B batteries). `scripts/run_add_car_realistic_intake_scenarios.py` completed successfully (exit 0).
- **Verified (read-through):** Chen Kui `ui_copy.json` handoff closure, post-handoff hints, workbench parity copy; `clientConfig.ts` keys; `triage.py` / `reply_templates.json` already_sent branches.
- **Verified (production probe):** `GET https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz` → **HTTP 200**, `intake_path_ready: true`, `demo_mode: true` (embedding/qdrant clients not “ready” but intake path flagged ready — consistent with pilot/demo stance).
- **Not verified this session:** Local `http://localhost:8001` API test (**SKIPPED** — no server). Browser E2E on deployed UI not run. **Deployment commands not executed** — `scripts/check_env_vars.sh` reported missing `QDRANT_*`, `GCP_PROJECT`, `GCP_REGION`.
- **Code changes:** None (no clear release-blocking defect found).

## Release gate

**PASS WITH CAUTIONS**

**Why PASS side:** Rule-path and simulation coverage for Add-Car happy path, already_sent, materials sent, corrections, and append/boundary is strong; handoff copy is broker-grade in config; production API responds with intake readiness.

**Why CAUTIONS:** (1) Chat-thread centric UX and workbench/customer **STATE** parity remain mid-maturity per industrial scorecard. (2) Persistence/auth/PII are pilot-tier per truth switch. (3) This session did not run local live API or full deploy verification. (4) Deploy was **not** performed from this environment due to missing Cloud Run env vars.

## Deployment result

| Surface | Result |
|---------|--------|
| Frontend (e.g. Vercel) | **Not run** — no deploy executed in this session. |
| Backend (Cloud Run) | **Not run** — required env vars absent (`check_env_vars.sh` failed). |

## What remains

- Run **local** `run_demo_local.sh` + `test_inbox_triage_api.py` before broker demo.
- Andy (or CI) runs deploy scripts with secrets when choosing to push a new build.
- Real broker feedback on **tone length** and **“像不像真人柜台”** (scorecard HANDOFF 3 → 4).

## Recommended next step

**Collect constrained pilot feedback** on Add-Car + handoff + workbench while running guardrail before each release candidate; optional small reply polish sprint if brokers flag procedural tone.

## Sprint timing

- **Date:** 2026-03-28  
- **Elapsed (rough):** ~35–50 minutes (read-first, guardrail, scenarios, prod probe, docs)
