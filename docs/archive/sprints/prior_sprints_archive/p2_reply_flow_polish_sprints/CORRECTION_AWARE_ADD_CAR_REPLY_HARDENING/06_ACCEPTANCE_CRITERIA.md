# Acceptance Criteria

## Must pass

- [ ] Guardrail: `bash scripts/guardrail_inbox_triage.sh` → PASS.
- [ ] Multi-turn sims: no `WEAK`; friction only for documented timing quirks.
- [ ] ACE script: `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` → exit 0, no weak.

## Customer copy (ZH)

- [ ] Honda → Tesla correction: reply contains **「我按 2024 Tesla 这台车继续」** (or same meaning with exact vehicle string).
- [ ] X5 → X3 correction: reply and broker-visible vehicle favor **X3** when correction bubble says so.
- [ ] Correction + ZIP same turn: vehicle confirmation + zip acknowledgement + ask moves to **delivery/driver** (not re-ask zip).
- [ ] Correction + materials: handoff copy leads with effective corrected vehicle when applicable.

## Customer copy (EN)

- [ ] Mixed English correction (`meant the 2024 Tesla`): acknowledgement uses full vehicle, not year-only.

## Broker

- [ ] `broker_next_step` still references concrete vehicle when quote-ready; no regression on `collected_fields` / `still_needed_fields`.

## Explicit non-goals

- No new frontend strings beyond what triage returns as `client_reply_draft`.
- No change to add-car slot **requirements** (still year+model or VIN, zip, delivery or driver for handoff).
