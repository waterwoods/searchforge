# Small-Batch Customer-Visible Copy Externalization Sprint Blueprint

## Sprint intent

Move a small, safe batch of high-frequency customer-visible residual copy from `triage.py` into existing client-overridable phrase maps, without changing triage control flow.

## Scope

- In scope:
  - Residual copy audit for customer-visible lines still in engine
  - 2-4 phrase-family externalization using existing `stitched` phrase map style
  - A/B isolation validation (`chen_kui` vs `socal_precision`)
  - Regression and guardrail validation
- Out of scope:
  - Rewriting `triage.py`
  - Moving business logic/decision flow into JSON
  - New framework/config system

## Selected small batch (this sprint)

1. Handoff doc-clarification suffix lines (add-car and non-add-car variants)
2. Add-car coverage side-question handoff overlay (answer + suffix)
3. Payment correction + urgency handoff line

## Why this batch

- High visibility: appears on handoff-critical moments that customers read directly.
- High leak risk: hardcoded shared office voice in core engine (`办公室 / office`) even when client style differs.
- Low implementation risk: wording-only extraction into existing `stitched` retrieval path.

## Safety design

- Keep all detection and routing logic in Python.
- Add only optional phrase keys under `handoff_phrases.json -> stitched`.
- Engine defaults remain hardcoded if keys are omitted.
- No cross-client fallback introduced.

## Deliverables

- Code and config updates for selected phrase families
- Small-batch A/B battery + runner
- Guardrail integration
- Founder-facing final report with move-now/move-later/keep-in-code judgment
