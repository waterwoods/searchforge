# Acceptance / Operational Criteria

## Pre-Deploy

- [ ] `case_store` has `client_id` persistence (save_case, append_follow_up_message, _normalize_case)
- [ ] `inbox_triage` route uses `case.client_id` for append
- [ ] Frontend append passes `currentCase.client_id ?? clientId`
- [ ] `guardrail_inbox_triage.sh` passes
- [ ] `run_multi_turn_simulations.py` passes
- [ ] `verify_inbox_case_persistence.py` passes
- [ ] `test_client_identity_append.py` passes
- [ ] `npm run build` succeeds

## Post-Deploy

- [ ] Backend `/healthz` returns 200
- [ ] Frontend loads at production URL
- [ ] Scenario A: Entry copy differs by client
- [ ] Scenario B: Handoff wording uses demo_broker when `?client=demo_broker`
- [ ] Scenario C: Append to chen_kui case from demo_broker URL uses chen_kui handoff

## Operational

- Andy can run manual broker-style trial on Vercel with confidence
- No CORS errors
- No 500 on triage/append
