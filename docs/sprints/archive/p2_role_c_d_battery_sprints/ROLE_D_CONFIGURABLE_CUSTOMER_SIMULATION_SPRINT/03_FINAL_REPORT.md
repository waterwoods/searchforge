# ROLE D CONFIGURABLE CUSTOMER SIMULATION — Final Report

## Implemented

- **`roleDReplay.ts`** — Seven persona templates × three difficulty tiers; deterministic Chinese (and some zh/en mix) multi-turn scripts including typos, wrong-year corrections, fragmented turns, spouse/household, materials-sent ambiguity, VIN delay, and price sensitivity.
- **`addCarReplayTypes.ts`** — Shared `AddCarReplayScenario` type for JSON scenarios and Role D output (avoids circular imports).
- **`ScenarioReplayTab.tsx`** — Appends generated Role D scenario to the card list; configuration panel when D is selected; syncs selected scenario when D regenerates; resets replay on D config change.
- **`add_car_scenario_replay.json`** — Description note that Role D is UI-generated.

## Partial / deferred

- Custom note only **prepends context into turn 1**; it does not yet branch internal scripts by keyword.
- No per-run **random seed** — same config always yields the same lines (good for regression; less “surprise” coverage).
- Role C remains placeholder; no merge of D with controlled LLM.

## Recommended next sprint

- **Small seed knob** (optional integer) that swaps among pre-authored alternates for the same template+difficulty, or keyword hooks from the one-line note to pick sub-variants.
- **Guardrail scenario**: one Role D config checked into a script that hits `triage` in CI (if not already covered by existing batteries).

## Validation

- `cd ui && npm run build` — passed.
- Live triage against a running API was **not** executed in this session (blocked without `run_demo_local` + manual click-through).
