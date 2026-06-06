# SIMULATION TAB + FLOW EXPLANATION — Final report

## Implemented

- **Third tab** `场景仿真` in `UnifiedIntakePage` with `ScenarioReplayTab` (3-column layout).
- **Scenario assets** in `ui/src/config/add_car_scenario_replay.json`: **A**, **B**, **C** (C = placeholder note + 1 turn).
- **Replay controls**: 开始回放 / 重新回放 (resets via `runNextTurn([])`), 下一步, 清空; `soft_route: add_car` on all simulation turns.
- **Right column** surfaces step tag, collection/handoff tags, case id, collected/missing (ZH labels), broker next step, inferred next owner.
- **Flow explanation** via `AddCarFlowExplanation`: pre-handoff card during Add-Car step 2; post-handoff card at top of closure UI for Add-Car handoff.
- **Copy / config**: new `UiCopy` keys in `clientConfig.ts` (defaults) + Chen Kui `ui_copy.json` tab labels.
- **Customer entry** hero link opens simulation tab (`onOpenScenarioSimulation`); legacy **SimulationAssistant** drawer removed from this page to avoid duplicate primary entry.

## Partial / honest limits

- **C** is explicitly a **placeholder** for controlled variation; no live A/B variant engine yet.
- Simulation uses **`persist_case: false`**; persistence of `case_id` depends on API behavior — UI states when id may be absent.
- **Pre-handoff explanation** stays visible for the whole of step 2 (can feel repetitive vs a single “transition” flash); acceptable for 1.0 clarity.

## Future work

- Wire **C** to a bounded variation mechanism (config seed, rule flags, or guarded LLM).
- Optional: restore **multi-intent** scenarios in a secondary drawer or “高级测试” link for QA only.
- Tighten pre-handoff explanation to **first transition into step 2 only** if user testing finds the persistent card too heavy.

## Recommended next sprint

**Controlled variation for scenario C** + optional **export last replay as JSON** for regression fixtures.
