# ROLE C PLUS LIGHTWEIGHT FRONTEND SPRINT — Final report

## What was implemented

1. **`add_car_turn_intent` on `TriageResult`** (`ui/src/api/inboxTriage.ts`) so the UI can type-check intent payloads returned by Add-Car triage.
2. **`roleCPlusHelpers.ts`** — builds per-turn snapshots from replay, end summary, and bounded frontend heuristics (reply repeat, intent stuck/missing late, handoff vs still-needed, lifecycle vs `formal_submitted_at`).
3. **`ScenarioReplayTab.tsx`** — Role C Plus **一键跑完** control under existing Role C panel; `runRoleCFullSimulation` loop mirroring manual Role C; full-width **逐轮快照与结束报告** card when Role C is selected.

## What stayed intentionally lightweight

- No new backend endpoints or persistence.
- Heuristics are **best-effort**; no claim of full QA coverage.
- Reply/intent snippets are clipped for readability.
- Auto-run does not orchestrate formal submit (same as existing simulation triage).

## Future work (not this sprint)

- Optional: dedicated `loading` source enum so manual vs auto messaging could differ.
- Optional: export snapshot JSON for batteries (behind a “copy trace” if needed).
- Optional: bilingual copy keys in `ui_copy.json` for Role C Plus strings.
- Deeper alignment: drive one scripted path that calls `formal_submit` if we want `formal_submitted_at` in sim without misleading labels.

## Recommended next sprint

**Formal-submit-aware simulation slice** (still bounded): one explicit “submit this turn” control or scripted final turn so end-of-run summary can validate post-submit lifecycle + intent heads against truth—without building a full test platform.

## Validation performed

- `npm run build` in `ui/` — success.
- Live multi-turn Role C + API not run in this session (no guaranteed local 8001 + `OPENAI_API_KEY` here).
