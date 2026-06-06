# Structured Workbench Expansion Sprint Report

**Sprint:** Structured Workbench Expansion Sprint  
**Date:** 2026-03-10  
**Scope:** Extend structured intake from Add Car to Renewal and Claim flows

## 1. Stages completed

- Stage 1: Define selective structured intake — Completed
- Stage 2: Implement backend structured fields — Completed
- Stage 3: Expand Broker Workbench UI — Completed
- Stage 4–5: Simulation — Guardrail PASS
- Stage 6–7: Improvement loops — Skipped (first pass sufficient)
- Stage 8–10: Proof, regression, audit — Completed

## 2. Structured-intake targets

**Renewal:** premium_concern, renewal_context, remove_vehicle_interest, coverage_adjust_interest, policy_bill_sent; still: renewal_notice_or_bill, current_premium_details, which_vehicle_to_remove, target_coverage_preference

**Claim:** accident_reported, hit_and_run, photos, other_driver_info, police_report, injuries; still: photos, other_driver_insurance_license, accident_time_location, police_report_if_applicable

## 3. Changes made

- triage.py: _extract_renewal_fields, _renewal_structured_fields, _extract_claim_fields, _claim_structured_fields
- triage_conversation + route: wire renewal and claim
- UnifiedIntakePage: RENEWAL_FIELD_LABELS, CLAIM_FIELD_LABELS, humanizeStructuredField, inferCaseFocusFromText (claim), FOUNDER_DEMO_QUEUE + QUICK_FILL (renewal, claim)
- Docs: BROKER_HANDOFF_CLARITY_GUIDE, UNIFIED_INTAKE_DEMO_READINESS, UNIFIED_INTAKE_MVP_RUNBOOK

## 4. Validation

- guardrail_inbox_triage.sh: PASS
- npm run build: PASS

## 5. 中文宏观总结

扩到 Renewal 和 Claim 两条主线。经纪人一眼能看到 premium_concern、renewal_context、remove_vehicle_interest、accident_reported、hit_and_run、photos 等。Add-car、Renewal、Claim 三种 case 更像真实业务处理。对陈奎：三条主线都有结构化，产品更像真实办公室工具。

## 6. Cheat sheet

| Flow | Structure |
|------|-----------|
| Add-car | year, make_model, zip, delivery_date, primary_driver, vin |
| Renewal | premium_concern, renewal_context, remove_vehicle_interest, policy_bill_sent; still: renewal_notice_or_bill, which_vehicle_to_remove |
| Claim | accident_reported, hit_and_run, photos, other_driver_info; still: photos, other_driver_insurance_license, accident_time_location |

## 7. Live proof walkthroughs

1. Add-car: 客户要加一台2021 Tesla Model Y — Collected: Year, Make/Model, Delivery; Still needed: Primary driver
2. Renewal: 客户说这个月保费太高了 — Collected: Premium too high; Still needed: Renewal notice or bill, Current premium details
3. Remove-one-car: 续保保费太高了，其中一辆去掉会便宜吗 — Collected: Premium too high, Renewal context, Remove vehicle interest; Still needed: Renewal notice or bill, Which vehicle to remove
4. Claim: 刚出事故了，要收集什么？ — Collected: Accident reported; Still needed: Photos, Other driver insurance/license, Accident time/location
5. Control: Cancellation notice — No structured chips (graceful fallback)
