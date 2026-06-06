# Execution Outline

## Loop 1 — Audit

- Read: `triage.py` (structure, client_id threading), `config_loader.py`, `routes/inbox_triage.py`, `case_store.py`.
- Inventory: industry vs client vs common JSON; regression scripts invoked by guardrail.

## Loop 2 — Layer map

- Produce five-layer spec + ownership map + “what lives where” tables.

## Loop 3 — Low-risk implementation (this sprint)

| ID | Change | Risk |
|----|--------|------|
| L1 | `get_reply_templates(client_id)` + per-client cache in `triage.py` | Low — overrides empty today for Chen Kui; fixes future multi-client correctness |
| L2 | `get_soft_route_inbox_copy()` + `configs/common/soft_route_inbox.json` | Low — defaults match prior strings |
| L3 | `get_add_car_rules` / `save_add_car_rules` include `ask_driver_only` | Low — aligns disk schema with engine |

## Loop 4 — Validation

- `bash scripts/guardrail_inbox_triage.sh` (mandatory).

## Loop 5 — Report

- `FINAL_REPORT.md` + founder inspection notes.

## Not in this outline

- LangGraph migration, triage file split, new UI.
