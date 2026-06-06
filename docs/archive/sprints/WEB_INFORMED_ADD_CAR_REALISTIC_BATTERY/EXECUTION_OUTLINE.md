# Execution Outline

## Preconditions

- Repo root: `/home/andy/searchforge` (or your checkout).  
- Python 3 with project dependencies available (same as other triage scripts).  

## Run the battery (rule path)

```bash
cd /home/andy/searchforge
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_web_informed_add_car_realistic_battery.py
```

JSON only (for archiving or diffing):

```bash
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_web_informed_add_car_realistic_battery.py --json > docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/battery_run_results.json
```

Single scenario (debug):

```bash
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_web_informed_add_car_realistic_battery.py --single WIRC-004 -v
```

## Loops (document-driven sprint)

1. **Design** — Edit `scenario_battery.json`; update `SOURCE_GROUNDED_SCENARIO_DESIGN_SPEC.md` if categories shift.  
2. **Run** — Regenerate `battery_run_results.json`.  
3. **Inspect** — Per turn: `issue_category`, `handoff_ready`, `quote_ready_status`, `follow_up_type`, drafts, fields.  
4. **Classify** — Strong / Acceptable / Weak / Trust-breaking + escalation label.  
5. **Summarize** — Update `FINAL_REPORT.md` and gap specs.  

## Related runners (reuse context)

- `scripts/run_add_car_scenario_battery.py`  
- `scripts/run_add_car_driver_zip_materials_stress_battery.py`  
- `scripts/run_add_car_edge_case_simulations.py`  
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` (broader inbox)  

## API path (optional)

With server on **8001**, `scripts/test_inbox_triage_api.py` can hit HTTP; this sprint used **direct `triage_conversation`** for deterministic offline evaluation.
