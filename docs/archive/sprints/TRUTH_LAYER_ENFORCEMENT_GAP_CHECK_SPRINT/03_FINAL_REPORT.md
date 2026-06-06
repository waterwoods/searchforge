# TRUTH-LAYER ENFORCEMENT + GAP CHECK — Final report

## What was checked

- `02_TWO_LAYER_STANDARD_SPEC.md` against Add-Car: reply vs `handoff_ready` / `handoff_pending` / formal submit, office-receipt forbidden overreach, right-rail step truth.
- Files: `triage.py` handoff assembly, `chen_kui` + `socal_precision` `handoff_phrases.json`, `AddCarRecordSummaryRail.tsx` formal-complete helper, guardrail batteries that lock client-visible copy.

## What was fixed

1. **Reply layer (client packs + engine fallbacks):** Add-Car flagship and stitched suffixes (doc clarification, coverage combo) no longer claim office receipt or durable queue placement before **formal submit**; they state record capture + **入口正式提交** + queue **after** submit.
2. **UI truth gate:** `isFormalSubmissionToOfficeComplete` now requires `formal_submitted_at` or `handed_off` / `office_followup` — **not** `case_id` alone — so the right rail does not show “办公室已收到…” on ambiguous shapes.
3. **Regression batteries:** `residual_copy_ab_scenario_battery.json` and `small_batch_ab_scenario_battery.json` oracles updated to assert the new truth-aligned phrases and forbid old “资料已到办公室” style claims.

## What still violates or weakens the standard (next)

- **`triage_conversation` lifecycle:** Still emits `handoff_pending` for every rule-based handoff; post–formal-submit **re-triage** in the same session does not promote lifecycle in-engine (rely on persisted case merge / UI). Worth a bounded follow-up if mixed API shapes appear in the wild.
- **Talk-to-agent / other lanes:** `customer_requested_human` and non–Add-Car handoffs were not fully re-audited for the same office-receipt bar.
- **`handoff_ready` vs `still_needed_fields`:** No new structural gate in this sprint beyond existing contact-gap tail; re-check if any path sets handoff with missing vehicle keys.
- **Post–formal-submit “strong” receipt copy:** Optional future: separate **post-submit** phrase family when API merges `formal_submitted_at` into triage for warmer confirmation (still truth-locked).

## Validation

- `bash scripts/guardrail_inbox_triage.sh` — **PASS** (full pipeline including residual + small-batch A/B).

## Recommended next sprint

**Formal-submit-aware reply routing:** pass persisted `formal_submitted_at` / office-queue state into triage (or post-process in route) so post-submit follow-ups can use warmer **receipt-confirmed** phrasing without weakening pre-submit enforcement.
