# INTENT VISIBILITY + IDENTITY/LIFECYCLE SYNC + LATE-TURN REPLY HEADS — Blueprint

## Sprint goal

Make long-thread Add-Car behavior **more inspectable and more stable** by:

1. Exposing resolved intent (and template routing) on the **live API and persisted case** path.
2. Tightening **identity / service-record contact** alignment with `still_needed_fields` and continuation semantics.
3. Adding bounded **intent-specific reply openers** for post-submit late turns so distinct jobs do not read as one generic office block.

## Why now

Recent Role C / long-thread batteries showed: `add_car_turn_intent` missing from traces after formal persist, `still_needed_fields` staying out of sync with explicit name/phone or saved case contact, and late-turn replies collapsing to the same office-phase tone. The next increment is **observability and trust**, not new surface area.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`

## Scope

**In scope:** Add-Car only; API/case intent payload; bounded identity + lifecycle sync; post-submit late-turn reply heads; regression tests; this sprint folder.

**Out of scope:** NLU rewrite, Role C Plus UI, CRM/workflow engine, non–Add-Car lanes, large doc sets.

## Target outcome

- Reviewers can see **what intent the system resolved** and **which phrase key** was used on the same JSON as `client_reply_draft`.
- **Name/phone** on the thread or on the persisted record reduces contradictory `still_needed_fields` where appropriate.
- **Post-submit** replies for timeline vs quote-detail vs receipt vs materials vs supplement vs correction **start with different stems** while staying truth-safe.
