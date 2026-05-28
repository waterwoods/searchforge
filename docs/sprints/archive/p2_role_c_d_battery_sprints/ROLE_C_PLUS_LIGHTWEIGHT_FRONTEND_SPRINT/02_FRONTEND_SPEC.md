# ROLE C PLUS — Frontend spec

## UX model

- **Role C (unchanged):** Scenario card, knobs, thread bubbles, right-rail record summary; 「开始回放」「下一步」「清空」.
- **Role C Plus (additive):**
  - **Entry:** Sub-block under Role C knobs: title “Role C Plus · 轻量多轮”, button **一键跑完（最多 N 轮）** where `N = roleCConfig.maxTurns`.
  - **Readout:** Full-width card below the main 3-column row (only when Role C is selected): “Role C Plus · 逐轮快照与结束报告”.

## Preserved Role C requirement

- Same APIs: `POST /api/inbox/simulation-role-c-customer` then `POST /api/inbox/triage` with `soft_route: add_car`, same `client_id` and conversation history shape as manual flow.
- Auto-run uses shared `loading` so manual buttons are disabled during a run (avoids races); resetting Role C config still clears replay (existing `useEffect`).

## Auto-run behavior

- On click: clear replay, loop at most `maxTurns` times; each iteration = fetch customer line → triage → append to thread; short delay (~72ms) between turns for UI paint.
- Stops on empty customer message, API error, or when customer count reaches `maxTurns`.
- Does not send `formal_submit: true` (same as current simulation triage calls); `formal_submitted_at` in summary is whatever the backend returns for this path.

## Per-turn snapshot (compact)

For each customer/system pair derived from replay:

- Turn index, `lifecycle_status`, `handoff_ready`, `collection_stage`.
- `add_car_turn_intent.intent_family` shown as **intent** (or “—” if absent).
- Trimmed customer line and assistant reply snippet.
- One-line “仍缺” from `still_needed_fields` (truncated list).

No raw JSON dump.

## End-of-run summary

- Total customer turns, final lifecycle, final `handoff_ready`, `formal_submitted_at` note.
- One **overall read** paragraph (honest about simulation not using formal submit API).
- **Warnings:** up to ~4 heuristic flags (repeated reply stems, stuck intent, missing intent late, handoff vs still-needed tension, lifecycle vs `formal_submitted_at`). Labeled as heuristic, not oracle.

## Acceptance criteria

- [x] Original Role C manual flow still present and functional.
- [x] Role C Plus button visible only in Role C context; runs bounded multi-turn auto sequence.
- [x] After any Role C replay (manual or auto), snapshots + end report update from `triageResult` on system turns.
- [x] `TriageResult` typing includes `add_car_turn_intent` for TS safety when present in JSON.
