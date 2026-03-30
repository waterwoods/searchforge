# Role C — Product spec (1.0)

## Purpose

Role C answers: **What happens when a more realistic, variable customer interacts with Add-Car across multiple turns?**  
It is **not** a chat product; it is a **simulation asset** tied to real triage semantics.

## Difference from A / B / D

| Role | Nature |
|------|--------|
| A / B | Fixed scripted turns |
| D | Configurable **scripted** turns + keyword branch overlays (deterministic) |
| **C** | **LLM-generated** customer lines per turn, bounded by persona, difficulty, max turns, and system instructions |

## Bounded control model (1.0)

1. **Persona** (one of): 价格敏感、老年、材料先发、家庭车辆、信息很碎、中英混说.
2. **Optional one-line note** — short operator hint injected into LLM context (not user chat).
3. **Difficulty**: 顺畅 / 真实 / 刁钻 — adjusts style constraints in the system prompt.
4. **Max customer turns**: 4, 6, or 8 — hard cap; UI and API enforce.

## LLM behavior expectations

- North-American-Chinese Add-Car texting style when appropriate.
- Fragmented info, typos/corrections, price sensitivity, materials-already-sent, household mentions, mixed zh/en — **when consistent with persona/difficulty**.
- **Stay on Add-Car**; no unrelated topics; no meta role-play.

## Stopping condition

- After **max_turns** customer messages, **下一步** is disabled (same pattern as running out of scripted lines).

## Acceptance criteria

1. Simulation tab shows **角色 C** as **受控 LLM 客户** with clear labeling.
2. Each step: **LLM customer line** → **real triage** → right rail updates from **triage result**.
3. Without backend API key, user gets an **honest error** (503-style messaging), not fake text.
4. No infinite chat; controls remain **small and demo-safe**.
