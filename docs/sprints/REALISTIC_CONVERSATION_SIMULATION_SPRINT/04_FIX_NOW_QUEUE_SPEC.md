# Fix-Now Queue Spec

**Purpose:** Define what counts as fix-now, fix-next, defer.

---

## Fix-Now Criteria

- Directly causes broker extra follow-up
- Directly causes customer confusion in high-frequency flow
- Directly causes trust loss (generic fallback when intent clear)
- Same-day action missed (cancellation risk misclassified)
- Embarrassing in live demo

**Examples:** Generic "please provide more context" for clear add-car; wrong urgency for cancellation; Talk to Agent not detected.

---

## Fix-Next Criteria

- Friction but workaround exists
- Affects edge case, not core flow
- Summary/threshold tweak, not logic change

**Examples:** Secondary intent in mixed-intent not fully addressed; handoff one turn late.

---

## Defer Criteria

- Rare edge case
- Requires broad refactor
- Out of scope for trial

**Examples:** Full CRM integration; multi-tenant; OCR.

---

## Grouping

| Group | Examples |
|-------|----------|
| Scenario layer | Marker coverage, classification order |
| Workbench/handoff | Summary too thin, broker_next_step vague |
| Backbone/state | Handoff threshold, collected_fields |
| UI/copy | Ambiguous labels, missing CTA |
| Trial workflow/docs | Runbook unclear, handoff spec |

---

*End of Fix-Now Queue Spec*
