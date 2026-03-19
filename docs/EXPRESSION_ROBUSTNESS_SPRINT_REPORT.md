# Expression Robustness Sprint Report

**Sprint:** Expression Robustness Sprint  
**Date:** 2026-03-09

## 1. Stages Completed

- Stage 1: Build same-intent expression packs — **Completed**
- Stage 2: Run robustness simulations — **Completed**
- Stage 3: Fix highest-value robustness failures — **Completed**
- Stage 4: Standardize through intake skeleton — **Completed**
- Stage 5: Audit + validate — **Completed**

## 2. Expression Packs

Created configs/expression_robustness_cases.json with 7 intents, 36 variants.

## 3. Product / Logic Changes

triage.py: ADD_VEHICLE_MARKERS + 拿车, 报价, 多少钱; REMOVE_VEHICLE_MARKERS + sold; VEHICLE_CONTEXT_MARKERS + sold; QUESTION_HELP_MARKERS + what does.

configs/inbox_triage_scenarios.json: Added ER1-ER4 regression cases.

## 4. Robustness Results

Before: 32/36 strong. After: 36/36 strong.

## 5. Validation Summary

All checks pass: npm build, scenarios (40/40), proxy (14/14), multi-turn (14), expression robustness (36/36), guardrail, smoke check.

## 6. 中文宏观总结

测了7类意图36种说法。修掉4个脆弱点。现在BMW X5、付款失败、英文通知、缺材料等用多种说法都能得到正确回复。

## 7. 如何打开

bash scripts/run_demo_local.sh -> http://localhost:5173/workbench/unified-intake
test
