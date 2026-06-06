# Founder Inspection Notes

## What was directly run

- `PYTHONPATH=. python3 scripts/run_pre_broker_targeted_acceptance.py`
  - Result: 10/11 pass
  - File: `results/targeted_acceptance_results.json`
- `bash scripts/guardrail_inbox_triage.sh`
  - Result: PASS
  - File: `results/guardrail_inbox_triage.txt`
- `bash scripts/trial_readiness_check.sh`
  - Result: PASS
  - File: `results/trial_readiness_check.txt`
- Local backend probe: `curl http://127.0.0.1:8001/healthz`
  - Result: unreachable in this session (`000`)

## Key observed strengths

- Add-Car clean/partial/correction/materials/prospective-send all route to credible handoff.
- Boundary behavior correctly detects a new issue when billing appears in add-car append.
- Client wording isolation spot check shows expected office voice split:
  - `chen_kui`: `办公室`
  - `socal_precision`: `本所`
- Full guardrail and trial-readiness suites passed.

## Main caveat observed in targeted set

- `PBTA-10` failed strict expectation due to inconsistent state:
  - `quote_ready_status` = `quote_ready`
  - but `still_needed_fields` includes `delivery_date`
- This is not a crash; it is a semantic consistency caveat to avoid overselling in demo narration.

## Deployment/readiness evidence quality

- **Directly verified:** local guardrail/trial-readiness outputs and UI build pass.
- **Inferred:** backend/frontend codepaths are healthy for demo because guardrail + readiness passed.
- **Not verified in this sprint:** live Cloud Run revision, Vercel production alias target, and production URL alignment.

## Founder demo caution lines

- Do not claim "fully production-verified deployment alignment" without running Cloud Run + Vercel post-deploy checks from `docs/runbooks/DEPLOYMENT_PLAYBOOK.md`.
- Phrase accurately: "Core intake behavior is stable and demo-ready; production endpoint alignment still needs explicit release verification."
