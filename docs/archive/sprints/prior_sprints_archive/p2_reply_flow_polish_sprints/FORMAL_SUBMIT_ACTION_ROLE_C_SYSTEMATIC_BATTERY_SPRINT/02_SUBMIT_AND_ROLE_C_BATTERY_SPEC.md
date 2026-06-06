# Formal submit target + Role C battery spec

## Formal submit action (product target)

| Phase | Meaning |
|--------|---------|
| Still collecting | Office should **not** treat the thread as formally submitted; primary action is **补充** / structured fields. |
| Ready to submit | `handoff_pending`: info sufficient; main action is **正式提交办公室（送达处理队列）**; user may still add a remark in the input. |
| Formally submitted | Office has the record for handling; user may **append** on the same record; **not** “quoted” or “fully bound.” |

**UX principles:** strong CTA label, short explainer (Alert + flow card + right rail), **no** default heavy “are you sure” modal; optional **one-line subline** under the button for reassurance.

## Implementation notes (this sprint)

- **Empty input + handoff_pending:** UI sends a configurable canonical one-line message (`portal_handoff_pending_empty_submit_line`) so `POST /api/inbox/triage` always receives non-empty `text` while the customer can still “click only.”
- **CTA label** extended with **（送达处理队列）** to reduce ambiguity with casual “提交.”

## Role C battery: `handoff_loop` preset

| Id | Persona | Difficulty | Turns | Intent |
|----|---------|------------|-------|--------|
| C1 | `price_sensitive` | `realistic` | 6 | Price/deductible; ask if office “officially” has it + timeline. |
| C2 | `price_sensitive` | `tough` | 8 | Picky; sensitive to 正式提交 vs 办公室接手 wording. |
| C3 | `elderly` | `tough` | 8 | Oral style; worry office didn’t receive; repeat confirmation. |
| C4 | `family_vehicle` | `realistic` | 6 | Household drivers; who owns next step after ready. |
| C5 | `materials_first` | `realistic` | 6 | WeChat materials sent; ask receive vs need formal submit. |

Run:

`PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py --preset handoff_loop --client-id chen_kui`

Requires live `fiqa_api`, `OPENAI_API_KEY`, base URL (default `http://127.0.0.1:8001`).

## Issue harvest categories

- **A. Formal submit clarity** — user can’t tell when to submit; office seems to have the case too early.
- **B. Handoff truth** — reply over-claims; canned closure; `still_needed` vs visible copy.
- **C. State / lifecycle** — collecting vs `handoff_pending` blurry; post-submit vs office follow-up; right rail drift.
- **D. Persona realism** — persona/difficulty too weak.
- **E. Demo clarity** — broker confusion; right rail doesn’t explain latest turn.

## Acceptance criteria

- [x] Client pack copy distinguishes **补充 / 正式提交 / 办公室接手** in bounded strings (no modal).
- [x] Empty formal submit path works on customer portal when `lifecycle_status === 'handoff_pending'`.
- [x] Battery script supports `handoff_loop` and logs `lifecycle_status` + `handoff_ready` + `case_id` per turn.
- [x] `bash scripts/guardrail_inbox_triage.sh` passes (rule/scenario regression).
