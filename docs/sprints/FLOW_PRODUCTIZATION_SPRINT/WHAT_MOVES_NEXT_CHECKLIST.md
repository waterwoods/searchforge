# What Should Move Next — Checklist

Use this during PR planning; details live in `EXTERNALIZATION_PRIORITY_SPEC.md`.

## Immediate (before second broker)

- [ ] **Reply overrides:** load `configs/clients/{CLIENT_ID}/reply_overrides.json` (remove hardcoded `chen_kui` in `get_reply_templates()`).
- [ ] **Route copy:** relocate `REROUTE_MESSAGES` and `SOFT_ROUTE_STARTER_REPLIES` from `routes/inbox_triage.py` into config + loader.
- [ ] **Add-car rules:** support `ask_driver_only` in code **or** remove from `add_car_rules.json` to match loader.

## Documentation / ops

- [ ] **Scenario index:** table of JSON packs ↔ `scripts/run_*.py` ↔ business intent.
- [ ] **String audit:** for each user-visible class, record canonical file (see boundary spec).

## Later (optional)

- [ ] **Boundary reply paragraphs:** JSON templates; keep classification in Python.
- [ ] **Industry ID env:** mirror `CLIENT_ID` for future second vertical (doc + stub only if not needed yet).

## Do not do yet

- [ ] JSON-driven append boundary graph.
- [ ] Generic workflow DSL.
- [ ] LangGraph migration.
