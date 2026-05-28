# Scope boundary spec

## In scope

- `ui/src/pages/UnifiedIntakePage.tsx` — customer entry copy, section labels, buttons, pilot intro text, tab labels, main brand tagline wiring.
- `ui/src/api/clientConfig.ts` — new `portal_*` keys + updated defaults (`app_title`, quick-start label).
- `configs/clients/chen_kui/ui_copy.json` — mirror portal keys for production client pack.
- `services/fiqa_api/inbox_triage/config_loader.py` — whitelist new keys for `/api/inbox/client-config`.

## Out of scope (explicit)

- Triage rules, prompts, model selection, case persistence semantics.
- OCR, carrier APIs, email/WeChat integrations.
- Replacing Ant Design or large layout rewrites.
- New business lines or broker workbench feature work (except tab label reads from same `ui_copy`).

## Risk posture

- **Display-only** changes with **defaults** if API omits keys.
- Backend change is **pass-through whitelist only**; no new endpoints.

## Rollback

- Revert TS + JSON + `config_loader.py` or remove keys from JSON to fall back to `DEFAULT_UI_COPY`.
