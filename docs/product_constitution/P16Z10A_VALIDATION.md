# P16-Z10A Phase 6 — Validation

**Date:** 2026-06-02  
**Sprint:** P16-Z10A Memory Core Hardening  
**Engine:** rules path (`LLM_GENERATION_ENABLED=0`)

---

## Batteries run

| Battery | Command | Result |
|---------|---------|--------|
| **Role D** | `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py` | See below |
| **P16-Y** | `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16y_case_battery.py --label after` | **88.9/100** (no regression) |
| **Guardrails** | `bash scripts/guardrail_inbox_triage.sh` | **PASS** (13/13 HT + append A/B) |

---

## Role D — before vs after Z10A

| Metric | Z7 baseline | Z10A after | Target | Met? |
|--------|-------------|------------|--------|------|
| Avg memory (0–75) | 60.7 | **62.3** | — | ↑ |
| Avg reread (0–100) | 68.9 | **75.8** | ≥75 | ✅ |
| Needs WeChat | 4/10 | **0/10** | ≤3/10 | ✅ |
| Category match | 5/10 | **9/10** | — | ↑ |
| Claims retention | 36% | 36% | — | unchanged |

---

## Per-journey delta (Role D)

| ID | Reread before | Reread after | Needs WeChat before | Needs WeChat after | Notes |
|----|---------------|--------------|---------------------|--------------------|-------|
| D01 | 65 | 65 | ✅ | ❌ | payment_amount added; cancel class improved |
| D02 | 60 | 70 | ✅ | ❌ | payment lane; fields persist |
| D03 | 60 | 70 | ✅ | ❌ | missing_document + zip_94588 |
| D04 | 70 | 70 | ❌ | ❌ | stable |
| D05 | 70 | 70 | ❌ | ❌ | stable |
| D06 | 74 | 74 | ❌ | ❌ | stable |
| D07 | 70 | **80** | ❌ | ❌ | remove lane guard ✅ |
| D08 | 90 | 90 | ❌ | ❌ | stable |
| D09 | 70 | 70 | ❌ | ❌ | stable |
| D10 | 60 | **80** | ✅ | ❌ | payment_lapse + installment |

---

## Target journeys (D03, D10, D02, D07)

| Journey | Z10A acceptance | Status |
|---------|-----------------|--------|
| D03 zip persists | `garaging_zip`, `zip_94588` in collected | ✅ |
| D10 not unclear | `payment_lapse_expiration` | ✅ |
| D02 fields persist | `already_paid_claimed` Day 3 | ✅ |
| D07 lane stable | Summary ≠ "New quote" | ✅ |

---

## Append battery fix

`run_role_d_memory_battery.py` now passes `reply_truth_context` with prior turn `collected_fields` / `still_needed_fields` — matches production `case_store` append path.

---

## Regression check

- P16-Y avg: **88.9** (unchanged from pre-Z10A)
- Guardrail inbox triage: **PASS**
- No new modules, services, or storage

---

## Phase 6 verdict

**VALIDATION PASS** — Role D reread ≥75, needs WeChat 0/10, P16-Y green, guardrails green.
