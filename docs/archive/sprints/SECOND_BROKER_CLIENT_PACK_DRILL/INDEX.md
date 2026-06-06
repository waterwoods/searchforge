# Second Broker / Client-Pack Drill Sprint — Index

Sprint folder for a **document-driven portability drill**: same-industry second broker via `client_id` + client pack, minimal core changes.

| Doc | Purpose |
|-----|---------|
| [SECOND_BROKER_DRILL_BLUEPRINT.md](./SECOND_BROKER_DRILL_BLUEPRINT.md) | Mission, scope, drill design |
| [SECOND_BROKER_CLIENT_PACK_SPEC.md](./SECOND_BROKER_CLIENT_PACK_SPEC.md) | Fictional broker persona + config surfaces |
| [CURRENT_PORTABILITY_AUDIT_SPEC.md](./CURRENT_PORTABILITY_AUDIT_SPEC.md) | What was audited and how |
| [CLIENT_PACK_DRILL_SCENARIO_PACK.md](./CLIENT_PACK_DRILL_SCENARIO_PACK.md) | Scenario list + link to `drill_scenarios.json` |
| [PORTABILITY_GAPS_SPEC.md](./PORTABILITY_GAPS_SPEC.md) | Leaks, false portability, next fixes |
| [EXECUTION_OUTLINE.md](./EXECUTION_OUTLINE.md) | Step-by-step execution order |
| [ACCEPTANCE_CRITERIA.md](./ACCEPTANCE_CRITERIA.md) | Done definition for the drill |
| [FOUNDER_INSPECTION_NOTES.md](./FOUNDER_INSPECTION_NOTES.md) | Short checklist for founder review |
| [FINAL_REPORT.md](./FINAL_REPORT.md) | Full sprint judgment + 中文总结 |
| [drill_scenarios.json](./drill_scenarios.json) | Machine-readable drill scenarios |

**Runner:** `PYTHONPATH=. python3 scripts/run_second_broker_drill.py`

**Second client pack:** `configs/clients/socal_precision/`
