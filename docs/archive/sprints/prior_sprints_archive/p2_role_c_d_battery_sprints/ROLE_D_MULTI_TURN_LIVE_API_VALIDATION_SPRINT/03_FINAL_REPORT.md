# Final report — ROLE D MULTI-TURN LIVE API VALIDATION

## Verdict

**Role D does call the live triage path every turn** (same endpoint and payload family as `triageMessage` in the UI). Multi-turn responses **do change** (`triage_path`, fields, drafts). There are **coherence gaps** (year correction vs extracted state; post-handoff static broker copy) that limit “feels like a real customer” polish.

## Code — simulation → API

- `ScenarioReplayTab` → `triageMessage(..., 'add_car', undefined, clientId)` → `POST /api/inbox/triage` with `conversation_turns` built from prior replay. **Verified by read.**

## Live run summary (D1–D3)

- **D1:** Progression from `need_more` → `almost_ready` → `quote_ready` + `handoff_ready` by turn 4; later turns use mix of `fast` / `llm`. **Issue:** after customer corrects to **2024** CR-V, system draft/collected behavior still aligned with **2023** in mid-thread (backend extraction).  
- **D2:** Similar progression; name inferred early (`name` in collected turn 1). Post-handoff turns 5–7: **collected / still_needed unchanged**; drafts often identical — feels **scripted**.  
- **D3:** Turn 1 `issue_category: missing_document` + `llm` (materials-first note); then Add-car fields fill; VIN appears in collected after turn 5. Coherent enough; category skew is visible.

## Flow explanation

- **Customer Entry:** `AddCarFlowExplanation` uses `still_needed_fields` — not validated in browser this sprint.  
- **Simulation tab:** Uses step tag + missing tags + `broker_next_step` only — **no** `AddCarFlowExplanation` component.

## Broker demo readiness

Useful for **proving the pipe** and seeing structured fields move; weaker for **emotional realism** after handoff when replies repeat and structured state stops updating.

## Recommended next sprint (founder)

Balance: short **record summary + flow explainer on the right** for persisted/handoff context; parallel **triage** tuning for correction absorption — not more Role D templates first.
