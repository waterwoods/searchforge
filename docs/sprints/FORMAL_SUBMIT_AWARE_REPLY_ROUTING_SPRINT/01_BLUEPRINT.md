# FORMAL-SUBMIT–AWARE REPLY ROUTING — Blueprint

## Sprint goal

Make **Add-Car customer-facing replies** explicitly depend on **formal submit / persisted truth**: distinct phrasing for pre-submit handoff, the formal-submit moment, and post-submit follow-up—without the reply layer outrunning structured truth.

## Why now

Pre-submit trust leaks (early “office receipt”) were addressed. The remaining gap: after **formal submit** or when **appending to an office-visible case**, replies still sounded like “please submit” or generic handoff. **Truth layer** already exposes `formal_submitted_at`, `lifecycle_status`, and append semantics; **reply routing** did not consume them.

## Read-first alignment

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`
- `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md`

## Scope

**In scope:** Add-Car only; `triage_conversation` / append path; client-pack `handoff_phrases` (+ stitched) for pre vs post-submit families; optional `case_id` on `POST /api/inbox/triage`; customer UI passing `case_id` when continuing a saved record; bounded validation via `scripts/guardrail_inbox_triage.sh`.

**Out of scope:** CRM/workflow engine, non–Add-Car expansion, broad NLU rewrite, generic UI polish.

## Target outcome

- Reply selection uses an explicit **reply truth context** (`formal_submitted_at`, `lifecycle_status`, `formal_submit_this_turn`).
- **Post-submit** Add-Car families (default, supplement, timeline, quote detail, correction) and key stitched paths use **`_submitted`** pack keys or engine fallbacks—never “office has it” without that context.
