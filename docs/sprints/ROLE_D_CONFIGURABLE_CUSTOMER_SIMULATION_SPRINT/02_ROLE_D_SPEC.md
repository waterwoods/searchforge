# Role D — Specification (v1.0)

## Purpose

Role D simulates a **more realistic, messy Add-Car customer** than fixed A/B scripts, while staying **bounded and replayable**. It exists to:

1. **Reduce testing pain** — fewer manual multi-turn threads; named persona + difficulty presets.
2. **Reduce demo pain** — brokers can map a template + one sentence to someone they know.

## Configuration model (three inputs)

| Input | Role |
|-------|------|
| **Base persona template** | Chooses a scripted “arc” (price-sensitive, materials-first, fragmented info, household, flip-flop, zh/en mix, elderly). |
| **One-line custom description** | Optional; merged into the **first customer turn** as `对了，{note}` so it shapes tone without replacing the template. |
| **Difficulty / realism** | `顺畅` (~3 turns), `真实` (~5), `刁钻` (~7–8); controls fragmentation, corrections, and combined pressures (VIN delay, spouse, materials, price). |

**Defaults:** template `价格敏感型`, difficulty `真实`, empty custom note.

## Bounded behavior model

- All customer text comes from **fixed per-template, per-difficulty turn lists** in `ui/src/components/simulation/roleDReplay.ts`.
- No runtime LLM generates customer lines in v1.
- Content stays **Add-Car–centered** (vehicle, timing, drivers, zip, VIN/materials, price hints).

## Relation to A / B / C

| Role | Nature |
|------|--------|
| A | Short happy path, fixed JSON. |
| B | Longer fixed high-risk script, JSON. |
| C | Placeholder for future **controlled** LLM variation (outline). |
| **D** | **Configurable deterministic** messiness — more variety than A/B without open-ended chat. |

## Acceptance criteria

- [x] Role D appears as a **scenario card** (角色 D) in the simulation list.
- [x] User can set **template + optional note + difficulty** with a **small** panel (no large form).
- [x] Changing configuration **clears** in-progress replay and updates turn count / subtitles.
- [x] Replay uses the same **`triageMessage`** path and soft route `add_car` as A/B.
- [x] Right column continues to show step, state, collected/missing fields, next action, owner, case id when returned.
- [ ] Future: optional seed-based variation inside the same bounds; optional alignment with Role C LLM layer.
