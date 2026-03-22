# Boundary Scenario Pack

## Source of truth

Structured scenarios: `configs/case_boundary_append_scenarios.json` (18 cases).

## Runner

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_case_boundary_battery.py [--verbose]
```

## Coverage map

| ID | Theme |
|----|--------|
| CB-01 | Add-car handoff → materials same case |
| CB-02 | Add-car → billing pivot |
| CB-03 | Add-car in progress → coverage side question |
| CB-04 | Add-car in progress → claim |
| CB-05 | Handoff → vague “还有一个问题” |
| CB-06 | Office hours on add-car thread |
| CB-07 | Pivot + billing |
| CB-08 | Pivot + claim phrasing |
| CB-09 | Pivot only |
| CB-10 | Casual + remove car |
| CB-11 | Handoff + claim |
| CB-12 | Vehicle correction same case |
| CB-13 | Short zip reply |
| CB-14 | Remove car pivot |
| CB-15 | Premium thread → add car |
| CB-16 | Claim thread → billing |
| CB-17 | Add-car → vague other insurance question |
| CB-18 | Second vehicle same quote |

## Evaluation rubric

Per scenario: expected `case_boundary`, broker prefix rules, optional `client_reply_draft` substring checks.

Classification labels for backlog:

- **Rule-based good enough** — most cross-domain and same-case rows.
- **Human confirmation better** — borderline rows (CB-05, CB-06, CB-09, CB-17).
- **LLM assist later** — long ambiguous narratives not in pack; English/Chinese code-switch with weak markers.
