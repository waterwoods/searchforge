# P16 Visibility Simulation Report

**Script:** `scripts/run_p16_office_visibility_simulation.py`  
**Raw output:** `docs/trial/.p16_office_visibility_simulation.json`  
**Date:** 2026-06-06

---

## Battery composition

| Category | Count |
|----------|-------|
| Add-car Tesla formal submits | 5 |
| Add-car Honda formal submits | 5 |
| Certified case (`case_ea74d66fa3ba`) | 1 |
| Cancellation (same-day) | 5 |
| Payment failed | 5 |
| Missing document | 1 |
| Founder demo seeds | 6 |
| **Total** | **28** |

Pass threshold: **≥95%**

---

## Results

| Metric | Value |
|--------|-------|
| Passed | 28 / 28 |
| Pass rate | **100%** |
| Certified | **YES** |

---

## Key rank outcomes

| Case | Before (UI) | After (simulated) |
|------|-------------|-------------------|
| `case_ea74d66fa3ba` | #12 | **#7** |
| vs demo-only queue | below 11 demos | **#1** |
| Top of mixed queue | demo/action noise | urgent cancel/pay (correct) |

**Top 5 (mixed queue):** real urgent cancellation + high payment-fail — intentional; fresh add-car at **#7** (first visible screen).

---

## Scenario checks

| Rule | Result |
|------|--------|
| Recent add-car beats all demo seeds | Pass |
| Certified case on first screen (rank ≤8) | Pass (rank 7) |
| Critical/high cancellation above fresh add-car | Pass |
| High payment-fail due today above fresh add-car | Pass |
| Demo seeds below all recent add-car | Pass |

---

## Phase 5 spot cases

| # | Scenario | Visibility |
|---|----------|------------|
| 1 | New Tesla add-car submit | Rank 7 mixed / #1 demo-only |
| 2 | New Honda add-car submit | Above all demos |
| 3 | Missing-doc case | No boost (old formal) — stays below action queue |
| 4 | Cancellation case | Ranks 1–4 (urgent) — no regression |
| 5 | Payment-failed case | Ranks 5–6 when high + due today |

---

## Command

```bash
python3 scripts/run_p16_office_visibility_simulation.py
python3 scripts/run_p16_office_visibility_simulation.py --json
```

---

## Certification

**Simulation PASS (100% ≥ 95%).** Safe to certify for pilot visibility sprint.
