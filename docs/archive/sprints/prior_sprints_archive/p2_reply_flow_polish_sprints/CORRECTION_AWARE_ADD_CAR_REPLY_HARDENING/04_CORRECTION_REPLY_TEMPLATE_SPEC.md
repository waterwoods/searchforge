# Correction Reply Template Spec

## When to use

- Add-car flow active.
- Last customer message: `_is_add_car_vehicle_correction_signal` is true.
- `_extract_add_car_vehicle_concrete(merged)` is non-empty.

## Chinese (primary)

`好的，我按 {vehicle} 这台车继续。`

Optional same-turn zip acknowledgement (if zip appears in last message and field detected):

` … 邮编{zip}也收到了。`

Then append the **existing** next ask from add-car rules (zip / delivery / driver / etc.) — no duplicate asks for already-provided slots.

## English

`Got it, we'll proceed with the {vehicle}.`

Optional:

` I have zip {zip} as well.`

## Non-correction improvement

When year **and** model slots are filled but the message is **not** a vehicle correction, prefer **full concrete** (`{year} {make…}`) over **year-only** acknowledgement — removes thin “2024年的” when make is known.

## Handoff

If the turn hands off and the last message is a vehicle correction, prefix the standard add-car / materials-sent handoff with the Chinese or English correction lead-in **once** (avoid duplicate if already present).
