# P16-Z7 Phase 5 — Claims Stress Test

**Date:** 2026-06-02  
**Cases:** 10 difficult claims · 3 turns each (`configs/role_d_claims_battery.json`)  
**Engine:** `triage_conversation` + `triage_for_append`  
**Metric:** Keyword retention % in summary + collected + broker_next_step

---

## Aggregate

| Metric | Value |
|--------|-------|
| **Avg keyword retention** | **36%** |
| Turn 1 FNOL routing | Strong (8/10 claim-ish summary) |
| Turn 2+ memory | Weak (corrections, plates, amounts) |
| Worst case | **CL02** (0%), **CL06** (20%) |

---

## Per-case results

| ID | Title | Retention | Final category | Summary headline |
|----|-------|-----------|----------------|------------------|
| CL01 | Hit-and-run + plate fix | 40% | customer_question | Claim intake; police in latest only |
| CL02 | Total loss correction | **0%** | unclear | Message count only — **全损 context lost** |
| CL03 | Photo chain | 50% | missing_document | **Wrong lane** — DL chase not claim |
| CL04 | Carrier delay | 40% | customer_question | Policy 9901234; hail weak |
| CL05 | Claim + payment pivot | 40% | customer_question | Correction flag; 2/28 weak |
| CL06 | Injury + statement | 20% | unclear | MRI/neck dropped |
| CL07 | Uninsured motorist | 50% | customer_question | UM/deductible in latest only |
| CL08 | Glass → full claim | 40% | customer_question | VIN 88219 in latest only |
| CL09 | Not accident correction | 40% | customer_question | 刮蹭 correction partial |
| CL10 | Rental + total loss fight | 40% | unclear | $18k in latest only |

---

## Stress dimensions tested

| Dimension | Result |
|-----------|--------|
| Plate corrections | CL01 — partial; plate in latest, typo turn lost in headline |
| Total loss disputes | CL02, CL10 — **fail**; 全损 / $18k not in collected |
| Photo references | CL03, CL08 — photos in collected sometimes; not in summary |
| Police report updates | CL01 — `police_report` collected T3; not in T1–2 summary |
| Carrier delays | CL04 — escalate intent in latest; adjuster wait weak |
| Mixed claim/payment | CL05 — “不是payment” honored as correction; accident date weak |
| Injury complexity | CL06 — **fail** — no injury fields |
| UM coverage | CL07 — coverage question lane; plate 4AB2291 partial |

---

## TOP 10 claims memory failures

| # | Failure | Case |
|---|---------|------|
| 1 | Total loss correction drops FNOL | CL02 |
| 2 | `unclear` on multi-turn injury | CL06 |
| 3 | Claim thread misclassified as missing_document | CL03 |
| 4 | Dollar amounts not in collected | CL10, CL02 |
| 5 | Plate correction not in summary headline | CL01 |
| 6 | Rental extension not retained | CL10 |
| 7 | Hail / roof leak not in collected | CL04 |
| 8 | Glass→full pivot loses “glass only” context | CL08 |
| 9 | Police report # only in latest snip | CL01 |
| 10 | Adjuster wait not setting waiting_on | CL04, CL05 |

---

## TOP 10 claims successes

| # | Success | Case |
|---|---------|------|
| 1 | Turn 1 FNOL templates fire | CL01, CL04, CL05, CL09 |
| 2 | `accident_reported` often collected | CL01, CL03, CL05, CL08, CL09 |
| 3 | `Customer corrected/clarified` in summary | CL05, CL09 |
| 4 | Policy # extraction | CL04 |
| 5 | `police_report` field on upload turn | CL01 |
| 6 | Photos field when client says sent | CL03, CL08 |
| 7 | Hit-and-run heuristic | CL01 |
| 8 | Multi-turn message count | All 10 |
| 9 | `other_driver_info` on plate threads | CL03, CL05 |
| 10 | No new FNOL service required | Architecture OK — tune memory |

---

## Comparison to P16-Z6 claims validation

| Metric | Z6 (engine) | Z7 Role D |
|--------|-------------|-----------|
| Avg turn score | 16.4/25 | ~36% retention (different rubric) |
| Correction prepend | C9 improved | CL09 @ 40% |
| UI thread | Shipped | Not re-run live |

Z7 confirms Z6: **Turn 1 pilot-ready; Turn 2+ needs claim-specific collected merge.**

---

## Phase 5 verdict

**Claims 3-day memory: NO-GO for unsupervised use**

- Safe: Turn 1 paste → evidence checklist  
- Unsafe: Correction chains, total loss disputes, injury, carrier-wait without WeChat  
- Next slice (not Z7 build): plate/policy/$ in `collected_fields` merge on append; `waiting_on: carrier` heuristic
