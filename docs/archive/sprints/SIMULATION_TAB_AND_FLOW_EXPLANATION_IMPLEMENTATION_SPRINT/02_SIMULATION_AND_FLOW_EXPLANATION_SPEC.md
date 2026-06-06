# Simulation tab + flow explanation — 1.0 spec

## Tab purpose

- **场景仿真** is a **scenario asset surface**: scripted, replayable Add-Car paths that use the same triage API semantics as live intake (`POST` via `triageMessage`, `soft_route: add_car`).
- **Not** a toy chat; **not** a full multi-intent simulator (the legacy drawer may be removed from the main path in favor of this tab).

## 1.0 layout

| Column | Content |
|--------|---------|
| Left | Named scenario cards: role **A / B / C**, title, subtitle, risk tag, turn count |
| Center | Customer + system bubbles; **开始回放 / 重新回放**, **下一步**, **清空** |
| Right | **服务记录与进度（主视图）**: flow step, collection state, case id (if any), collected / missing fields, broker next step, next owner |

## A / B / C roles

- **A — 标准加车（顺畅）**: 3 customer turns, happy-path style completion toward handoff.
- **B — 高风险加车**: ~5 turns; spouse/household wording, “already sent” material, garaging/VIN follow-up, brief reshopping tangent, then refocus on primary add-car.
- **C — 受控变式（占位）**: Single scripted turn + in-UI note that **controlled variation** (rules / seeds / bounded LLM) is a **next sprint**; structure is valid for QA of the shell.

## Replay behavior

- Each **下一步** sends the next scripted customer line with accumulated `conversation_turns` from prior replay only (no stale closure after **重新回放** — explicit `priorReplay` base).
- **persist_case** remains `false` for simulation calls (same as legacy assistant); case id may still appear when the API creates ephemeral/demo records — UI labels this honestly.

## Flow explanation rules

**Pre-handoff (Add-Car, step 2)**

- Shown when: active Add-Car thread, not `handoff_ready`, at least one system turn.
- Explains: step 1 done (record anchored), now step 2, optional **仍待补** list, owner (customer + system), prose CTAs (continue in same record — not a modal).

**Post-handoff (Add-Car, step 3)**

- Shown at top of green closure card when Add-Car handoff.
- Explains: step 2 done → record ready for office, now step 3, optional residual gaps, office-owned next action, prose CTAs (append vs new issue).

Copy is **business-process** tone; avoids generic “Anything else?” filler.

## Acceptance criteria

1. Third tab **场景仿真** is visible next to customer / office tabs.
2. A and B replay multi-turn; right panel updates with last system `triageResult`.
3. C shows placeholder note and at least one replay turn.
4. Add-Car customer entry shows flow explanation block mid-flow and at handoff.
5. `cd ui && npm run build` succeeds.
