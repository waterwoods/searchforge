# Current Ownership / Responsibility Map

**Last updated:** Flow Lightweight Productization Sprint (2026-03-22)

## Runtime entrypoints

| Owner | Responsibility |
|-------|----------------|
| `routes/inbox_triage.py` | HTTP validation, `soft_route` / reroute UX lines (loaded from config), case persistence **when** `handoff_ready`, session save |
| `triage.triage_conversation` | Single source of truth for triage output shape, workflow keys, handoff decisions |
| `triage.triage_for_append` | Re-triage with case context; boundary behavior |
| `case_store` | Durability, attachment rules, case status machine (lightweight) |

## Config loader (`config_loader.py`)

| Function | Owns |
|----------|------|
| `get_insurance_markers` / `get_document_item_markers` | Industry lexicon |
| `get_reply_templates(client_id)` | Industry base + **that client’s** `reply_overrides.json` only |
| `get_handoff_phrases(client_id)` | Client handoff strings (+ fallback to default client if missing) |
| `get_ui_copy(client_id)` | Client UI strings |
| `get_add_car_rules` / `save_add_car_rules` | Industry add-car prompts including `ask_driver_only` |
| `get_workflow_fallbacks` | Common fallbacks |
| `get_soft_route_inbox_copy` | Common soft-route reroute + starter replies |

## Concentration vs scatter

- **Too concentrated:** Most conversational policy still in `triage.py` (~3k+ LOC). This is **acceptable** for this phase; rewriting without tests is not.
- **Too scattered:** Intent markers split between `markers.json` and large `_FALLBACK_MARKERS` in code — intentional safety net; document when extending.
- **Fragile:** Any change to `WORKFLOW_STATE_KEYS` or handoff gating order — must run full guardrail.
- **Already well-separated:** Industry vs client JSON paths; common workflow defaults; regression scripts.

## Safe to move now (this sprint)

- Reply override path by `client_id` (not hardcoded broker folder).
- Route-level Chinese strings for soft-route → `configs/common/soft_route_inbox.json`.
- Align `add_car_rules` loader/save with `ask_driver_only` key present on disk.

## Keep in code (for now)

- `_should_handoff`, add-car quote-ready logic, mixed-intent branches, LLM merge/guardrails.
- Case append boundary classification.
