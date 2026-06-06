# TRUTH LAYER + REPLY LAYER INDUSTRIAL STANDARD SPRINT — Final Report

## What was added to core docs

| Document | Change |
|----------|--------|
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | New **§4.8 Structured Truth Layer vs Reply Generation Layer (Industrial Standard)** after §4.7: purpose split, constraint, pointer to this sprint’s spec. |
| `docs/PROJECT_TRUTH_SWITCH.md` | New **§6A. STRUCTURED TRUTH VS REPLY GENERATION (INDUSTRIAL CONTRACT)** between persistence (§6) and priorities (§7): authoritative fields, subordination of replies, known failure mode, link to spec. |

## What standard was defined

- **Structured truth layer:** fields, gaps, lifecycle, handoff vs formal submit, office-visible record, time semantics, ready/not-ready distinctions.
- **Reply generation layer:** phrasing, intent acknowledgment, variation, reassurance, next steps—all **bounded** by truth.
- **Constraint:** reply is **subordinate**; no stronger factual claims than truth + persistence support.
- **Non-overreach table** and **industrial review checklist** in `02_TWO_LAYER_STANDARD_SPEC.md`.

## Honest mapping to current Add-Car system

- **Aligned today:** `triage.py` computes `collected_fields`, `still_needed_fields`, `handoff_ready`, `lifecycle_status`; append logic when name/phone still missing shows awareness of truth–reply tension; UI `AddCarRecordSummaryRail.tsx` explicitly separates **`handoff_ready` / `handoff_pending`** from **`isFormalSubmissionToOfficeComplete`** for step-3 / “办公室已收到” style copy.
- **Remaining tension:** `handoff_phrases.json` (e.g. add_car “已到办公室”) can still **read stronger** than formal-submit truth if not gated consistently in every code path; some stitched suffixes assert “已提交办公室” in branches that assume `handoff` without re-checking persist flags; template variety (`zh_alt`) must be reviewed against **non-overreach** row-by-row.

## What remains to be implemented later

- Central **reply guard** (or lint/tests) that asserts customer-visible strings do not contain office-receipt idioms unless `formal_submitted_at` / lifecycle matches product rules.
- Automated scenarios that fail when `still_needed_fields` non-empty but reply implies completeness.
- Optional: unify handoff phrase keys with **explicit truth predicates** in config schema (machine-checkable).

## Recommended next sprint

**Enforcement sprint:** “Truth-locked reply templates” — implement automated checks + triage/UI alignment so no reply path can emit office-receipt or completeness claims without matching structured + persistence predicates; add guardrail scenarios drawn from §D of `02_TWO_LAYER_STANDARD_SPEC.md`.
