# Client Isolation Audit Spec

## Files reviewed

| Area | Path |
|------|------|
| Core triage | `services/fiqa_api/inbox_triage/triage.py` |
| Config load | `services/fiqa_api/inbox_triage/config_loader.py` |
| API | `services/fiqa_api/routes/inbox_triage.py` |
| Client A | `configs/clients/chen_kui/*` |
| Client B | `configs/clients/socal_precision/*` |
| Industry | `configs/industries/insurance/markers.json`, `reply_templates.json`, … |
| UI | `ui/src/api/clientConfig.ts`, `ui/src/pages/UnifiedIntakePage.tsx` |

## What already switches correctly by `client_id`

- **Handoff one-liners** (`handoff` keys: `add_car`, `other_*`, `customer_requested_human`) from `handoff_phrases.json`.
- **Reply templates** via `reply_overrides.json` merged into industry `reply_templates.json`.
- **UI chrome** via `GET /api/inbox/client-config` → `ui_copy.json` (titles, closure card, quick-start labels). `clientConfig.ts` defaults are Chen-flavored when API omits keys.

## What still leaked from core (before this sprint)

High-frequency **stitched** paths in `triage_conversation` / add-car assembly:

1. **Add-car “materials already sent”** warm handoff — hardcoded 办公室 wording for all clients.
2. **“Why still chasing” + already_sent** reassurance — hardcoded 办公室.
3. **Prospective-send lead** (`要不要发你` / WeChat / screenshot) — hardcoded **整理给办公室** (and English “office”).

## Fallback behavior biased toward Chen Kui

- **`CLIENT_ID` unset** → `get_active_client_id()` = `chen_kui` (`config_loader.py`).
- **Missing client `handoff` section** → load `chen_kui` handoff file (by design; can mask incomplete B packs).

## Highest-frequency / highest-harm if wrong

- Materials-sent + prospective-send (Add-Car flagship adjacency).
- Talk-to-agent handoff (already config-backed; verify B never sees 陈奎).

## Safe to externalize now (done)

- The three paths above via `stitched` on `handoff_phrases.json` (small schema, no business logic in JSON).

## Keep in code (this sprint)

- Intent markers, slot extraction, LLM guardrails, `_apply_append_case_boundary` continuity lines (still shared Chinese with 办公室 — see scenario `ab_10`).
- Coverage side-answer + handoff suffix (`保额…办公室`) and other overlays until a follow-up sprint scopes them.
