# Targeted Scenario Selection Spec

## Selection strategy

- Chosen for broker-facing realism, high demo relevance, and acceptance value.
- Keep scope to 11 scenarios (within 8-12 target).
- Cover required Add-Car flow types, boundary behavior, client isolation, and flagship single-message intake.

## Scenario set (11)

1. `PBTA-01` Add-Car clean path
2. `PBTA-02` Add-Car partial -> completion
3. `PBTA-03` Add-Car correction path
4. `PBTA-04` Add-Car materials-sent
5. `PBTA-05` Add-Car ask-to-send / prospective-send
6. `PBTA-06` Add-Car price-sensitive / ballpark
7. `PBTA-07` Add-Car handoff / office-processing clarity
8. `PBTA-08` Append boundary (new issue from add-car thread)
9. `PBTA-09A` Client isolation spot check (chen_kui)
10. `PBTA-09B` Client isolation spot check (socal_precision)
11. `PBTA-10` Flagship all-info-in-one-message

## Why this set

- Focuses on the final broker demo risks: quote intake trust, handoff clarity, and boundary separation.
- Includes one realistic price-sensitive ask (common in broker conversations).
- Includes explicit client wording isolation check to prevent cross-client leakage claims.
- Includes one dense flagship case for founder live demo.

## Runner and evidence files

- Runner: `scripts/run_pre_broker_targeted_acceptance.py`
- Output: `docs/sprints/PRE_BROKER_TARGETED_ACCEPTANCE_SPRINT/results/targeted_acceptance_results.json`
