# Fix spec — two issues

## Issue 1 — `handoff_ready` vs contact gap

**Problem:** Quote-ready structured state could list `name`/`phone` in `still_needed_fields` while `handoff_ready` stayed true, and post-submit runs could keep chat-extraction gaps in `still_needed` even after office-visible submit.

**Bounded fixes**

1. **Turn 4+ pre-submit gate:** If Add-Car `handoff`, quote path still missing extracted name/phone in-thread, and **no** office submit context, set `handoff_ready=False`, `lifecycle_status=collecting`, and a short `next_best_question` nudge. Turns 1–3 stay compatible with MATURE_INTAKE (slot completion + first-turn full quote).
2. **Post-submit `still_needed`:** When `reply_truth_context` carries `formal_submitted_at`, drop `name`/`phone` from `still_needed_fields` (service record is authoritative for identity after submit).
3. **Battery oracle:** `TRUTH_HANDOFF_READY_CONTACT_GAP` only for **pre-submit** turns and **turn ≥ 4** (aligned with gate).

## Issue 2 — Late-turn repeated reply blocks

**Problem:** Same post-submit stem across many turns (same pack line + same fallback).

**Bounded fixes**

1. **Engine:** `_POST_SUBMIT_ADD_CAR_FALLBACK_POOLS` — rotate variants by turn index via `_post_submit_add_car_fallback_line(..., rot_idx=turn)`.
2. **Pack:** `use_alt_post_submit` on even turns (turn ≥ 3) when `zh_alt`/`en_alt` exist on the resolved `*_submitted` key.
3. **Chen Kui pack:** Add `zh_alt`/`en_alt` for key `*_submitted` families used in late turns.

## Recheck expectations

- Role C 5-turn + `--truth-chain`, personas: price_sensitive/tough, family_vehicle/realistic, materials_first/realistic.
- **REPLY_REPEATED_BLOCK** should stay **absent** in normal runs.
- **TRUTH_HANDOFF_READY_CONTACT_GAP** may still appear on **pre-submit** turn 4+ if the model keeps `handoff_ready` true before gate conditions match — monitor; post-submit should not spike false positives.

## Acceptance criteria

- `bash scripts/guardrail_inbox_triage.sh` passes.
- Short Role C recheck completes; report captures warning codes and qualitative notes.
