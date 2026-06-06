# Current Portability Audit Spec

## Files reviewed (minimum set)

| Area | Path | Lens |
|------|------|------|
| Loader | `services/fiqa_api/inbox_triage/config_loader.py` | What is per-client vs industry vs common; fallbacks |
| Engine | `services/fiqa_api/inbox_triage/triage.py` | Hardcoded ZH/EN strings, client_id threading |
| API | `services/fiqa_api/routes/inbox_triage.py` | `client_id` on triage + append; soft-route copy source |
| Client pack | `configs/clients/chen_kui/*` | Reference pack shape |
| Industry | `configs/industries/insurance/*` | Shared templates, markers, add_car_rules |
| Common | `configs/common/*` | `soft_route_inbox.json`, `workflow_defaults.json` |
| UI API | `ui/src/api/clientConfig.ts` | Defaults = Chen Kui wording when merge base |
| UI page | `ui/src/pages/UnifiedIntakePage.tsx` | Uses `useClientConfig()` + passes `clientId` into triage |
| Context | `ui/src/context/ClientConfigContext.tsx` | `?client=` query param |

## Findings summary (see also PORTABILITY_GAPS_SPEC.md)

### Already client-pack friendly

- `get_ui_copy(client_id)` — whitelist keys, per-client JSON.
- `get_handoff_phrases(client_id)` — per-client file; **falls back to `chen_kui`** if missing (important for ops, dangerous if mistaken for isolation).
- `get_reply_templates(client_id)` — industry base + per-client overrides; **no cross-client fallback** on overrides (good).
- API `client_id` on `POST /api/inbox/triage` and append; cases store `client_id`.
- UI passes `clientId` from context into triage and append.

### Still leaks default / Chen-adjacent behavior

- `config_loader._DEFAULT_CLIENT_ID` and `get_active_client_id()` default to `chen_kui`.
- `ui/src/api/clientConfig.ts` **DEFAULT_UI_COPY** is Chen-branded (e.g. 陈奎 starter); used when API fails or keys missing.
- `configs/industries/insurance/markers.json` **talk_to_agent** still lists **联系陈奎 / 找陈奎** (broker name in “industry” file).
- `triage.py` contains many **hardcoded Chinese sentences** (handoff branches, materials-sent path, coverage side-answers, etc.) using **办公室** regardless of `client_id`.
- `get_soft_route_inbox_copy()` and `get_add_car_rules()` are **not** per-client (common + industry only).

### Configurable today but shared across brokers

- Add-car **next-step prompts** (`add_car_rules.json`) — industry-wide.
- Soft-route reroute + starter replies (`soft_route_inbox.json`) — common.
- Category broker/client templates (`category_templates.json`) — industry.

### Dangerous to treat as “portable” without caveats

- Missing client `handoff_phrases.json` **silently** falling back to Chen Kui phrases — looks like second broker, sounds like Chen Kui.
- Assuming `reply_overrides` always apply — some stitched replies bypass the template path.
