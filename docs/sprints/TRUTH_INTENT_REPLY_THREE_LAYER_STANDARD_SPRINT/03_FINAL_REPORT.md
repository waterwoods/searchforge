# TRUTH → INTENT → REPLY THREE-LAYER STANDARD — Final Report

## What was added to core docs

| File | Change |
|------|--------|
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | **§4.9** *Three-Layer Standard: Truth → Intent → Reply* (table of layer roles, constraint chain, relation to §4.7 flow explanation and §4.6 simulation). **§4.8** closing paragraph updated to reference two-layer foundation + **§4.9** + both sprint specs. |
| `docs/PROJECT_TRUTH_SWITCH.md` | **§6A** extended with **Intent layer (middle contract)** bullet, pointer to `02_THREE_LAYER_STANDARD_SPEC.md`, and **additional gap** (truth-safe but intent-wrong replies). |

## What standard was defined

- **Truth Layer:** Office-grade snapshot—fields, gaps, lifecycle, handoff vs formal submit, office-visible record, time semantics; authoritative for **what is allowed to be true**.
- **Intent Layer:** **Current-turn job**—what the customer is doing *now*; derived from latest text + context + **truth as hard constraint**; authoritative for **what we should answer**.
- **Reply Layer:** Natural wording that **answers resolved intent** and **never exceeds** truth.
- **Constraints:** Truth → Intent → Reply; explicit **forbidden** categories including **intent collapse** and **long-thread degradation**.
- **Industrial checklist:** Truth, Intent, Reply, and cross-surface (right rail vs reply) rows.

## What remains to be implemented later

- **First-class intent resolution** in the engine/API (reviewable labels or equivalent), not only implicit hints inside `triage.py`.
- **Regression assets** that assert intent + truth + reply together on long threads (build on Role C / scenario replay).
- **Optional:** surface resolved intent in simulation/replay UI for operator visibility (aligned with master outline §4.9).

## Recommended next sprint

**Intent resolution implementation sprint (Add-Car bounded):** define a minimal **intent taxonomy** and wire **reply family selection** to **resolved intent × truth snapshot**; add **guardrail or scenario tests** for late-turn non-collapse (e.g. turns 7–10 battery). Keep scope to Add-Car flagship and avoid broad refactors.
