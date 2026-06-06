# Backend Redeploy + Founder Trial — Execution Outline

## Phase A — Control Docs

1. Sprint Blueprint ✓
2. Execution Outline (this doc)
3. Acceptance / Operational Criteria
4. Founder Trial Checklist

## Phase B — Pre-Deploy Validation

1. Inspect `triage.py` — billing clarification, remove vehicle, claim intake, renewal
2. Inspect `markers.json` — 减车, 卖掉了, 报事故, 刚撞了, 续保涨, 账单
3. Inspect `inbox_triage_scenarios.json` — TSH2-BC1, TSH2-BC2, TSH2-CL1, TSH2-RN1, TSH2-RV1
4. Run: `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
5. Run: `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
6. Run: `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py`
7. Run: `PYTHONPATH=. python3 scripts/verify_speed_routing.py`
8. Run: `bash scripts/guardrail_inbox_triage.sh`
9. Run: `bash scripts/unified_intake_smoke_check.sh`

**Blocker rule:** If any fails → stop, explain, do not deploy.

## Phase C — Backend Redeploy

1. Run: `bash scripts/deploy_rag_demo.sh`
2. Capture: success/failure, backend URL, revision, warnings/errors
3. Verify: /healthz, /readyz

## Phase D — Post-Deploy Verification

Call production inbox triage API for each founder scenario:

| Scenario | Input | Expected category | Expected reply contains |
|----------|-------|-------------------|-------------------------|
| A | 账单什么意思 | customer_question | 发我, 帮你看 |
| B | 这个账单我看不懂 | customer_question | 账单, 发我, 帮你看 |
| C | 减车，卖掉了 | customer_question | 拿掉, 卖车, 过户 |
| D | 报事故，刚撞了 | customer_question | 事故, 照片, 报案 |
| E | 续保涨了好多，帮我看看 | customer_question | 保费, 账单, 保单 |

## Phase E — Optional Second Loop

If one small, high-value, low-risk issue → fix and redeploy once. Do NOT broaden scope.

## Phase F — Final Report

- Operational judgment
- 中文宏观总结
- COPY/PASTE FOUNDER BLOCK
- REQUIRED SHORT OVERVIEW
