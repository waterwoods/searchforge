# Add-Car Real Intake Lite V1 Report

**Sprint:** Add-Car Real Intake Lite V1
**Completed:** 2026-03-19

---

## 1. Sprint theme

Transform add-car from "good chat demo" into a more realistic insurance intake by adding quote-ready visibility, clearer collected vs still-needed, and stronger broker handoff. Why now: founder concern that add-car still feels demo-like; broker trust and trial credibility require a "real intake" feel before Chen Kui trial.

---

## 2. Document set created

1. 01_ADD_CAR_REAL_INTAKE_LITE_BLUEPRINT.md
2. 02_MINIMAL_INTAKE_FIELD_SPEC.md
3. 03_QUOTE_READY_STATE_SPEC.md
4. 04_BROKER_INTAKE_VISIBILITY_SPEC.md
5. 05_EXECUTION_OUTLINE.md
6. 06_ACCEPTANCE_REAL_INTAKE_CRITERIA.md
7. 07_FOUNDER_INSPECTION_NOTES.md

---

## 3. Baseline audit

**Strongest:** Backend handoff logic, vehicle_concrete, collected/still_needed already in place.
**Biggest fake-feeling weakness:** No explicit quote-ready status; broker could not scan in under 3 seconds.
**Biggest broker-structure gap:** broker_next_step generic even when one field already collected.
**Biggest customer-trust gap:** No quote status badge during chat.

---

## 4. 10-20 point breakdown

1. Current add-car feels fake: no quote-ready badge.
2. Minimum customer info: year, make/model, zip, delivery or driver (P0).
3. Minimum vehicle info: (year + make_model) OR vin.
4. Required: vehicle + zip + (delivery OR driver).
5. Optional: VIN, name, phone.
6. VIN optional: many customers do not have it at first contact.
7. Chat populates fields: existing extraction unchanged.
8. Structured fields: green/orange tags + quote_ready_status badge.
9. Quote-ready: vehicle + zip + (delivery OR driver).
10. Almost-ready: vehicle + zip, missing delivery and driver.
11. Need-more: missing vehicle OR zip.
12. Broker sees: quote_ready_status, collected, still_needed, broker_next_step.
13. Still-needed: delivery_date, primary_driver (or year, make_model, zip when missing).
14. Reduces rework: tailored broker_next_step.
15. Improves trust: quote-ready badge.
16. Improves trial value: founder can demo "real intake."
17. Deferred: name/phone, OCR, quote engine.
18. V2: name/phone extraction.

---

## 5. Loop 1

**Fixed:** quote_ready_status in triage, case_store, UI badge.
**Why:** Highest-value, lowest-friction step.
**More real:** Broker and customer see Quote-ready / Almost ready / Need more.
**Worth it:** Yes.

---

## 6. Loop 2

**Fixed:** Tailored broker_next_step (Confirm main driver vs delivery date); getQueueReadinessLabel and getCompactQueuePreview use quote_ready_status.
**Improved:** Broker handoff more actionable.
**Worth it:** Yes.

---

## 7. Loop 3

**Hardened:** MT42 (skip VIN), MT43 (correction), MT44 (progressive), MT45 (side question).
**Improved:** 45/45 multi-turn sims pass.
**Worth it:** Yes.

---

## 8. Validation

guardrail_inbox_triage.sh: PASS. run_multi_turn_simulations.py: 45/45. ui build: Success.

---

## 9. Deployment

Backend and frontend redeploy needed.

---

## 10. Founder test list

1. Full add-car 2 turns - expect Quote-ready.
2. Partial then complete - expect status transitions.
3. Skip VIN - expect Quote-ready.
4. Correction - expect vehicle X3.
5. Side question - expect answer + handoff.
6. Queue view - expect status label.

---

## 11. Final judgment

**Biggest gain:** Quote-ready visibility.
**Biggest weakness:** Name/phone not collected.
**Real enough for Chen Kui:** Yes.
**Next step:** Deploy; run founder tests on Vercel.

---

## 12. 中文宏观总结

为什么现在做: 加车偏演示感。主要修了什么: 报价状态、broker_next_step、4个模拟。最大提升: 报价状态可见。还差什么: 姓名/电话。下一步: 部署后测试，V2考虑姓名/电话。

---

## 13. COPY/PASTE FOUNDER BLOCK

Add-Car Real Intake Lite V1 Complete. Biggest improvement: Quote-ready status visible. Biggest weakness: Name/phone deferred. Redeploy: Yes. Test: 我想加车 then 2024 Tesla Model Y 90210 下周提车 - expect Quote-ready.

---

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事

加车偏演示感，陈奎试跑前需要更真实接单体验。

### 主要用了什么方法/技术

quote_ready_status、定制broker_next_step、UI状态标签、4个加车模拟。

### 这轮最大的提升

报价状态可见，经纪人3秒内判断是否可出价。

### 现在还差什么

姓名、电话未采集；V2可补充。
