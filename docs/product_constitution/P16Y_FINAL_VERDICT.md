# P16-Y Phase 10 — Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Question:** Can messy customer communication become an office-executable case?

---

## Verdict summary

| Question | Answer |
|----------|--------|
| **Can this save office time?** | **Yes — on wedge lanes** (cancellation, payment, missing doc, UW deadline). Avg **88.6/100** post-fix; broker steps already strong. Estimated **2–5 min saved per message** vs manual read + draft. |
| **Can this replace manual triage?** | **Partially — not yet fully.** ~90% of single-turn commercial paste is good enough to act. Multi-turn corrections (Y44) and premium thread merge (Y45) still require re-reading WeChat. |
| **Sprint success?** | **Yes** — +3.0 intelligence score, 0 regressions, no UI/architecture scope creep. |

---

## Scores

| Index | Before | After | Delta |
|-------|--------|-------|-------|
| Overall | 85.6 | **88.6** | +3.0 |
| Case Intelligence | 39.1 | **42.1** | +3.0 |
| Case Distillation | 43.8 | **46.5** | +2.7 |
| Office Actionability | 25.0 | 25.0 | — |

---

## What improved

1. **Classification breadth** — address, coverage, add-driver, UW questionnaire no longer fall to `unclear`
2. **Structured gaps** — `notice_image`, `deadline_mentioned`, `policy_number`
3. **Summary intent lines** — office glance shows lane without opening raw paste
4. **Zero draft regression** — office actionability stayed at ceiling

---

## Top 10 remaining intelligence gaps

| # | Gap | Example | Severity |
|---|-----|---------|----------|
| 1 | **Multi-turn summary merge** | Y44 correction — turn 1 dropped | **P0** |
| 2 | **Premium thread collected fields** | Y45 “我发你账单了” not in collected | **P1** |
| 3 | **Chinese deadline in collected** | Y02 emoji cancel — no “7 days” token | **P1** |
| 4 | **OCR / image body fusion** | Screenshot with no OCR blob | **P1** |
| 5 | **Named insured extraction** | Anonymous paste — no client name | **P1** |
| 6 | **Carrier name extraction** | “保险公司说…” — which carrier? | **P2** |
| 7 | **Vehicle count on address change** | Y12 “both cars” — not in summary | **P2** |
| 8 | **Claim vs coverage boundary** | Y37 windshield — coverage not claim lane | **P2** |
| 9 | **Secondary intent in summary** | Mixed add-car + garaging proof | **P2** |
| 10 | **LLM path parity** | Rules fixed; LLM quota path unverified this sprint | **P2** |

---

## Recommendations (next sprint — intelligence only)

1. **Append summary merge** — inject prior `[客户]` bubbles into `conversation_summary` explicitly  
2. **Premium review structured fields** — `bill_sent_claimed` when 发你账单了  
3. **Deadline → still_needed** when category is cancellation/UW and date parseable  
4. **Regression battery in CI** — `run_p16y_case_battery.py` gate at ≥88 avg  

---

## Explicit non-goals (honored)

- ❌ UI redesign  
- ❌ P17  
- ❌ Deployment  
- ❌ New pages  

---

## One-line founder read

> **The engine now converts most broker paste into a case you can act on. It does not yet replace reading the thread when the client corrects themselves mid-conversation.**

---

*End of P16-Y — Final Verdict*
