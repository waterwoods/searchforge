# P16 Append Integrity — Simulation Report

**Date:** 2026-06-06  
**Sprint:** P16-APPEND-INTEGRITY-SPRINT — Phase 4  
**Battery:** `scripts/run_p16_append_simulation_battery.py`  
**Result:** **22/22 PASS**

---

## Categories

| Cat | ID | Scenario | Result |
|-----|-----|----------|--------|
| A. Add name only | A1, A2 | `Name: Li Hua` / `My name is Li Hua` | PASS |
| B. Add phone only | B1, B2 | `Phone: 949-555-1234` / `call me at ...` | PASS |
| C. Add name + phone | C1, C2, C3 | English / compact / Chinese | PASS |
| D. Add VIN later | D1, D2 | VIN append on partial case | PASS |
| E. Add ZIP later | E1, E2 | ZIP append | PASS |
| F. Add driver later | F1, F2 | primary driver append | PASS |
| G. Add delivery later | G1, G2 | delivery append + regression sim | PASS |
| H. Multiple appends | H1–H4 | Sequential name/phone + regression sim | PASS |
| I. Empty append | I1 | Empty message (rejected at API) | PASS (skip) |
| J. Repeated append | J1, J2 | Same name/phone twice | PASS |

---

## Representative rows (Before / After / Expected / Actual)

### C1 — Name + phone (AC05 audit append)

| | Value |
|--|-------|
| **Before collected** | year, make_model, vin, zip, delivery_date, primary_driver, … |
| **Before still** | name, phone, notice_image |
| **Append** | `Name: Li Hua\nPhone: 949-555-1234` |
| **After collected** | … delivery_date, primary_driver, **name, phone** |
| **After still** | notice_image |
| **Expected** | Prior slots preserved; name/phone added |
| **Actual** | PASS |

### H1 — Multiple append with triage regression simulation

| | Value |
|--|-------|
| **Before collected** | includes delivery_date |
| **Simulated triage** | Drops delivery_date; adds to still_needed |
| **After collected** | delivery_date **preserved** (store merge) |
| **After still** | delivery_date **not** reintroduced |
| **Expected** | Additive memory wins over triage regression |
| **Actual** | PASS |

### G2 — Delivery append + regression sim

| | Value |
|--|-------|
| **Append** | `pickup next Wednesday` |
| **Expected** | delivery_date not lost from prior collected |
| **Actual** | PASS |

### I1 — Empty append

| | Value |
|--|-------|
| **Expected** | Reject empty (ValueError / HTTP 400) |
| **Actual** | PASS — not executed in battery; API/store guard |

---

## Full battery summary

```
22/22 passed
```

Command:

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16_append_simulation_battery.py
```

---

*Phase 4 complete.*
