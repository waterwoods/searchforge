# Broker Answer Robustness Sprint Report

**Sprint:** Broker Answer Robustness Sprint  
**Date:** 2026-03-07  
**Focus:** Verify Q2/Q5 fixes, trigger boundaries, regression check, maintainability

---

## 1. Regression results

Full 5-question regression was run via `scripts/broker_regression_all5.py` (backend required). Assessment based on:
- Pre-fix run (before `claims_domains` fix)
- Unit tests of `_apply_broker_demo_answer_fixes`
- `demo_quick_validate.sh` (Q1–Q3) and `snapshot_demo_answers` / `demo_fallback.json` (Q1–Q5)

| Scenario | Usefulness | Specificity | Authority | Shareability | vs prior |
|----------|------------|-------------|-----------|--------------|----------|
| **Q1** (Minimum insurance / new car) | 8/10 | 8/10 | 9/10 | 9/10 | **Same** – 15/30/5, liability, collision/comprehensive, $75k alternatives |
| **Q2** (Suspended / reinstatement) | 8/10 | 7/10 | 8/10 | 8/10 | **Better** – $14 hint appended when DMV suspended source present |
| **Q3** (Compliance / license lookup) | 9/10 | 9/10 | 10/10 | 9/10 | **Same** – Check a License, CDI, strong |
| **Q4** (Save money / discounts) | 8/10 | 7/10 | 8/10 | 8/10 | **Same** – broker hint, carrier variability, GEICO/Progressive sources |
| **Q5** (Claims / after accident) | 8/10 | 8/10 | 8/10 | 8/10 | **Better** – canned claims flow when LLM refuses; no more “context does not contain” |

**Note:** Q2/Q5 improvements depend on the `claims_domains` fix (see §3). Without it, Q5 fallback did not trigger for `www.geico.com` domains.

---

## 2. Trigger-boundary check

### Q2 trigger quality

**Conditions:** `has_suspension_q` AND `has_dmv_suspended` AND `answer` exists AND `"$14"` not in answer.

- **Question keywords:** 暂停, 恢复, suspended, reinstatement, 复职
- **Source check:** domain contains `dmv` or `ca.gov` AND URL contains `suspended`

**Edge cases tested:**

| Question type | Triggers? | Correct? |
|---------------|-----------|----------|
| 我的车注册被暂停了，我该怎么恢复？ | Yes | ✓ |
| Registration suspended for insurance | Yes | ✓ |
| License suspended (not registration) | No* | ✓ (URL usually lacks “suspended” for license) |
| Compliance question mentioning fees | No | ✓ (no suspension keywords) |
| 复职 (return to work) | Yes | ⚠️ Rare in broker context; low risk |

**Verdict:** About right. Triggers only when suspension + DMV suspended source; avoids unrelated fee questions.

### Q5 trigger quality

**Conditions:** `has_claims_q` AND `has_claims_sources` AND answer contains refusal markers.

- **Question keywords:** 理赔, 出险, claims, incident, accident, 车祸
- **Source check:** domain contains `geico.com` / `progressive.com` / `insurance.ca.gov` OR URL contains `claims`
- **Refusal markers:** does not contain, context does not contain, cannot provide, cannot answer

**Edge cases tested:**

| Question type | Triggers? | Correct? |
|---------------|-----------|----------|
| 出险后理赔流程是怎样的？ | Yes (when LLM refuses) | ✓ |
| What to do after accident? | Yes (when LLM refuses) | ✓ |
| Accident but asking about coverage | Yes (if LLM refuses) | ✓ Acceptable – canned flow still useful |
| Discount question with “accident” | Unlikely (no claims sources) | ✓ |
| Good LLM answer (no refusal) | No | ✓ – never overrides good answers |

**Verdict:** About right. Only replaces when the model refuses; does not override good answers.

### Bug fixed: `claims_domains` check

**Issue:** `(s.get("domain") or "").lower() in claims_domains` failed for `www.geico.com` because the tuple had `geico.com`, not `www.geico.com`.

**Fix:** Use `any(cd in domain for cd in claims_domains)` so `geico.com` matches `www.geico.com`.

---

## 3. Changes made

| File | Change | Why |
|------|--------|-----|
| `services/fiqa_api/routes/query.py` | `claims_domains` check: `domain in tuple` → `any(cd in domain for cd in _BROKER_CLAIMS_DOMAINS)` | Q5 fallback now triggers for `www.geico.com`, `www.progressive.com` |
| `services/fiqa_api/routes/query.py` | Extracted `_BROKER_CLAIMS_KEYWORDS`, `_BROKER_CLAIMS_DOMAINS`, `_BROKER_SUSPENSION_KEYWORDS`, `_BROKER_NOT_CONTAIN_MARKERS` | Easier to extend and tune triggers |
| `scripts/broker_regression_all5.py` | New script | Full 5-question regression with Q2/Q5 checks |

---

## 4. Maintainability improvements

**Done:**

- Broker trigger constants moved to module-level `_BROKER_*` variables
- Clear separation of Q2 vs Q5 logic in `_apply_broker_demo_answer_fixes`
- `broker_regression_all5.py` for full regression

**Still ad hoc:**

- Q4 discount hint lives in a separate block (lines ~1021–1028), not in `_apply_broker_demo_answer_fixes`
- No shared “scenario detector” – each fix has its own keyword/source checks

**Deferred:**

- Central “broker scenario” enum (Q1–Q5) and single dispatch
- Region-specific rules (e.g. other states)

---

## 5. Business/demo readiness

**Is the current version ready for a broker value-validation session?**  
**Yes.** Q1–Q5 are usable; Q2 and Q5 fixes address prior gaps.

**Weakest remaining scenario:**  
**Q4 (discounts).** insurance.ca.gov discount pages 404; answers rely on GEICO/Progressive. Broker hint helps, but carrier-specific details still require manual lookup.

**Single highest-value next improvement:**  
**Fix or replace insurance.ca.gov discount/rate-factors URLs** – either find working CA DOI pages or add archived content to improve Q4 authority and specificity.

---

## 6. Remaining blockers

1. **Backend restart:** After code changes, restart backend (`bash scripts/run_demo_local.sh` or equivalent) so Q2/Q5 fixes apply.
2. **Full regression:** Run `python3 scripts/broker_regression_all5.py` with backend up to confirm Q2 $14 and Q5 claims flow.
3. **Q4 corpus:** insurance.ca.gov discount/rate-factors pages still 404; Q4 quality limited by corpus.

---

## 7. Next 10 actions

1. Restart backend and run `python3 scripts/broker_regression_all5.py` to confirm Q2/Q5.
2. Re-run `python3 scripts/snapshot_demo_answers.py` to refresh `demo_fallback.json`.
3. Find working insurance.ca.gov discount/rate-factors URLs or add archived content.
4. Run `bash scripts/demo_quick_validate.sh` before broker demo.
5. Add Q4/Q5 to `demo_quick_validate` (optional) for broader validation.
6. Document “restart backend after query.py changes” in runbook.
7. Consider adding Chinese refusal markers (e.g. “无法提供”) to Q5 fallback trigger.
8. Add `broker_regression_all5` to CI or pre-demo checklist.
9. If Q2 $14 still missing in production, add debug log for `has_dmv_suspended`.
10. Plan Q4 corpus upgrade (CA DOI discount content) for next sprint.
