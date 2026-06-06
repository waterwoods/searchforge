# High-Frequency Residual Copy Audit Spec

## Method

1. Read `services/fiqa_api/inbox_triage/triage.py` for `_build_client_reply_draft`, `_get_next_ask_for_add_car`, and `triage_conversation` merge paths.
2. Compare with existing externals: `configs/industries/insurance/reply_templates.json`, `configs/clients/*/handoff_phrases.json` (`stitched`), `configs/clients/*/reply_overrides.json`.
3. Classify each candidate: **frequency**, **visibility**, **voice leak risk**, **safe to externalize**, **keep in code** (logic-tied).

## Residuals identified (pre-sprint)

| Area | Example (engine) | Frequency | Leak risk | Verdict |
|------|-------------------|-----------|-----------|---------|
| Add-car price / ballpark caveat | `；具体数字要等办公室按车型和地址算出来。` / `our office will run the numbers` | Very high on quote path | **High** (办公室 / office) | **Externalize** (`stitched.add_car_price_caveat`) |
| Payment / premium + “already sent materials” tail | `；如果材料说发过了，我这边也帮你核对。` | Medium-high | Medium (我这边 vs 本所) | **Externalize** (`stitched.document_already_sent_tail`) |
| Add-driver first-turn reply | Hardcoded zh/en in `customer_question` | Medium | Medium | **Externalize** (`reply_templates.add_driver` + overrides) |
| Bundling first-turn reply | Hardcoded zh/en | Medium | Medium | **Externalize** (`reply_templates.bundling` + overrides) |
| Progressive add-car asks (`_get_next_ask_for_add_car`) | Uses `add_car_rules` but **omitted caveat** when this path wins | High (multi-turn UI) | Same as caveat row | **Unify** with same stitched caveat helper |
| Missing signature, UW, renewal one-liners | Short category replies | Medium | Lower | **Defer** (can move to templates later) |
| Marker tuples / detection strings | `_FALLBACK_MARKERS`, talk-to-agent fallbacks | N/A (not customer draft) | N/A | **Keep in code** |

## Leak checklist (before → after)

| Path | Before | After |
|------|--------|-------|
| Add-car + 多少钱 / roughly | Always 办公室 / our office in caveat | Client B: 本所 / our desk via `stitched` |
| Premium + 发过了 + doc | Fixed 我这边 tail | Client B: 本所 tail |
| Add-driver / bundling | Single hardcoded voice | Industry default + Client B overrides |

## What remains in engine (post-sprint)

- Most **category one-liners** (missing_signature, renewal_reminder, informational, etc.).
- **Handoff assembly** glue (suffixes, correction paths) beyond this batch.
- **Intent markers** and **broker_next_step** English (broker-facing; lower priority for customer “voice leak”).
