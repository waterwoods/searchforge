# Founder Inspection Notes

## What to click / run

1. `bash scripts/guardrail_inbox_triage.sh` — must end with `Guardrail: PASS`.
2. `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_case_boundary_battery.py --verbose` — spot-check drafts.

## What changed visibly

- **Broker:** First line of `broker_next_step` / `conversation_summary` may flag boundary on **append**.
- **Customer copy** on append may switch to **continuity + handoff** wording when a new domain is detected (instead of looking like a fresh add-car ask).

## What did not change

- Pre-case `triage_conversation` handoff timing, add-car field extraction, mixed-intent secondary note logic (still last-bubble biased).
- No new mandatory fields in core triage schema beyond optional `case_boundary`.

## Honest limits

- **Prior domain** is coarse; threads that never mention add-car explicitly may stay `generic`.
- **Borderline** relies on broker confirmation—by design.
- With **LLM enabled**, base triage may differ; boundary layer still applies on append after `triage_conversation`.
