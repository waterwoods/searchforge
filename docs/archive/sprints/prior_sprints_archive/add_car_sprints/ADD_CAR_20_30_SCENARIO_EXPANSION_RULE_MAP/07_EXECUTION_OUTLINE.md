# Execution Outline

## Time budget

Target **60–90 minutes** document-driven sprint: design → run → classify → summarize.

## Loops

1. **Design** — Lock 30 scenarios in `scenario_battery.json` (A–G coverage, messiness tags).
2. **Run** — Rule path JSON capture.
3. **Inspect** — Per-turn `category`, `handoff`, `follow_up_type`, fields, drafts.
4. **Classify** — Strong / Acceptable / Weak / Trust-breaking per `04_EVALUATION_CRITERIA.md`.
5. **Summarize** — Pattern analysis, gaps, rule map, broker confidence (`09_FINAL_REPORT.md`).

## Commands

```bash
cd /home/andy/searchforge

# Primary battery (30 scenarios)
PYTHONPATH=. python3 scripts/run_add_car_expansion_rule_map_battery.py --json > /tmp/acexp_only.json

# + historical ACB + ADZM (69 scenarios total)
PYTHONPATH=. python3 scripts/run_add_car_expansion_rule_map_battery.py --include-existing-batteries --json > /tmp/acexp_plus_regressions.json
```

## Optional

- Single scenario debug: `--single ACEXP-014 -v`
- API smoke (server up): `python3 scripts/test_inbox_triage_api.py`

## Completion checklist

- [ ] `scenario_battery.json` committed under sprint folder
- [ ] Runner script added
- [ ] JSON artifacts produced for this run (local `/tmp` ok)
- [ ] `09_FINAL_REPORT.md` includes scenario table + counts + 中文总结
