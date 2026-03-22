# Execution Outline

## Time box

Target **45–75 minutes** for design + run + classify + write up (can be split across agents).

## Loop

1. **Design** — Lock scenario list in `scenario_battery.json` (this sprint: 19 cases).
2. **Run** — Execute runner with LLM off; save JSON artifact if needed.
3. **Inspect** — For each scenario, read last-turn `follow_up_type`, `collected_fields`, `still_needed_fields`, drafts, broker step.
4. **Classify** — Strong / Acceptable / Weak / Trust-breaking with logic vs reply vs broker split.
5. **Summarize** — Counts, pillar robustness, single best next fix.
6. **Document** — `FINAL_REPORT.md`, `FOUNDER_INSPECTION_NOTES.md`.

## Step-by-step (operator)

```bash
cd /home/andy/searchforge
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_driver_zip_materials_stress_battery.py -v
# Or machine-readable:
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_driver_zip_materials_stress_battery.py --json | tee docs/sprints/ADD_CAR_DRIVER_ZIP_MATERIALS_STRESS_BATTERY/.last_run.json
```

## Optional: compare with API

When `localhost:8001` is up, spot-check one scenario via `POST /api/inbox/triage` — should match `triage_conversation` for the same text sequence.

## Done when

- All 19 scenarios executed under rule path.
- Final report includes scenario table, counts, 中文总结, and copy-paste founder block.
