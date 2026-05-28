# Final report — ROLE C PLUS VISIBILITY + LOW-EYE-STRAIN UI POLISH

## What changed

- Added **`ROLE_C_PLUS_SCENARIO_ID`** and **`buildRoleCPlusScenarioCard`**; scenario list now includes a **distinct Role C Plus card** alongside Role C and Role D.
- **Role C lane logic** generalized (`isRoleCLane`) so triage, `hasMore`, snapshots, and auto-run apply to **both** C and C Plus selections.
- **Removed** the nested “Role C Plus” dashed subsection from inside the Role C panel; **added** pointer copy to choose the C Plus card for one-click run.
- **Role C Plus panel** when selected: primary **一键跑完** button + shared knobs via extracted **`roleCSharedKnobs`**.
- **Readability:** hero, scenario list, replay column, right rail, and snapshot blocks use stronger hierarchy, contrast, and spacing (inline styles only).

## Intentionally untouched

- Backend Role C simulation APIs and triage logic.
- Other Unified Intake tabs and global Ant Design theme.
- `add_car_scenario_replay.json` content (dynamic cards still override/filter C/D/C+).

## Rollback

**Yes — easy.** Revert changes in:

- `ui/src/components/simulation/ScenarioReplayTab.tsx`
- `ui/src/components/simulation/roleCReplay.ts`

Optionally remove this sprint doc folder.

## Validation performed

- `npm run build` in `ui/` — **passed**.
- **Live / demo URL:** not verified in this sprint (no deploy run here).

## Recommended next sprint

- Optional **deploy + smoke** on Vercel/demo URL for founder eyeball pass.
- **Workbench / portal** parity pass for the same readability principles if Simulation feedback is positive.
- Deeper **Role C Plus** UX: e.g. progress text during auto-run (still bounded, no redesign).
