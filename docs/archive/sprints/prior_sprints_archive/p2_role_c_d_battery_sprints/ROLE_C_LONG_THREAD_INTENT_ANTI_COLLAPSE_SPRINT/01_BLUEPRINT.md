# ROLE C Long-Thread Intent Anti-Collapse — Blueprint

## Purpose

Bounded **issue-harvest** sprint: use long-thread Role C (live HTTP) to see whether Add-Car replies stay **latest-turn-specific** at turns 5–8+, or **collapse** into generic handoff / quote-detail blocks—aligned with Truth → Intent → Reply (`docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`).

## Non-goals

- No product redesign, CRM, or simulation-framework expansion.
- No implementation fixes in this sprint folder (harvest only).

## Success criteria

- Minimum four persona/difficulty mixes run with **persisted-context path** where practical (`--truth-chain`).
- Issues grouped (intent collapse, reply weakness, truth/state, persona, demo clarity).
- Top 3–5 ranked by pilot risk.

## Constraint discovered (2026-03-29 run)

- API `SimulationRoleCCustomerRequest.max_turns` **le=8**; truth-chain inject adds one **customer** turn to transcript history.
- With `max_turns=8`, the **eighth** Role C generation can hit `max_turns reached` once inject has fired.
- Mitigation used: **`ROLE_C_SIMULATION_MAX_TURNS=8`** and **`--max-turns 7`** on the outer battery loop so runs complete while still exercising **Role C turn indices ≥5** after early handoff.
