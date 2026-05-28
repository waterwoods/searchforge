# ROLE C PLUS FRONTEND DEPLOY + RUNTIME CHECK — Blueprint

## Goal

Ship **Role C Plus** UI (simulation tab: per-turn snapshots + end summary, bounded auto-run) to the **demo-facing Vercel production alias** and confirm the **bundled backend URL** returns triage/simulation payloads the UI expects.

## Non-goals

- No product redesign, no new features, no battery work, no Cloud SQL.

## Success criteria

1. Production alias serves a JS bundle that contains Role C Plus copy (e.g. `轻量多轮`, `逐轮快照`).
2. `VITE_API_BASE_URL` on production points at a live Cloud Run service that returns `add_car_turn_intent` on Add-Car triage and accepts `POST /api/inbox/simulation-role-c-customer`.
3. Andy can open one URL, navigate to Unified Intake → Simulation, pick Role C, and see Role C Plus panels.

## References

- UI: `ui/src/components/simulation/ScenarioReplayTab.tsx`, `roleCPlusHelpers.ts`, `ui/src/api/inboxTriage.ts`
- Deploy: `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` (`cd ui && vercel --prod`)
- Demo path: `/workbench/unified-intake` → Simulation tab → Role C scenario
