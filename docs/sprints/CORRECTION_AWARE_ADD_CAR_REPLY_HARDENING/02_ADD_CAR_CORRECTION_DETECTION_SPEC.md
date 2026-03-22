# Add-Car Correction Detection Spec

## Goal

Identify turns where the customer is correcting **which car** (make/model/trim/year), not e.g. driver-only fixes or unrelated “不是”.

## Function

`_is_add_car_vehicle_correction_signal(text: str) -> bool`

## Positive signals (examples)

- Chinese: `不是…是…` within ~40 chars; `不是这个` / `不是这辆` / `不是那辆` / `另一辆` / `不是这台车`.
- English: `not that one`, `wrong car`, `wrong vehicle`, `meant the`, `meant a`.
- English clause: `i meant` / `actually` … `20xx` / `tesla` / `bmw` / etc.
- `说错了` **only if** the same bubble also contains a vehicle token (year, 特斯拉, X3/X5, tesla, honda, …) — excludes driver-only “说错了主要是我老婆开”.

## Non-goals

- Do not treat every substring `不是` as vehicle correction (e.g. unrelated negation).
- Driver-only corrections remain normal acknowledgement / handoff without vehicle template.

## Broker alignment

`follow_up_type` may still be `correction` from `_derive_follow_up_type` for broader product use; vehicle-specific behavior uses `_is_add_car_vehicle_correction_signal` on the **last customer message**.
