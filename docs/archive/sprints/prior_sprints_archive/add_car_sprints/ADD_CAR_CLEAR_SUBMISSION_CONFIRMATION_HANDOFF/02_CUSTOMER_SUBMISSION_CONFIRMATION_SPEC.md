# Customer Submission Confirmation Spec

## Purpose

After `handoff_ready`, the Add-Car customer must see a **structured confirmation** of what the rule brain believes it captured—not only the conversational `client_reply_draft`.

## Requirements

1. **Visibility** — Show `quote_ready_status` (when present) and `collected_fields` as customer-facing tags (same humanization as pre-handoff progress card).
2. **Gaps** — If `still_needed_fields` is non-empty at handoff (edge paths), show under “还需办公室可能跟进” or equivalent; do not hide.
3. **Accuracy cue** — Short intro: customer should **verify** snapshot; corrections go through **same-case append**, not a new free-form chat thread.
4. **Human confirmation** — When `human_confirmation_required` is true, show a single calm line: office will **confirm** sensitive items (VIN, driver, materials claims)—no alarmist tone.
5. **Non-chatty** — No extra prompts; copy is informational, not solicitous.

## Copy ownership

- Panel title + intro + verification note + timing: `configs/clients/chen_kui/ui_copy.json` (keys prefixed in sprint implementation).
- Tag labels: existing `CUSTOMER_FIELD_LABELS_ZH` / `QUOTE_READY_STATUS_LABELS` in `UnifiedIntakePage.tsx`.

## Out of scope

Extracting literal VIN/year from text into the snapshot (OCR / NLP display); this sprint uses **field presence** tags only, same as progress card.
