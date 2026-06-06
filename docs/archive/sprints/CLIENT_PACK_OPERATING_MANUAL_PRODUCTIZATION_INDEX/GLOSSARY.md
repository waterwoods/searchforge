# Glossary — Unified Intake Productization

| Term | Meaning |
|------|---------|
| **Unified Intake** | SearchForge MVP: customer message intake + broker triage output + optional case persistence (inbox triage product surface). |
| **Client pack** | Folder `configs/clients/<client_id>/` with `ui_copy.json`, `handoff_phrases.json`, `reply_overrides.json`, etc. |
| **Client ID** | String `client_id`; active value from env `CLIENT_ID` (default `chen_kui`). Selects which client pack loads. |
| **Industry pack** | `configs/industries/insurance/` — shared California auto insurance markers and templates. |
| **Common config** | `configs/common/` — defaults shared across clients (e.g. soft-route copy, workflow fallbacks). |
| **Triage engine** | `triage.py` — turns text (+ context) into structured triage fields and manages workflow progression. |
| **Config loader** | `config_loader.py` — reads JSON and defines merge / fallback rules. |
| **Soft route** | UI quick-start intent hint (`add_car`, `missing_document`, etc.) sent to API to steer first turn. |
| **Handoff** | State where customer-facing copy says the office will take over; phrases often from `handoff_phrases.json`. |
| **Stitched phrases** | Optional nested copy under `handoff_phrases.json` → `stitched` (boundaries, caveats, tails). |
| **Reply templates** | Industry base in `reply_templates.json`; client may override via `reply_overrides.json`. |
| **Markers** | Keyword lists in `markers.json` used for rule-based intent detection. |
| **Case store** | JSON-backed persistence of saved cases for demo/workbench (`case_store.py`). |
| **Scenario pack** | `configs/inbox_triage_scenarios.json` — expected outputs for rule-mode checks. |
| **Guardrail** | `scripts/guardrail_inbox_triage.sh` — umbrella script chaining regression tests. |
| **A/B isolation scripts** | Tests that broker A’s output must not contain broker B’s configured strings. |
| **LLM_GENERATION_ENABLED** | Env flag; `0` forces more deterministic rule-focused runs in CI scripts. |

---

*See [READ_THIS_FIRST.md](./READ_THIS_FIRST.md).*
