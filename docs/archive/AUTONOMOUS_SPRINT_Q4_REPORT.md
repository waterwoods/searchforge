# Autonomous Sprint Report

**Date:** 2026-03-06  
**Focus:** Q4 (discounts / saving money) + operator efficiency

---

## 1. Issue targeted

- **What:** Q4 (客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？) was the weakest remaining broker scenario.
- **Why it mattered:** Brokers need actionable discount guidance: common categories, what to ask the client, what the client should prepare, and safe carrier-variability phrasing. The existing broker hint was useful but lacked explicit discount categories and client-prep guidance. Copy-to-client output for Q4 was less structured than Q1–Q3.

---

## 2. Changes made

| File | Change |
|------|--------|
| `services/fiqa_api/routes/query.py` | Enriched Q4 broker hint: added **常见折扣类别** (好司机、多车、好学生、防御性驾驶、低里程、多保单), **客户可准备** (当前保单、驾照、车辆信息、多车情况、学生证明), and kept **经纪人可进一步询问** + carrier variability note. |
| `ui/src/pages/DemoPage.tsx` | Improved `fallbackSavings` bullets and steps: added "客户可准备" to bullets and steps for better copy-to-client when extraction is insufficient. |
| `scripts/broker_regression_all5.py` | Added Q4 validation: `q4_has_discounts`, `q4_has_broker_hint`, `q4_has_carrier_note`. Regression now fails if Q4 lacks these. |
| `ui/src/assets/demo_fallback.json` | Updated Q4 answer with the new broker hint structure for offline mode. |

---

## 3. Re-test results

- **What was tested:** `python3 scripts/broker_regression_all5.py --port 8001` (backend with `USE_LOCAL_QDRANT=1`).
- **Before:** Q4 had broker hint but no explicit discount categories or client-prep block.
- **After:** All 5 scenarios pass. Q4 answer includes:
  - 常见折扣类别（各公司政策不同，具体金额需向保险公司确认）：好司机、多车、好学生、防御性驾驶、低里程、多保单
  - 客户可准备：当前保单、驾照、车辆信息、多车情况、学生证明（如有）
  - 经纪人可进一步询问 + 各公司折扣政策不同，建议多家比价
- **Result:** **Better** – Q4 is now more useful for brokers and copy-to-client.

---

## 4. Business / broker impact

- **Broker usefulness:** Brokers get explicit discount categories and client-prep checklist; carrier variability is clearly stated.
- **Shareability:** "复制给客户" output for Q4 now includes 客户可准备 and clearer steps via improved fallbackSavings.
- **Operator simplicity:** broker_regression_all5.py validates Q4; no manual Q4 spot-check needed.
- **Product readiness:** More ready for broker value-validation or pilot use.

---

## 5. Manual-work reduction

- **Andy no longer needs to:** Manually verify Q4 has discount categories and client-prep; regression script does it.
- **Cursor can now:** Run broker_regression_all5.py to validate Q1–Q5 in one pass.
- **Reusable asset:** `broker_regression_all5.py` with Q4 checks; `docs/AUTONOMOUS_SPRINT_Q4_REPORT.md` for sprint record.

**Run broker regression:**
```bash
USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh  # or start backend with local Qdrant
python3 scripts/broker_regression_all5.py --port 8001 --out results/broker_regression.json
```

---

## 6. Future extraction note

- **Reusable:** Q4 broker hint structure (discount categories + client prep + broker follow-up + carrier note) could become a template for other regions.
- **California-specific:** Discount categories (好司机、多车、好学生等) are general; carrier URLs (GEICO, Progressive) are US/CA.
- **Config-pack material:** A `q4_discount_hint_template` could later be moved to `configs/broker_demo_*.json` for region overrides.

---

## 7. Remaining blocker(s)

- insurance.ca.gov discount/rate-factors pages still 404; Q4 corpus relies on GEICO/Progressive. No code fix for that.
- Broker regression requires `USE_LOCAL_QDRANT=1` (or working Qdrant Cloud) to run successfully.

---

## 8. Recommended next sprint

- **Target:** Add Q4 (and optionally Q5) to `demo_quick_validate.sh` so the 3-question quick validate can optionally expand to 5.
- **Why:** Reduces demo prep effort; one script validates all broker scenarios before demo.
