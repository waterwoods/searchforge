# P16 Append Integrity — Executive Summary

**Date:** 2026-06-06  
**Sprint:** P16-APPEND-INTEGRITY-SPRINT

---

## Problem

AC05 formal submit → customer returns later → append name/phone → `delivery_date` disappeared from `collected_fields`, reappeared in `still_needed_fields`, broker next step regressed to ask for delivery again. Trust-breaking for Chen Kui demo.

---

## Root cause

`append_follow_up_message()` **replaced** case field lists with fresh triage output instead of **merging additively** with persisted case memory. Triage re-extraction can drop relative delivery dates when `persisted_collected_fields` is missing from context.

---

## Fix location

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/case_store.py` | `_merge_append_field_lists()`, `_office_broker_next_step_from_still()`, merge in `append_follow_up_message()` |
| `services/fiqa_api/inbox_triage/triage.py` | `Name:` English contact extraction pattern |
| `tests/test_append_field_integrity.py` | Regression tests |
| `scripts/run_p16_append_simulation_battery.py` | 22-scenario battery |

---

## Tests executed

| Suite | Count | Result |
|-------|------:|--------|
| Append integrity unit tests | 3 | PASS |
| Add-car persisted coherence | 8 | PASS |
| Inbox triage scenario pack | 64 | PASS |
| Pre/post submit reply regression | 4 checks | PASS |
| Append simulation battery | **22** | **22/22 PASS** |
| AC03 / AC05 / AC07 triage | 3 | PASS |
| AC05 append E2E | 1 | PASS |

**Regression cases re-run:** 7 (AC03, AC05, AC07, Continue/Start/History/Formal/Append flows)

---

## Simulation count

**22** (categories A–J)

---

## Commercial verdict

| Item | Value |
|------|-------|
| Can append lose information? | **NO** |
| Confidence | High (95%) |

---

## GO / NO GO

# **GO**

Append behaves as additive memory. Customer returns later, adds name/phone — system retains VIN, ZIP, delivery date, driver. AC acceptance paths unchanged.

---

## Artifacts

| Phase | Doc |
|-------|-----|
| 0 | `P16_APPEND_BUG_PREFLIGHT.md` |
| 1 | `P16_APPEND_REPRODUCTION.md` |
| 2 | `P16_APPEND_ROOT_CAUSE.md` |
| 4 | `P16_APPEND_SIMULATION_REPORT.md` |
| 5 | `P16_APPEND_REGRESSION_REPORT.md` |
| 6 | `P16_APPEND_COMMERCIAL_CERTIFICATION.md` |
| 7 | `P16_APPEND_EXECUTIVE_SUMMARY.md` (this file) |

---

*P16-APPEND-INTEGRITY-SPRINT complete.*
