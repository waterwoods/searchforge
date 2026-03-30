# Role C — Control spec (v1)

## Current weakness (pre-sprint)

- Logic lived next to the route; **reuse for scripts** was implicit (“copy the request shape”) rather than a **named service boundary**.  
- **`client_id`** was accepted by the API but **not** passed into the LLM context (minor pack-alignment gap).

## Target knob model (2–3 core + optional note)

| Knob | API / UI field | Values (examples) |
|------|----------------|-------------------|
| **Persona** | `persona_id` | `price_sensitive`, `elderly`, `materials_first`, `family_vehicle`, `fragmented`, `mixed_zh_en` |
| **Difficulty** | `difficulty` | `smooth`, `realistic`, `tough` |
| **Max turns** | `max_turns` | **3–8** (integer cap on **customer** lines) |
| **Optional note** | `optional_note` | Short operator hint (≤ ~200 chars); **not** a fourth “major” subsystem |

## Frontend + backend dual-use

| Surface | Mechanism |
|---------|-----------|
| **Frontend** | `POST /api/inbox/simulation-role-c-customer` then `POST /api/inbox/triage` with `soft_route: add_car` (unchanged flow). |
| **Backend / CI** | Same HTTP endpoints via `scripts/run_role_c_add_car_battery.py`, **or** in-process `next_role_c_customer_line()` from `role_c_simulation_service.py`. |

## Model / bounds

- Default model: **`gpt-4o-mini`** via `ROLE_C_SIMULATION_MODEL` or `LLM_MODEL` env, else `gpt-4o-mini` (see `role_c_customer_llm.py`).  
- Prompt rules: **single next customer message**, Add-Car only, temperature/mtoken caps unchanged unless intentionally revised.

## Acceptance criteria

1. **One Python entry** for “next Role C line” used by the route (`next_role_c_customer_line`).  
2. **Knobs remain** persona + difficulty + max_turns (+ optional note).  
3. **Battery script** can run a **small preset** (`--preset smoke`) or a **single** variant against a running API.  
4. **No** new free-form chat mode; **no** expansion beyond Add-Car simulation.

## Bounded battery design (future-friendly, not huge)

**Preset `smoke` (built-in):** two short runs (4 customer turns each)—fragmented/realistic and price_sensitive/tough—to spot reply/state/gap regressions cheaply.

**Suggested expansion (documentation only for now):** a 3×3 matrix (3 personas × 3 difficulties) at `max_turns=6` as an occasional manual run; keep **JSONL** output for diffing traces.
