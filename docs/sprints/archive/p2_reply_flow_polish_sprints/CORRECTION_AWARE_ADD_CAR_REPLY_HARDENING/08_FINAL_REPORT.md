# Correction-Aware Add-Car Reply Hardening — Final Report

## 1. Sprint theme

Make Add-Car **correction turns** feel understood: explicit **effective vehicle** in the customer reply, then **only** the next missing fields — broker accuracy preserved.

## 2. Document set created

| # | File |
|---|------|
| Blueprint | `01_CORRECTION_AWARE_ADD_CAR_REPLY_BLUEPRINT.md` |
| Detection | `02_ADD_CAR_CORRECTION_DETECTION_SPEC.md` |
| Effective vehicle | `03_EFFECTIVE_VEHICLE_STATE_SPEC.md` |
| Reply templates | `04_CORRECTION_REPLY_TEMPLATE_SPEC.md` |
| Execution | `05_EXECUTION_OUTLINE.md` |
| Acceptance | `06_ACCEPTANCE_CRITERIA.md` |
| Founder inspection | `07_FOUNDER_INSPECTION_NOTES.md` |
| Final report | `08_FINAL_REPORT.md` |

## 3. Baseline audit

| Finding | Detail |
|---------|--------|
| Biggest correction weakness | Vehicle concrete from **whole thread** could keep **X5** after “是 X3”; BMW trim order checked **X5 before X3**. |
| Biggest trust issue | `_get_add_car_acknowledgement` filled **year** first and **skipped** model when both present → thin “2024年的”. |
| Best low-risk fix | Vehicle-scoped extraction on correction turns + correction template + pass **merged** text into ack builder. |

## 4. What was fixed

- `_is_add_car_vehicle_correction_signal` for vehicle-specific corrections (excludes driver-only `说错了`).
- `_add_car_vehicle_concrete_from_scope` + correction-first path in `_extract_add_car_vehicle_concrete`; last **X3/X5** token in scope wins.
- `_get_add_car_acknowledgement(..., merged_text_for_vehicle=...)` with correction zh/en templates and zip-in-same-turn line.
- Single-turn add-car draft uses same helper (fixes plain **Tesla**).
- Handoff prefix for add-car + vehicle correction + concrete.
- Simulations **ACE13–ACE16**.

## 5. Validation summary

- `guardrail_inbox_triage.sh`: **PASS** (includes multi-turn pack, API checks, ACE suite).
- `run_multi_turn_simulations.py`: **67/67** strong (after ACE16 expected handoff aligned to T1 quote-ready).
- `run_add_car_edge_case_simulations.py`: **16/16** strong, **0** weak.

## 6. Biggest improvement

Customer-facing add-car replies **name the corrected vehicle** (ZH: **我按 … 这台车继续**) instead of year-only acknowledgements.

## 7. Biggest remaining weakness

- Very messy or ambiguous corrections (no year/make in the correction bubble) still depend on **prior turns** for year; rare edge cases may need LLM or richer parsing later.
- Minor: optional space after `继续。` before the next Chinese sentence (cosmetic).

## 8. Backend redeploy

**Yes** — `services/fiqa_api/inbox_triage/triage.py` changed. Redeploy the **fiqa / inbox triage API** environment that serves Unified Intake; do not assume auto-deploy.

## 9. Founder test case

**Paste (T1 → T2):**

1. `我想加车 2021 Honda`  
2. `不是这个，是 2024 Tesla`

**Expected (better reply):** contains **「好的，我按 2024 Tesla 这台车继续。」** then asks for **zip** (e.g. 先把地址邮编发我…), not “好的，2024的” only.

## 10. 中文宏观总结

本次冲刺针对「客户改口是哪台车」的场景，把**对有效车辆的确认**写进客户可见的回复里，并修正了「只_ack 年份、不提车型」以及「全线程里仍偏向旧车（如 X5）」的问题。实现上增加了**车辆改口检测**、在改口时**以最后一条客户消息为主**解析车型/年份，并在必要时把手写话术与材料已发场景的前缀对齐。验证上跑通 guardrail、全量多轮模拟与 ACE 加车边角用例；**上线需重新部署**后端 triage 服务。
