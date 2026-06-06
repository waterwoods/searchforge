# RIGHT RAIL CORRECTION / UPDATE VISIBILITY — Final report

## Summary

- Fixed **correction + new fields**: 本回合新记入 no longer suppressed when `follow_up_type === 'correction'`.
- Added **latest-understood lead** before grouped received/missing.
- Added factual **still_needed** set diffs (cleared / newly marked).
- Added **impact** lines (handoff ready transition, gap shrink/grow, correction-only same-gaps, new-fields-only).
- Centralized logic in **`buildAddCarRailTurnModel`** for main rail + post-handoff snapshot.

## Validation

- **Direct:** `npm run build` in `ui/` (pass).
- **Not run:** Browser E2E on Simulation / live triage; guardrail script unchanged (no backend edits).

## Follow-ups (2–3)

1. Backend **explicit `updated_fields` / `corrected_fields`** when safe, for precise “哪几项理解变了” without guessing.
2. **Lifecycle / step** impact when `lifecycle_status` changes without `handoff_ready` or still-needed moving.
3. **broker_next_step** delta snippet in rail when it changes turn-over-turn (short, optional).
