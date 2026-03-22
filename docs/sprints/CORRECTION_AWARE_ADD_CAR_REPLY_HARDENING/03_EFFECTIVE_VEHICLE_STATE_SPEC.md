# Effective Vehicle State Spec

## Definition

**Effective vehicle** is the office-facing string (e.g. `2024 BMW X3`, `2024 Tesla`) used in:

- Customer acknowledgement / correction lead-in.
- `broker_next_step` when quoting (“Run quote for …”).
- Conversation summary hints via `_extract_add_car_vehicle_concrete`.

## Resolution rules

1. Parse **customer-only** lines from merged `[客户] …` blocks.
2. If the **last** customer message matches `_is_add_car_vehicle_correction_signal`:
   - Resolve **model/trim cues from that bubble only** (`_add_car_vehicle_concrete_from_scope(last_seg, year_pool=full_customer_text)`).
   - **Year**: prefer years appearing in the correction bubble; if none, use latest year in the full customer thread.
3. Otherwise resolve from the **full** merged customer text (legacy behavior, with last-year wins).

## BMW X5 / X3 disambiguation

When multiple `X3` / `X5` substrings appear across the thread, the **last** `[xX][35]` match inside the **active scope** (correction bubble or full text) wins — fixes “thread still says X5” after “不是X5 是X3”.

## Plain Tesla

`Tesla` without Model Y/3 is a valid concrete make for replies and summaries when year is present.

## Broker correctness

Structured `collected_fields` / `still_needed_fields` continue to use `_extract_add_car_fields` on merged text; effective vehicle string is **presentation + broker narrative**, not a replacement for slot validation.
