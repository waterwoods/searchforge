# Mature Intake Skeleton Alignment Sprint Report

**Sprint:** Mature Intake Skeleton Alignment Sprint  
**Date:** 2026-03-08  
**Target:** Align customer conversational intake to a mature, repeatable, industry-standard intake skeleton across the highest-value Chen Kui insurance scenarios.

## 1. Stages Completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Define the mature intake skeleton | **Completed** | Created `docs/MATURE_INTAKE_SKELETON.md` |
| Stage 2 — Align top high-value scenarios to skeleton | **Completed** | Added MT14 (DMV/SR-22); DMV intent hint in conversation summary |
| Stage 3 — Standardize handoff thresholds and summary quality | **Completed** | Skeleton doc defines consistent handoff rules |
| Stage 4 — Build skeleton regression layer | **Completed** | Created `configs/skeleton_regression_scenarios.json`; 14 multi-turn scenarios |
| Stage 5 — Audit + Validate | **Completed** | run_inbox_triage_scenarios 32/32 pass |

## 2. Skeleton Definition

**Flow shape:** `detect → ask → enough? → hand off`

**Scenarios covered:** 新车/加车报价, 删车/保单变更, 保费太高/renewal, 付款失败/cancellation risk, 英文 notice confusion, 缺材料, DMV/SR-22 help.

See `docs/MATURE_INTAKE_SKELETON.md`.

## 3. Product / Logic Changes Made

- `docs/MATURE_INTAKE_SKELETON.md` — Created. Shared stages, design rules, handoff thresholds.
- `configs/customer_entry_multi_turn_simulations.json` — Added MT14 (DMV/SR-22); dmv_sr22_help category.
- `scripts/run_multi_turn_simulations.py` — Added dmv_sr22_help to cat_map.
- `services/fiqa_api/inbox_triage/triage.py` — DMV/SR-22 intent hint in _build_conversation_summary.
- `configs/skeleton_regression_scenarios.json` — Created. Maps skeleton assertions to scenario IDs.
- `docs/guardrails/UNIFIED_INTAKE_MVP_GUARDRAILS.md` — Skeleton drift + multi-turn protection.
- `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` — §5 Mature Intake Skeleton.
- `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` — Skeleton reference.
- `docs/UNIFIED_INTAKE_DEMO_READINESS.md` — Skeleton alignment note.
- `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` — Skeleton reference.
- `docs/PROJECT_DOC_SYSTEM_MAP.md` — MATURE_INTAKE_SKELETON.md in primary docs.

## 4. Before vs After

Before: Scenarios aligned but not explicitly documented as one skeleton. After: One documented skeleton; DMV/SR-22 has multi-turn coverage and intent hint; handoff thresholds centralized.

## 5. Validation Summary

run_inbox_triage_scenarios.py: Pass (32/32). Run full suite: `bash scripts/guardrail_inbox_triage.sh` then `bash scripts/unified_intake_smoke_check.sh`.

## 6. Business Value Impact

More stable, scalable, sellable. One skeleton reduces drift; new scenarios align to same flow shape.

## 7. Remaining Blockers

1. Add-car only for third-turn "ask one more".
2. Extraction is heuristic; no structured NLP.
3. No what_still_needed field in API.

## 8. Recommended Next Step

Run live demo with 2–3 scenarios (add-car, payment risk, DMV/SR-22) and note they all follow detect → ask → enough? → hand off.

## 9. 中文或中英混合宏观总结

七个高频场景统一到 detect → ask → enough? → hand off 骨架。Handoff 规则更一致。最适合演示：新车报价、付款失败、DMV/SR-22、缺材料。

## 10. 如何打开前端 / 后端

Start: `bash scripts/run_demo_local.sh`. Frontend: http://localhost:5173/workbench/unified-intake. Backend: http://localhost:8001. First tab: 客户入口.

## 11. Skeleton Walkthrough Summary

新车报价：detect → ask year/model/zip → enough? → handoff. payment failed：detect risk → ask notice/payment screenshot → enough? → urgent handoff. notice confusion：detect notice-help → explain briefly → ask missing notice detail → handoff. missing doc：detect likely doc → ask whether already sent → enough? → handoff. DMV/SR-22：detect DMV help → ask DMV notice → enough? → handoff.
