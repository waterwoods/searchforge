# Regression pack + battery spec

## A. In-process regression (`scripts/run_pre_post_submit_reply_regression.py`)

Runs with `LLM_GENERATION_ENABLED=0`. Oracles (aligned with `02_TWO_LAYER_STANDARD_SPEC.md` §D):

| Check | Condition | Failure |
|-------|-----------|---------|
| Pre-submit office receipt | `reply_truth_context=None`, full Add-Car handoff fixture | Draft contains forbidden substrings: 已到办公室, 已进办公室队列, 办公室已正式收到记录, 资料已到办公室, 已交办公室, 办公室已收到 |
| Post-submit nag | `formal_submitted_at` + `lifecycle_status=handed_off`, follow-up turn | Draft contains portal formal-submit nag lines (e.g. 请在入口完成「正式提交办公室」) |
| Append + truth | `triage_for_append` with `reply_truth_context` set | Same nag lines forbidden |
| Submit-turn smoke | `formal_submit_this_turn=True` | Sanity pass (shape) |

**Guardrail:** `scripts/guardrail_inbox_triage.sh` step `[3c]`.

## B. Role C limits

- `ROLE_C_MAX_TURNS_MAX = 12` in `role_c_simulation_service.py` — **10** Role C iterations + **headroom** for one script-injected formal-submit customer line in the transcript (Role C counts all `customer` rows).
- `SimulationRoleCCustomerRequest.max_turns` Pydantic `le=12` in `routes/inbox_triage.py`.

## C. Battery script

- **Preset:** `sprint_10_turn` — five variants (C1–C5); C5 optional for time.
- **`--truth-chain`:** After a `handoff_ready` triage result, script sends one **formal-submit persist** turn (`_FORMAL_SUBMIT_INJECT_ZH`), then passes returned **`case_id`** on subsequent triage calls so `reply_truth_context` loads from the case store.
- **Role C API `max_turns`:** `min(ROLE_C_MAX_TURNS_MAX, user_max_turns + 2)` when `truth_chain` is on.

## D. Live run matrix (minimum)

| Case | Persona | Difficulty | Turns |
|------|---------|------------|-------|
| C1 | price_sensitive | tough | 10 |
| C2 | elderly | tough | 10 |
| C3 | family_vehicle | realistic | 10 |
| C4 | materials_first | realistic | 10 |

Optional: C5 `fragmented` / `tough` / 10.

## E. What to watch (issue harvest)

- Pre/post-submit wording vs persisted truth
- Repetition vs latest customer question (late turns)
- `lifecycle_status` / `handoff_ready` / `still_needed_fields` coherence
- Contact-gap tails when name/phone already present
