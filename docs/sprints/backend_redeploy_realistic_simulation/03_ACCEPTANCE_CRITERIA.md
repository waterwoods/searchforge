# Backend Redeploy — Acceptance / Operational Criteria

## Pre-Deploy

| Criterion | Pass |
|-----------|------|
| "找陈奎" in talk_to_agent markers or triage fallback | |
| policy_stop alone routes to cancellation_warning, critical | |
| realistic_conversation_simulation_pack.json exists | |
| run_realistic_conversation_pack.py exists | |
| run_realistic_conversation_pack.py passes (RC-S5, RC-S6) | |
| run_inbox_triage_scenarios.py passes | |
| guardrail_inbox_triage.sh passes | |
| No blocker before deploy | |

## Deploy

| Criterion | Pass |
|-----------|------|
| deploy_rag_demo.sh completes | |
| /healthz returns 200 | |
| /readyz returns (ok or known acceptable) | |

## Post-Deploy

| Scenario | Input | Expected | Pass |
|----------|-------|----------|------|
| A | 找陈奎 | customer_requested_human, NOT unclear | |
| B | 急死了 保单要停了 | cancellation_warning, critical, NOT unclear | |
| C | 联系人工 | customer_requested_human, handoff-ready | |
| D | 我想加一台X5 → 算了，找陈奎 | T2 escalates to talk_to_agent | |

## Operational Judgment

- Backend live: Y/N
- New fixes live: Y/N
- Andy can test on frontend: Y/N
