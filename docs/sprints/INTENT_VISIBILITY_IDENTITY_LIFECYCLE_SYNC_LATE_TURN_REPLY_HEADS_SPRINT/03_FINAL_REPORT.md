# Final report — INTENT VISIBILITY + IDENTITY/LIFECYCLE SYNC + LATE-TURN REPLY HEADS

## What was implemented

1. **`add_car_turn_intent` on persist/append** — `case_store._validate_triage_result` now normalizes and retains `add_car_turn_intent` (including optional `phrase_storage_key`). `append_follow_up_message` writes the latest intent snapshot onto the case.
2. **API intent payload** — `phrase_storage_key` added to triage’s `add_car_turn_intent` for template-key observability.
3. **Record + turn identity sync** — Routes pass `record_contact_name` / `record_contact_phone` into `reply_truth_context`; triage merges **last-turn** contact extraction, expands **姓名/名字/手机** patterns, and reconciles `still_needed_fields` + contact-gap tail with record/thread contact.
4. **Lifecycle** — Post–formal-submit continuation turns (no new submit, not handoff) use **`office_followup`** instead of regressing to `collecting` when the case is already office-visible.
5. **Late-turn reply heads** — Post-submit Add-Car **handoff** replies get a short **intent-specific opener** (ZH/EN) before the template body for timeline, quote-detail, office-receipt, materials-claim, supplement, and correction intents.

## What improved

- Batteries and curl against **persist=true** responses can finally see **intent + phrase key** alongside the draft reply.
- **Name/phone** gaps are less likely to contradict explicit customer text or saved case contact.
- Late post-submit answers are **easier to tell apart** by their first clause.

## What remains weak

- **Non-handoff** post-submit replies (collection-style `next_best_question` path) do not get intent openers — only the handoff reply path.
- Contact extraction is still **regex-bounded**; unusual formats may still miss.
- `phrase_storage_key` duplicates information already inferable from pack + base key but is **intentional** for debugging.

## Recommended next sprint

- Thread `add_car_turn_intent` into **Workbench / simulation UI** columns for operator-visible regression.
- Optional: align **non-handoff** post-submit customer-visible drafts with the same intent opener rule where safe.
