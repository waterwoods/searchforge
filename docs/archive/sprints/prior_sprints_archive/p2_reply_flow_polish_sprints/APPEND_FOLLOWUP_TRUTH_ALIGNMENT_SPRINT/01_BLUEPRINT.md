# APPEND / FOLLOW-UP TRUTH ALIGNMENT — Blueprint

## Sprint goal

Make **Add-Car append / follow-up** behave as a **first-class continuation** of an **already office-visible service record**: same truth model as formal submit + persistence (`formal_submitted_at` immutable, `updated_at` active, post-submit reply families), without redesigning intent NLU or the whole product.

## Why now

Formal-submit alignment, `formal_submitted_at` / `updated_at`, and pre/post-submit reply routing have improved the main path, but append could still (a) surface **pre-submit lifecycle** in triage output, (b) miss **case-level `still_needed_fields`** when the latest bubble is short, weakening intent ceiling checks, and (c) leave **generic flagship `add_car`** phrasing where **supplement / submitted** tone fits better.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md` (§6A Truth → Intent → Reply)
- `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md`
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`

## Scope

**In:** Add-Car only; append API truth context; `triage_for_append` lifecycle; intent merge for `still_needed_fields`; bounded generic→supplement nudge on append; tests + this sprint folder.

**Out:** Full intent anti-collapse, non–Add-Car lanes, CRM/workflow engine, broad UI polish.

## Target outcome

- Append triage exposes **`office_followup`** when the record is office-visible, not **`handoff_pending`**.
- Reply routing receives **persisted gaps + `service_record_append`** so wording stays **post-submit / continuation**.
- Regression tests lock **lifecycle**, **no formal-submit nag** on append (HTTP script), and **intent merge** (unit).
