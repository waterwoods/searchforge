# Pre-Broker Targeted Acceptance Sprint Blueprint

## Sprint intent

- Final targeted simulation before broker review (Chen Kui) for Unified Intake.
- Acceptance sprint only: verify credibility, readiness, and demo suitability.
- Avoid scope expansion; only document caveats unless a fix is clearly broken/high-impact/low-risk.

## Timebox and operating mode

- Target duration: 30-45 minutes.
- Mode: scenario selection -> targeted simulation -> readiness check -> acceptance judgment.
- Evidence hierarchy: directly verified > inferred > not verified.

## Required acceptance questions

1. Is current product ready enough to show Chen Kui now?
2. Do key Add-Car and boundary scenarios behave credibly?
3. Is UI/API deployment state aligned enough for founder demo?
4. What are last caveats?
5. What are best two demo cases?

## Execution plan

1. Select 8-12 broker-relevant scenarios (include required categories).
2. Run focused targeted battery and required guardrail:
   - `PYTHONPATH=. python3 scripts/run_pre_broker_targeted_acceptance.py`
   - `bash scripts/guardrail_inbox_triage.sh`
   - `bash scripts/trial_readiness_check.sh`
3. Check live/deploy state signals:
   - local backend health (`/healthz`)
   - trial readiness output (UI build and guardrail)
   - deployment runbook constraints and what is still unverified.
4. Produce founder-readable acceptance judgment and two demo picks.

## Exit criteria

- Targeted scenarios executed with pass/fail and caveat notes.
- Guardrail and trial-readiness status captured.
- Clear "show now / hold" decision with non-oversell guidance.
- Two paste-ready demo cases documented.
