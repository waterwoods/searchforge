# ROLE C CONTROL KNOBS + BATTERY DESIGN — Final report

## Implemented

- **`role_c_simulation_service.py`**: `next_role_c_customer_line()`, transcript normalization, `RoleCMaxTurnsReached`, re-exports `VALID_PERSONAS` / `VALID_DIFFICULTIES`, turn bounds **3–8**.  
- **Route** `simulation_role_c_customer` now delegates to that service (same HTTP contract).  
- **`generate_role_c_customer_turn`**: optional **`client_pack_id`** hint in the system prompt when `client_id` is sent.  
- **`scripts/run_role_c_add_car_battery.py`**: HTTP multi-turn runner; **`--preset smoke`** for two short variants.  
- **UI**: short copy under Role C panel + **`roleCReplay.ts`** comment linking to Python knobs.

## Reusability

Role C is **more clearly a service**: scripts and the API share **`next_role_c_customer_line`**; the battery script uses the **same endpoints** as the simulation tab.

## Partial / follow-ups

- No automated CI wiring for the battery (runner needs live server + API key on backend).  
- Persona lists remain **duplicated** in TS and Python (acceptable v1; could add a tiny shared JSON later if drift hurts).  
- Larger matrix runs are **documented**, not scheduled.

## Recommended next sprint

Wire **`--preset smoke`** into a **manual or nightly** job when API + key are available; optionally persist **JSONL** artifacts for regression diffing.
