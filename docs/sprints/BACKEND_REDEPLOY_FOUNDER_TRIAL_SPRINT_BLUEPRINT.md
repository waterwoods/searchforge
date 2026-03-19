# Backend Redeploy + Founder Real Trial Sprint — Blueprint

**Sprint name:** Backend Redeploy + Founder Real Trial Sprint  
**Target budget:** 20–45 minutes  
**Execution mode:** Structured inspect → validate → deploy → verify → summarize

## Mission

Deploy the latest Top Scenarios Hardening Phase 2 backend changes, then verify the founder's real trial scenarios on the live system.

## Scope (In)

- Confirm scenario hardening changes in code
- Redeploy backend to Cloud Run (production)
- Verify production truth with exact founder trial scenarios
- Output founder test checklist with expected behavior

## Scope (Out)

- No new feature scope
- No changes to unrelated product areas
- No frontend changes

## Key Files

| File | Purpose |
|------|---------|
| `services/fiqa_api/inbox_triage/triage.py` | Billing clarification, remove vehicle, claim intake, renewal logic |
| `configs/industries/insurance/markers.json` | Intent markers (payment, remove_vehicle, claim_intake, premium_review) |
| `configs/inbox_triage_scenarios.json` | TSH2 scenarios (BC1, BC2, CL1, RN1, RV1) |
| `scripts/deploy_rag_demo.sh` | Production deploy path |

## Hardened Scenarios (Phase 2)

1. **Billing clarification** — 账单什么意思, 这个账单我看不懂 → customer_question, NOT payment_lapse_expiration
2. **Remove vehicle shorthand** — 减车，卖掉了 → remove_vehicle handling
3. **Claim first notice** — 报事故，刚撞了 → claim intake guidance
4. **Renewal increase** — 续保涨了好多，帮我看看 → premium_review, NOT payment failure

## Success Criteria

- Backend deploy succeeds
- All 5 founder trial scenarios behave as expected in production
- Founder can manually test on live frontend with confidence
