# Acceptance Criteria

## Functional

- New stitched keys are read correctly from client packs.
- Selected handoff overlay phrases are client-overridable.
- Omitted keys still use engine defaults without crash.

## Isolation

- `chen_kui` and `socal_precision` produce distinct intended wording on selected paths.
- Client B no longer leaks selected Client A office wording on those paths.

## Regression safety

- Add-car flagship handoff path remains intact.
- No logic-routing regressions (`handoff_ready`, category selection) on tested paths.
- Full inbox guardrail remains green.

## Documentation

- Required sprint docs are created.
- Final report includes move-now / move-later / keep-in-code judgment and risk analysis.
