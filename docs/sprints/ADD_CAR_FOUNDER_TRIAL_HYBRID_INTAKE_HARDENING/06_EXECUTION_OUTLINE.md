# Execution Outline

## Workstreams

1. **Product architect** — Blueprint, intake comparison, hybrid spec.
2. **Founder trial runner** — Scenario pack walkthrough (manual + sims).
3. **Intake mode analyst** — Mode A/B/C scoring and decision.
4. **Add-car flow worker** — UI hybrid card + composed message.
5. **QA / simulation** — Guardrail + multi-turn + stress + handoff timing.
6. **Reviewer** — Acceptance criteria vs results.

## Loop plan

| Loop | Activity | Outcome |
|------|----------|---------|
| **1** | Intake mode comparison | Hybrid (C) chosen for commercialization now |
| **2** | Implement FN-1 hybrid card | Customer Entry ships structured optional path |
| **3** | Retest + commercial judgment | Build + scripts green; founder checklist updated |
| **4** | Optional | **Skipped** — no second high-ROI change without scope creep |

## Simulation / validation

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py`
- `PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py`
- `cd ui && npm run build` (if UI touched)

## Deployment

- **Backend:** No change in this sprint → **no backend redeploy** for FN-1.
- **Frontend:** **Redeploy** hosting (e.g. Vercel) when ready so brokers see hybrid card.
