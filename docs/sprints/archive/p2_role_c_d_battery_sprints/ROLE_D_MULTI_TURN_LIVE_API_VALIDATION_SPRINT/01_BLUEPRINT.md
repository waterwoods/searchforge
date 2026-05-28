# ROLE D MULTI-TURN LIVE API VALIDATION — Blueprint

## Goal

Prove that **Role D** (bounded configurable Add-Car replay) drives **real** multi-turn calls to the same **Add-Car triage** backend path as production Unified Intake, and that **state / missing / next action** remain usable turn-by-turn.

## Non-goals

- UI or simulation redesign  
- LLM / workflow engine changes  
- Large backend refactors  

## Success criteria

- Code inspection shows each simulation step uses `POST /api/inbox/triage` with `soft_route: add_car`, accumulating `conversation_turns`.  
- At least three specified Role D configs are exercised against a **live** API (local `8001` acceptable).  
- Honest split: directly verified vs inferred vs not verified.  

## Scope note — flow explanation

`AddCarFlowExplanation` is wired on **Customer Entry**, not inside `ScenarioReplayTab`. The simulation tab uses a **lighter** right-rail (progress tag, collected/missing, `broker_next_step`, next-owner heuristic). Validation must treat these separately.
