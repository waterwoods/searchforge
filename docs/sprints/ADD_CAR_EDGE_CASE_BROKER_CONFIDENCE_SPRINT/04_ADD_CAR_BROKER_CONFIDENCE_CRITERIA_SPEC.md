# Add-Car Broker Confidence Criteria Spec

## “This is useful”

- Broker sees **one primary playbook** (add-car quote intake), not a renewal-review template, when the customer is clearly adding a vehicle.
- **Structured fields** (year, model, zip, delivery/driver, contact when applicable) appear consistently in workflow state.

## “This is trustworthy”

- After a **correction**, the conversation summary or context hints reflect “customer corrected,” and vehicle hints prefer **latest** grounded extractors where implemented.
- **Materials-sent** language produces a **verify / office will check** tone instead of arguing with the client.

## “This saves me time”

- No extra synthetic turns when the customer already hit **quote-ready**.
- Side questions (garaging, cheap premium) get a **short** answer without resetting the thread.

## “This is not embarrassing”

- No **premium-renewal** client_prep (“send dec page and bill”) when the user is asking for a **new car quote** in the same message.
- No obviously **wrong vehicle line** for common Chinese phrasing (宝马 / 丰田).

## Observable checks (automated + manual)

- `bash scripts/guardrail_inbox_triage.sh` — PASS.
- `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` — all **strong**.
- Manual: spot-check Unified Intake UI for ACE02-style message (founder list in doc 08).
