# Acceptance Criteria

## Product behavior criteria

- Add-Car clean/partial/correction/materials/prospective-send scenarios must reach coherent handoff behavior.
- Boundary case must classify as new issue when customer pivots from add-car to billing.
- Client isolation spot check must show client-specific wording differences (`办公室` vs `本所`).
- Flagship one-message case must remain broker-credible even if minor field follow-up is still needed.

## Readiness criteria

- `bash scripts/guardrail_inbox_triage.sh` passes.
- `bash scripts/trial_readiness_check.sh` passes (includes UI build check).
- Any failed targeted scenario must be judged as:
  - release-blocking, or
  - acceptable caveat for broker demo with explicit founder talking points.

## Acceptance decision rules

- **Show now:** no trust-breaking failure, guardrail pass, trial-readiness pass, caveats explainable.
- **Hold:** trust-breaking extraction/routing issues, major guardrail regression, or unusable demo stack.

## Evidence labels

- **Directly verified:** command output or runner JSON from this sprint.
- **Inferred:** based on existing guardrail/readiness outputs and prior validated paths.
- **Not verified:** production/Vercel checks not executed during this sprint.
