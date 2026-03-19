# Unified Broker Validation Sprint Report

## 1. Issue targeted

**What:** `demo_quick_validate.sh` was the documented pre-demo entry point but only validated Q1–Q3. Full broker validation (Q1–Q5) lived in a separate script (`broker_regression_all5.py`). Andy had to run two different commands to get complete confidence before demo/pilot.

**Why it mattered:** Manual mental load, risk of forgetting to run the full regression, and inconsistent “recommended” path across docs. The product is close to broker value-validation use; a single reliable pre-demo check reduces operator effort and improves repeatability.

## 2. Changes made

| File | Change |
|------|--------|
| `scripts/broker_regression_all5.py` | Added `--report PATH` to write `REPORT.md` with per-scenario pass/fail, Q2/Q4/Q5 checks, and overall summary. |
| `scripts/demo_quick_validate.sh` | Replaced curl + `demo_quick_validate.py` (Q1–Q3) with a single call to `broker_regression_all5.py` (Q1–Q5). Kept health check and same output location (`results/demo_quick_validate/<timestamp>/REPORT.md`). |
| `scripts/demo_pre_checklist.sh` | Updated Offline fallback text: "click 3 sample questions" → "click 5 sample questions". |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Updated quick validate description to "Q1–Q5". |

**Why it helps:** One command (`bash scripts/demo_quick_validate.sh`) now validates all 5 broker scenarios, produces a clear REPORT.md, and preserves the same entry point used by `demo_pre_checklist.sh` and `demo_prepare_tomorrow.sh`.

## 3. Re-test results

**What was tested:**
- `bash scripts/demo_quick_validate.sh` (backend on 8001)
- `bash scripts/demo_pre_checklist.sh` (which invokes demo_quick_validate)

**Q1–Q5 coverage:** All 5 scenarios validated. Report shows:
- Q1: minimum insurance / new car ✅
- Q2: suspended / reinstatement, $14 fee ✅
- Q3: compliance / license lookup ✅
- Q4: save money / discounts, broker hint, carrier note ✅
- Q5: claims flow, no refusal ✅

**Before vs after:**

| Aspect | Before | After |
|--------|--------|-------|
| Scenarios covered | 3 (Q1–Q3) | 5 (Q1–Q5) |
| Commands for full validation | 2 (demo_quick_validate + broker_regression_all5) | 1 (demo_quick_validate) |
| Q4/Q5 checks | Separate script only | In default path |
| REPORT.md format | 3-question rules (gov/insurer) | 5-scenario broker checks |

**Verdict:** Better — single path, full coverage, clearer output.

## 4. Operator impact

**Andy no longer needs to:**
- Run `broker_regression_all5.py` separately before demo
- Remember which script covers which scenarios
- Manually verify Q4/Q5 before pilot use

**New default validation path:**
```bash
bash scripts/demo_quick_validate.sh
```
Or via pre-demo checklist:
```bash
bash scripts/demo_pre_checklist.sh
```

**Cursor / OpenClaw can now:** Run `demo_quick_validate.sh` once to validate all 5 broker scenarios and get a single REPORT.md.

## 5. Future extraction note

**Reusable:**
- `broker_regression_all5.py` with `--report` is a good base for a “scenario pack” (questions + checks)
- REPORT.md structure (summary + per-scenario) could be a template for other validation packs

**California-specific:**
- Questions and checks (Q2 $14, Q4 discounts, Q5 claims) are California auto insurance broker–specific
- A future “validation pack” could parameterize: questions file, check rules, region label

**No heavy architecture changes.** The structure suggests a later extraction into a scenario pack / validation pack, but that is out of scope for this sprint.

## 6. Remaining blocker(s)

None. Validation path is unified and working.

## 7. Recommended next sprint

**Target:** Snapshot/offline pack alignment — ensure `snapshot_demo_answers.py` and `demo_fallback.json` stay in sync with the 5 validated scenarios so Offline mode always has current answers for Q1–Q5.

**Why:** Demo_quick_validate now validates live; the offline fallback should reflect the same 5 questions. If snapshot is stale, Offline mode may show outdated answers.
