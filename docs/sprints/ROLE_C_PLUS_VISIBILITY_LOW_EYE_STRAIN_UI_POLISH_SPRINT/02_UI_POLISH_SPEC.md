# UI polish spec — Role C Plus visibility + readability

## Role C Plus visibility model

- **New scenario id:** `ADD_CAR_C_PLUS` (`ROLE_C_PLUS_SCENARIO_ID` in `roleCReplay.ts`).
- **List placement:** Injected next to generated Role C and Role D cards (after static JSON scenarios, before or beside peer cards as implemented).
- **Card copy:** Title **「Role C Plus · 一键多轮」**; subtitle states lightweight auto-run and shared engine with Role C.
- **Controls:** When Role C Plus is selected, a dedicated panel shows:
  - Primary **「一键跑完」** action (same `runRoleCFullSimulation` as before).
  - Shared knobs (persona, note, difficulty, max turns) labeled as synced with Role C.
- **Role C:** Unchanged behavior for manual **下一步**; nested Role C Plus block **removed** from Role C panel; one-line pointer to select the C Plus card for auto-run.

## Readability improvements (bounded)

- Darker primary text (`#262626` / `#434343`) vs default Ant secondary grays where it mattered.
- Slightly larger section titles and card titles; increased line-height on hero and thread.
- Thread container: stronger border and `#f5f5f5` tray; bubble text 14px, clearer label color.
- Snapshot rows: stronger borders, padding, and body color for customer/assistant lines.
- Scenario cards: active state ring via box-shadow; subtitle no longer `type="secondary"` at tiny size only.

## Rollback principle

- No global theme tokens changed; no `ConfigProvider` overrides.
- Revert edits to `ScenarioReplayTab.tsx` and `roleCReplay.ts` only (plus removing this sprint folder if desired).

## Acceptance criteria

- [ ] Role C Plus appears as its **own** selectable scenario card before using Role C.
- [ ] Role C remains available with manual step-by-step flow.
- [ ] One-click full run works from Role C Plus selection.
- [ ] Snapshots + end report still show for both Role C and Role C Plus lanes.
- [ ] `npm run build` passes in `ui/`.
- [ ] Changes are localized and easy to revert by file rollback.
