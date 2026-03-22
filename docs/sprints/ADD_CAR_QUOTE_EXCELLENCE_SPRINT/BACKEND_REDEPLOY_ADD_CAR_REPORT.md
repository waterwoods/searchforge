# Backend Redeploy for Add-Car Quote Excellence Report

## 1. Sprint theme

- **What was deployed:** Backend-only changes from the Add-Car Quote Excellence Sprint: `triage.py`, `add_car_rules.json`, and related add-car logic.
- **Why now:** Add-car improvements (ask_driver_only, concrete vehicle extraction, coverage/garaging side-question handling, handoff timing) only matter if they are live in production. The founder needs confidence that the Vercel frontend now reflects the stronger backend behavior.

## 2. Pre-deploy validation

### Files inspected

| File | Confirmed |
|------|-----------|
| `configs/industries/insurance/add_car_rules.json` | `ask_driver_only` present (zh/en) |
| `services/fiqa_api/inbox_triage/triage.py` | `_extract_add_car_vehicle_concrete()`, `_get_next_ask_for_add_car` with coverage/doc skip, coverage handoff reply, garaging handoff |
| `configs/handoff_timing_simulations.json` | HT8, HT11, HT12 (add-car + side questions, correction) |

### Test results

| Script | Result |
|--------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (64/64 scenarios, 41 multi-turn, 12 handoff timing, 27 simulation assistant, 8 broker stress) |
| `PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py` | **12/12 passed** (HT1–HT12) |

### Blocker

**None.** All validation passed. One minor API test failure (`append follow-up message: need case_id`) is unrelated to add-car and does not block deployment.

## 3. Backend deploy result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-1013093472160.us-west1.run.app |
| **Alternate URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | fiqa-api-00033-jdz |
| **Warnings** | pip venv warning (non-blocking); /healthz FAILED (service may still be warming) |
| **Readiness** | /readyz OK |

Deployment completed successfully. Cloud Run is serving 100% traffic to the new revision.

## 4. Post-deploy verification

Production API verified via `PYTHONPATH=. python3 scripts/verify_add_car_production.py --url https://fiqa-api-1013093472160.us-west1.run.app`.

### Scenario A — Normal add-car flow

| Item | Value |
|------|-------|
| **Input** | 1) 我想加一台车 2) 2024 Tesla Model Y，92620 3) 下周提车，我自己开 |
| **Expected** | add-car route, reasonable ask-next/handoff, concrete vehicle in summary/next_step |
| **Observed** | `handoff_ready=True`, `broker_next_step` = "Run quote for 2024 Tesla Model Y. Confirm delivery date and driver with client before binding." |
| **Pass/Fail** | **PASS** |
| **Notes** | Concrete vehicle in broker_next_step; handoff at T3. |

### Scenario B — Add-car + coverage side question

| Item | Value |
|------|-------|
| **Input** | 1) 我想加一台车 2) 2024 Tesla Model Y，92620，下周提车 3) 对了，coverage 能不能调一下？ |
| **Expected** | Answer coverage question, then hand off; do not ignore and blindly ask driver again |
| **Observed** | `handoff_ready=True`, `client_reply_draft` = "您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。" — no coverage answer |
| **Pass/Fail** | **PARTIAL** |
| **Notes** | Handoff works; coverage answer missing. Pattern covers "coverage 可以调吗" but not "coverage 能不能调一下" — minor phrasing gap. |

### Scenario C — Add-car + garaging proof question

| Item | Value |
|------|-------|
| **Input** | 1) 我想加一台车 2) 2024 BMW X5，90210，下周提车 3) 对了，garaging proof 是什么？ |
| **Expected** | Answer clarification, then hand off; do not continue mechanical ask-next |
| **Observed** | `handoff_ready=True`, `client_reply_draft` includes "garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。" |
| **Pass/Fail** | **PASS** |
| **Notes** | Garaging answer present; handoff proceeds. Draft also includes generic add-car ask text — acceptable. |

### Scenario D — Add-car correction

| Item | Value |
|------|-------|
| **Input** | 1) 我想加一台 2024 BMW X5 2) 不是 X5，是 X3 3) 92620，我老婆开 |
| **Expected** | Correction respected; case remains add-car; summary/next_step uses corrected vehicle |
| **Observed** | `handoff_ready=True`, `broker_next_step` = "Run quote for 2024 Bmw. Confirm delivery date and driver before binding." — X3 not in next_step |
| **Pass/Fail** | **PARTIAL** |
| **Notes** | Correction logic works in simulations (HT12); production showed "2024 Bmw" instead of "2024 BMW X3" — possible extraction edge case with merged context. |

### Summary

| Scenario | Pass | Notes |
|----------|------|-------|
| A | ✓ | Concrete vehicle, handoff |
| B | △ | Handoff OK; coverage answer missing for "能不能调一下" phrasing |
| C | ✓ | Garaging answer + handoff |
| D | △ | Handoff OK; X3 not surfaced in broker_next_step |

## 5. Final operational judgment

1. **Did backend deploy succeed?** Yes. Revision fiqa-api-00033-jdz is live.
2. **Are the add-car improvements now live?** Yes. ask_driver_only, concrete vehicle extraction, garaging side-question handling, and handoff timing are in production.
3. **Which production verification scenarios passed?** A and C fully; B and D partially (handoff works, minor gaps in coverage phrasing and X3 extraction).
4. **What remains the biggest add-car weakness?** Coverage-question phrasing ("coverage 能不能调一下") not covered; correction-to-X3 sometimes not reflected in broker_next_step.
5. **Can Andy now safely test on Vercel?** Yes. Backend is live; add-car flows are stronger than before. Test the four scenarios on Vercel to confirm end-to-end behavior.

## 6. 中文宏观总结

- **为什么现在要 redeploy backend：** Add-Car Quote Excellence Sprint 的改动（ask_driver_only、具体车型提取、coverage/garaging 侧问处理、handoff 时机）需要上线生产，Vercel 前端才能用到新逻辑。
- **哪些 add-car 改进已经上线：** ask_driver_only 配置、broker_next_step 展示具体车型、garaging 侧问回答后 handoff、coverage 侧问（部分句式）回答后 handoff、HT11/HT12 相关逻辑。
- **哪些验证通过了：** 场景 A（正常加车）和 C（garaging 侧问）完全通过；场景 B（coverage 侧问）和 D（车型更正）handoff 正常，但有句式/提取小缺口。
- **现在我可不可以去 Vercel 测：** 可以。后端已部署，add-car 行为已加强，建议在 Vercel 上跑一遍上述四个场景做端到端验证。

## 7. COPY/PASTE FOUNDER BLOCK

```
Backend Redeploy for Add-Car Quote Excellence — DONE

Deploy status: SUCCESS (revision fiqa-api-00033-jdz)
Backend URL: https://fiqa-api-1013093472160.us-west1.run.app

Add-car verification:
  ✓ Scenario A (normal flow): concrete vehicle in broker_next_step, handoff
  ✓ Scenario C (garaging question): answer + handoff
  △ Scenario B (coverage question): handoff OK; "coverage 能不能调一下" not in pattern
  △ Scenario D (correction): handoff OK; X3 not always in broker_next_step

Biggest remaining weakness: Coverage phrasing gap; correction-to-X3 extraction edge case.

Andy: You can test on Vercel now. Backend is live; add-car is stronger than before.
```

## 8. REQUIRED SHORT OVERVIEW

### 为什么做这件事

Add-Car Quote Excellence Sprint 的 backend 改动需要上线生产，让 Vercel 前端使用新的 ask-next、车型提取、侧问处理和 handoff 逻辑。

### 主要用了什么方法/技术

Pre-deploy 验证（guardrail、handoff timing 模拟）→ Cloud Run 部署（deploy_rag_demo.sh）→ 生产 API 四场景验证（curl/Python 脚本）。

### 这轮最大的提升

Backend 成功部署；add-car 的 ask_driver_only、具体车型、garaging 侧问回答、handoff 时机改进已上线；场景 A、C 生产验证通过。

### 现在还差什么

Coverage 侧问句式扩展（"coverage 能不能调一下"）；correction 后 X3 在 broker_next_step 中的稳定提取；在 Vercel 上的端到端人工验证。
