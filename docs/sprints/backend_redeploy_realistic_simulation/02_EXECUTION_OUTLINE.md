# Backend Redeploy — Execution Outline

## Phase A — Control Docs
- [x] Sprint Blueprint
- [x] Execution Outline
- [x] Acceptance Criteria
- [x] Founder Verification Checklist

## Phase B — Pre-Deploy Validation
1. Inspect: markers.json, triage.py, realistic_conversation_simulation_pack.json, run_realistic_conversation_pack.py
2. Confirm: "找陈奎" in talk_to_agent; policy_stop alone → cancellation_warning
3. Run validation scripts (all must pass or document blocker)

## Phase C — Backend Deploy
- `bash scripts/deploy_rag_demo.sh`
- Capture: success/failure, URL, revision, warnings

## Phase D — Post-Deploy Verification
- Scenario A: 找陈奎 → talk_to_agent / customer_requested_human
- Scenario B: 急死了 保单要停了 → cancellation_warning, critical
- Scenario C: 联系人工 → handoff-ready
- Scenario D (optional): 我想加一台X5 → 算了，找陈奎 → escalation

## Phase E — Optional Second Loop
- One small fix only if high-value, low-risk

## Phase F — Final Report
- Operational judgment
- Founder block
- 中文宏观总结
