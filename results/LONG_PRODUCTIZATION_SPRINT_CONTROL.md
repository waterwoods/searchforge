# LONG PRODUCTIZATION SPRINT — Control Note

**Branch:** `auto-evolution/long-productization-sprint-20260504-1910`  
**Base:** `auto-evolution/workbench-timeout-fix-20260504-1843`

## SPRINT_GOAL

- Workbench queue timeout fixed and validated on live API (`GET /api/inbox/cases`)
- Frontend Phase 2 advanced safely (thin extractions only)
- TriageResult contract clarified on the frontend without breaking API shape

## NON_GOALS

- No Vercel production promote
- No resolver / triage vehicle decision logic changes
- No risky hook extraction (`useTriage`, `useConversation`, etc.)
- No removal of API fields from types or responses

## TRACKS

| Track | Description |
|-------|-------------|
| **A** | Workbench timeout deploy + live timing + UI spot-check |
| **B** | Frontend decoupling (one safe Phase 2 extraction) |
| **C** | API contract classification (docs/helpers only, frontend) |

## VALIDATION_GATES

- `ui`: `npm run build`
- `ui`: `npx madge --circular --extensions ts,tsx src`
- Repo: `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_full_regression.py` or chaos fallback
- Live: `curl` timing on `/api/inbox/cases`
- Preview/local UI when SSO allows

## STATUS (updated at sprint end)

| Gate | Result |
|------|--------|
| Track A deploy | **PASS** — `fiqa-api-00077-qpq`, `CLOUD_RUN_USE_SECRET_MANAGER=1` |
| Track A timing | **PASS** — live `GET /api/inbox/cases?limit=50` **~4.8s** cold-path sample; **~0.79s** warm; HTTP 200 |
| Track B | **PASS** — `MyRequestsTab.tsx` thin wrapper; `UnifiedIntakePage` wired |
| Track C | **PASS** — `hasDebugSignals`, `pickTriageResultOptionalSignals`, docs; tag in `BrokerWorkbenchTab` queue cards |
| Loops | **PASS** — `npm run build`, madge, guardrail, `run_full_regression.py`, final curl |

### Deploy blockers resolved this sprint

1. **Dockerfile smoke test** pointed at `services.fiqa_api.models` but image build context **omitted** `services/fiqa_api/models/` because root `.gitignore` had bare `models/` (matches any `**/models/`). Fixed: `.gitignore` uses `/models/` (root HF cache only) so Cloud Build uploads the Python package.
2. **Plaintext `QDRANT_API_KEY` deploy** conflicted with Secret Manager binding on the live service. Deploy succeeded with `CLOUD_RUN_USE_SECRET_MANAGER=1` (per `deploy_rag_demo.sh`).

## Final judgment

**READY_FOR_PREVIEW_RETEST** — Automated bar for workbench latency is met on live API; full regression green; preview UI not exercised through automation (Vercel SSO login wall). See `LONG_PRODUCTIZATION_FINAL_REPORT` in chat output.

_Note:_ Per sprint non-goals, **no** Vercel production promote was run.
