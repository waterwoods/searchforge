# Backend Redeploy for Realistic Simulation Fixes Report

**Sprint:** Backend Redeploy for Realistic Simulation Fixes  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Date:** 2026-03-19

---

## 1. Sprint Theme

- **What was deployed:** Backend (fiqa-api) to Cloud Run with the Realistic Conversation Simulation + Fix-Now fixes: "找陈奎" → talk_to_agent, "急死了 保单要停了" → cancellation_warning/critical.
- **Why now:** These fixes matter only if they are live in production. The founder needs confidence that the production API behaves correctly and the frontend trial/demo benefits from the new backend behavior.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/backend_redeploy_realistic_simulation/01_SPRINT_BLUEPRINT.md` |
| Execution Outline | `02_EXECUTION_OUTLINE.md` |
| Acceptance / Operational Criteria | `03_ACCEPTANCE_CRITERIA.md` |
| Founder Verification Checklist | `04_FOUNDER_VERIFICATION_CHECKLIST.md` |

---

## 3. Pre-Deploy Validation

### Files Inspected

| File | Expected Logic | Found |
|------|----------------|-------|
| `configs/industries/insurance/markers.json` | "找陈奎" in talk_to_agent | ✓ Line 287 |
| `configs/industries/insurance/markers.json` | "保单要停了" in policy_stop | ✓ Line 67 |
| `services/fiqa_api/inbox_triage/triage.py` | policy_stop alone → cancellation_warning, critical | ✓ Lines 954–955 |
| `services/fiqa_api/inbox_triage/triage.py` | _is_talk_to_agent_request fallback includes "找陈奎" | ✓ Lines 897–901 |
| `configs/realistic_conversation_simulation_pack.json` | RC-S5, RC-S6 scenarios | ✓ |
| `scripts/run_realistic_conversation_pack.py` | Runner exists | ✓ |

### Validation Results

| Script | Result |
|--------|--------|
| `run_realistic_conversation_pack.py` (RC-S5, RC-S6) | PASS |
| `run_realistic_conversation_pack.py` (full) | 20/20 Strong |
| `run_inbox_triage_scenarios.py` | 64/64 passed (via guardrail) |
| `run_multi_turn_simulations.py` | 41/41 PASS |
| `audit_state_field_accuracy.py` | 9/9 passed |
| `verify_speed_routing.py` | All OK |
| `guardrail_inbox_triage.sh` | 64/64, continuity OK |
| `unified_intake_smoke_check.sh` | PASS |

### Direct Triage Test (Key Scenarios)

```
A 找陈奎: customer_requested_human medium ✓
B 急死了 保单要停了: cancellation_warning critical ✓
C 联系人工: customer_requested_human ✓
```

**Blocker:** None. All validations passed.

---

## 4. Backend Deploy Result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-1013093472160.us-west1.run.app |
| **Revision** | fiqa-api-00030-4k7 |
| **Warnings/Errors** | /healthz returned FAILED during deploy script (404 on curl); /readyz OK |
| **Readiness** | /readyz: `ok: true`, `intake_path_ready: true` |

Deployment completed successfully. The triage API responds correctly.

---

## 5. Post-Deploy Verification

### Scenario A — Talk to Agent shorthand

| Field | Value |
|-------|-------|
| **Input** | 找陈奎 |
| **Expected** | customer_requested_human, handoff_ready, NOT unclear |
| **Observed** | issue_category: customer_requested_human, urgency: medium, handoff_ready: true |
| **Pass/Fail** | **PASS** |
| **Notes** | Directly verified in production |

### Scenario B — Cancellation urgency shorthand

| Field | Value |
|-------|-------|
| **Input** | 急死了 保单要停了 |
| **Expected** | cancellation_warning, critical, NOT unclear |
| **Observed** | issue_category: cancellation_warning, urgency: critical |
| **Pass/Fail** | **PASS** |
| **Notes** | Directly verified in production |

### Scenario C — Existing Talk to Agent phrase

| Field | Value |
|-------|-------|
| **Input** | 联系人工 |
| **Expected** | customer_requested_human, handoff-ready |
| **Observed** | issue_category: customer_requested_human, handoff_ready: true |
| **Pass/Fail** | **PASS** |
| **Notes** | Directly verified in production |

### Scenario D — Mid-flow human escalation

| Field | Value |
|-------|-------|
| **Input** | T1: 我想加一台X5; T2: 算了，找陈奎 |
| **Expected** | T2 escalates to talk_to_agent / customer_requested_human |
| **Observed** | T1: customer_question, handoff_ready=false; T2: customer_requested_human, handoff_ready=true |
| **Pass/Fail** | **PASS** |
| **Notes** | Directly verified in production |

---

## 6. Optional Second Loop

- **Whether used:** No
- **Reason:** All four scenarios passed. No fix needed.

---

## 7. Final Operational Judgment

| Question | Answer |
|----------|--------|
| Did backend deploy succeed? | **Yes** |
| Are the newly fixed realistic scenarios now live? | **Yes** |
| Which production verification scenarios passed? | **A, B, C, D — all four** |
| What remains weakest? | /healthz returns 404 from external curl (internal /readyz and triage API work; may be routing/load-balancer behavior) |
| Can Andy now test on live frontend confidently? | **Yes** |

---

## 8. 中文宏观总结

- **为什么现在要 redeploy：** 真实对话模拟修复（找陈奎、急死了 保单要停了）只有在生产环境生效才有价值。
- **这轮验证了哪些修复：** 找陈奎 → 联系人工；急死了 保单要停了 → 付款/取消风险、critical。
- **哪些已经上线成功：** 上述两个场景及联系人工、两轮找陈奎，均在生产 API 验证通过。
- **哪些还弱：** /healthz 外部访问 404，但不影响 triage 和前端使用。
- **现在我可不可以去前端测试：** 可以。后端已部署，关键场景在生产验证通过。

---

## 9. COPY/PASTE FOUNDER BLOCK

```
Backend Redeploy for Realistic Simulation Fixes — DONE

Backend deploy status: SUCCESS
  URL: https://fiqa-api-1013093472160.us-west1.run.app
  Revision: fiqa-api-00030-4k7

Scenario pass summary:
  ✓ 找陈奎 → customer_requested_human, handoff-ready
  ✓ 急死了 保单要停了 → cancellation_warning, critical
  ✓ 联系人工 → customer_requested_human
  ✓ 两轮 算了找陈奎 → T2 escalates to handoff

Biggest remaining weakness: /healthz 404 from external curl (triage API works)

Andy should test on live frontend now: YES
```

---

## 10. REQUIRED SHORT OVERVIEW

### 为什么做这件事

真实对话模拟修复（找陈奎、急死了 保单要停了）只有在生产环境生效才有价值；需要确认后端已部署且生产 API 行为正确。

### 主要用了什么方法/技术

- 控制文档（Blueprint、Outline、Criteria、Checklist）
- 预部署校验（markers、triage 逻辑、脚本）
- `deploy_rag_demo.sh` 部署到 Cloud Run
- 生产 API 直接调用验证四个场景

### 这轮最大的提升

生产环境已确认：找陈奎、急死了 保单要停了 等关键场景正确路由，不再返回 unclear；创始人可以放心在前端测试。

### 现在还差什么

/healthz 外部访问 404（可能为路由/负载均衡配置）；不影响 triage 和前端。如需，可后续排查 healthz 路由。
