# Broker Demo Quality Standard

**Scope:** California Auto Insurance Broker Demo/Pilot path only.

## What Must Always Be True Before Demo/Pilot Use

| Requirement | Check | Fail if |
|-------------|-------|---------|
| Q1–Q5 core scenarios pass | `broker_regression_all5.py` | Any of 5 fails; Q2 missing $14; Q5 missing claims flow; Q4 missing discounts/broker/carrier; workflow hints missing for Q1/Q2/Q3/Q5 |
| Offline pack has 5 items | `demo_fallback.json` items.length | < 5 |
| Offline pack has workflow hints | Each item.answer contains 客户可准备 + 经纪人可进一步询问 | < 5 items with both |
| Copy-to-client excludes broker-only | `scripts/verify_copy_to_client_guardrail.py` + `guardrail_broker_demo.sh` | 经纪人可进一步询问 or 经纪人下一步 appears in client copy |
| Demo path is consistent | run_demo_local.sh → 8001; Docker → 8000 | Validation uses wrong port for actual demo backend |

## Core Scenario Coverage (Q1–Q5)

| Label | Question (Chinese) | Must Include |
|-------|--------------------|---------------|
| Q1 | 新车最低保险/怎么配 | 客户可准备 + 经纪人可进一步询问 |
| Q2 | 注册暂停/恢复/费用 | $14 fee + 客户可准备 + 经纪人可进一步询问 |
| Q3 | 查合规/执照 | 客户可准备 + 经纪人可进一步询问 |
| Q4 | 省钱/折扣 | 折扣关键词 + broker hint + 各公司/政策不同 |
| Q5 | 理赔流程 | 理赔/索赔 + 客户可准备 + 经纪人可进一步询问 |

## Workflow-Helper Expectations

- **客户可准备**: What the client should prepare (documents, info).
- **经纪人可进一步询问**: What the broker should ask next.
- **经纪人下一步**: What the broker should do next (actionable next step).
- All three must appear in Q1, Q2, Q3, Q5 answers (live and offline).
- Q4 already has broker hint; must also have carrier-variability note (各公司/政策不同).

## Offline Pack Alignment

- `demo_fallback.json` must be refreshed after a PASS from `demo_quick_validate.sh`.
- `demo_quick_validate.sh` runs snapshot on PASS; if validate fails, snapshot does not run.
- If `demo_fallback.json` is missing or has < 3 items, `DEFAULT_FALLBACK_ITEMS` in DemoPage.tsx is used.
- `DEFAULT_FALLBACK_ITEMS` must also include workflow hints so worst-case fallback is broker-useful.

## Copy-to-Client Cleanliness

- **Included:** 客户可准备 content surfaced as dedicated **您可准备** section (client-facing tone).
- **Excluded:** 经纪人可进一步询问, 经纪人下一步 (broker-internal).
- Filter: `demoCopy.ts` `buildCopyTextClientReady` filters bullets/steps containing `BROKER_ONLY_MARKERS`.
- Structure: 客户可准备 is extracted and rendered as "您可准备：" before 建议您 for clearer client usability.
- Guardrail: `scripts/verify_copy_to_client_guardrail.py` (run by `guardrail_broker_demo.sh`) fails if broker-only content would leak.

## Pre-Demo Validation Expectations

1. Run `bash scripts/demo_pre_checklist.sh` (or `--strict` to fail on drift).
2. Run `bash scripts/demo_quick_validate.sh` when backend is up.
3. If validate PASS: offline pack is refreshed automatically.
4. If validate FAIL: use Offline path only; click 5 recommended questions.

## What Counts as Regression / Drift

- **Regression:** Q1–Q5 answers lose workflow hints, Q2 loses $14, Q5 loses claims flow, Q4 loses discounts/broker/carrier.
- **Drift:** Offline pack has fewer than 5 items with workflow hints; validation QUESTIONS diverge from snapshot QUESTIONS; copy-to-client starts including 经纪人可进一步询问.
- **Tolerated:** Backend down (use Offline); long-tail (LT03/LT04) not in core validation unless `--longtail`.

## Fail Loudly vs Tolerate

| Condition | Action |
|-----------|--------|
| Workflow hints < 5 in offline pack | Fail (--strict) or warn |
| Offline pack < 5 items | Fail (--strict) or warn |
| broker_regression QUESTIONS ≠ snapshot QUESTIONS | Fail |
| Copy-to-client includes 经纪人可进一步询问 or 经纪人下一步 | Fail (unit test or guardrail) |
| Backend down | Tolerate; use Offline path |
| Port mismatch (8000 vs 8001) | Document; operator chooses correct port |
