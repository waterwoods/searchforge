# Residual Copy Externalization Blueprint

## Purpose

Finish peeling **high-frequency, customer-visible** phrasing off the Unified Intake rule engine so **same-industry client packs** (Chen Kui vs SoCal Precision) can diverge on voice **without** changing classification, handoff gates, or slot collection order.

## In scope

- Wording that appears on **hot paths** (add-car quote collection, premium/payment mixed-intent tails, add-driver, bundling).
- **Client-overridable** surfaces already used in the product: `handoff_phrases.json` → `stitched`, and `reply_overrides.json` shallow merge over industry `reply_templates.json`.

## Out of scope (this sprint)

- OCR, carrier APIs, framework swaps, splitting `triage.py` broadly, giant policy JSON, UI redesign, cross-industry abstraction.

## Design rules

1. **No cross-client fallback** for stitched keys: missing key → engine default string (avoids Client A bleed into Client B).
2. **Business logic stays in code**; only **append tails** and **template bodies** move to config.
3. **Regression first**: guardrail + Add-Car battery + prior A/B runners stay green.

## Clients

- **Client A:** `chen_kui` (defaults in code + industry templates = historical office voice).
- **Client B:** `socal_precision` (second-broker pack: 本所 / desk).

## Deliverables

- Engine hooks + client JSON.
- Focused A/B battery + runner (`scripts/run_residual_copy_ab_scenarios.py`).
- Documentation set in this folder + validation record.
