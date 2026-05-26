# Correction Confirmation Reply Blueprint — Add-Car

## Goal

When the customer **corrects which vehicle** they mean (e.g. Honda → Tesla, X5 → X3), the **customer-facing reply** must:

1. **Explicitly name the effective vehicle** the office will use (year + make/model when available), in **natural office Chinese** (or equivalent English).
2. **Avoid thin acknowledgements** that only echo the year (“好的，2024的”) when a fuller vehicle label is knowable from the thread.
3. **Preserve slot collection**: continue asking for the next missing field (zip, delivery, driver) without changing broker handoff rules.

## Target phrasing (Chinese)

- Lead: **「好的，我按 {effective_vehicle} 这台车继续。」**
- Then: next ask from rules, e.g. **「先把邮编发我，我就能继续帮您报价。」**

## Detection

- **Vehicle correction** = negation/clarification + re-specification of vehicle (markers include 不是这个、不是这辆、不是…是、不对…是、搞错了…是、English “not that one / meant the …”, etc.).
- **Effective vehicle** = resolved from the **latest customer bubble** on correction turns when possible, with **year pool** from full customer text so X5→X3 keeps the same year.

## Non-goals

- No OCR, no carrier API, no frontend, no new architecture.
