# Correction-Aware Add-Car Reply Blueprint

## Purpose

When a customer corrects **which vehicle** they mean (e.g. Honda → Tesla, X5 → X3), the **customer-facing reply** must show that the office understood the **effective vehicle**, then ask only for the **next missing slot** (zip, delivery/driver, etc.). Internal field extraction alone is insufficient for trust.

## In-scope

- Add-car / new quote flows only (`_is_add_vehicle_request`).
- Rule-based and fast-path triage in `services/fiqa_api/inbox_triage/triage.py`.
- Broker summaries and `broker_next_step` that already use `_extract_add_car_vehicle_concrete`.

## Out-of-scope

- UI, OCR, carrier APIs, non–add-car intents, large refactors.

## Target experience

| Weak | Strong |
|------|--------|
| 「好的，2024的。先把邮编发我…」 | 「好的，我按 2024 Tesla 这台车继续。先把邮编发我…」 |

## Loops

1. **Detect** vehicle-correction signal (last customer bubble).
2. **Resolve** effective vehicle (correction bubble wins over earlier mentions).
3. **Acknowledge** with correction template (ZH/EN).
4. **Ask** next missing field via existing add-car rules (`get_add_car_rules`).
5. **Handoff** when quote-ready; if correction + materials in same turn, prefix handoff with effective vehicle.

## References

- Code: `_is_add_car_vehicle_correction_signal`, `_extract_add_car_vehicle_concrete`, `_get_add_car_acknowledgement`, `triage_conversation` handoff prefix.
- Simulations: `ACE13`–`ACE16` in `configs/customer_entry_multi_turn_simulations.json`.
