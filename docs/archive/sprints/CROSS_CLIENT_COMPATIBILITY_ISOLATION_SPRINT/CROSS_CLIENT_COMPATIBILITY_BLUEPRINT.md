# Cross-Client Compatibility Blueprint

## Purpose

Same-industry Unified Intake must support **hot-pluggable client packs**: switching `client_id` should change **customer-visible language and office posture** without silently applying another broker’s phrases.

## In-scope clients (this sprint)

| Role | `client_id` | Notes |
|------|-------------|--------|
| Client A | `chen_kui` | Reference pack; 办公室 / 陈奎 tone |
| Client B | `socal_precision` | Second-broker drill; 本所 / 营业日 tone |

## Architectural facts (as implemented)

1. **Per-client JSON** under `configs/clients/<client_id>/`: `handoff_phrases.json`, `reply_overrides.json`, `ui_copy.json`.
2. **Industry layer** (`configs/industries/insurance/*`) is shared; **client** merges overrides where supported (`reply_overrides`).
3. **`get_handoff_phrases`** still falls back to `chen_kui` when a non-default client file is missing keys (documented risk for partial packs).
4. **New:** optional `stitched` block inside `handoff_phrases.json` for **high-frequency stitched paths** that previously lived only in `triage.py`. **No cross-client fallback** for `stitched` — empty/missing → engine defaults (avoids Chen wording bleeding into B).

## Non-goals

Cross-industry portability, UI redesign, carrier APIs, large template DSLs, or rewriting triage logic beyond thin config hooks.

## Success picture

- A/B drills show **different** visible copy where packs intend it.
- **No false confidence:** remaining engine-hardcoded Chinese (e.g. append-case boundary) is listed explicitly until externalized.
