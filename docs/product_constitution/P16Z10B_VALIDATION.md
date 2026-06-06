# P16-Z10B Phase 7 — Validation

**Date:** 2026-06-02  
**Engine:** rules path (`LLM_GENERATION_ENABLED=0`)

---

## Commands run

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16y_case_battery.py --label after
bash scripts/guardrail_inbox_triage.sh
```

---

## Success targets

| Metric | Target | Z10A | Z10B | Met? |
|--------|--------|------|------|------|
| Role D reread | ≥80 | 75.8 | **82.6** | ✅ |
| Need WeChat | 0/10 | 0/10 | **0/10** | ✅ |
| Claims retention | ≥70% | 36% | **71%** | ✅ |
| waiting_on auto | ≥7/9 | 0/9 | **9/9** | ✅ |
| P16-Y | ≥88 | 88.9 | **88.6** | ✅ |
| Guardrails | PASS | PASS | **PASS** | ✅ |

---

## Role D journeys (reread)

| ID | Reread | Notes |
|----|--------|-------|
| D01 | 74 | payment/cancel tokens improved |
| D02 | 80 | confirmation + portal tokens |
| D03 | 80 | stable |
| D04 | 70 | stable |
| D05 | 90 | claim + adjuster suggest |
| D06 | 74 | broker suggest on quote |
| D07 | 90 | stable |
| D08 | 90 | stable |
| D09 | 70 | stable |
| D10 | 80 | payment persist |
| **Avg** | **82.6** | |

---

## Waiting-on battery

9/9 scenarios — see `.role_d_results/role_d_battery.json` → `waiting_on_scenarios`.

---

## Claims battery

Avg **71%** — see `claims[]` in same JSON artifact.

---

## P16-Y

**88.6/100** — no regression vs Z10A (88.9).

---

## Guardrails

**PASS** — inbox triage HT 13/13, append A/B, client persistence.

---

## Phase 7 verdict

**VALIDATION PASS** — all Z10B acceptance gates green.
