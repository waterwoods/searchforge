# LangGraph Final Phone QA — Routing Fix (20260804T033002Z)

## Root cause

Latest DIT used scenario `chen_camry_stage2_phone`. On the Founder phone, isolated identity
`hash(wx_openid | chen_camry_stage2_phone)` resumed Stage 2 Active Case `case_09ad6254614a`
(CLM-0036) with Santa Ana / 1pm / 已有保单资料，客户已确认 — Case Status, not Start Claim.

## Fix

New isolated scenario/fixture: `langgraph_final_phone_qa` (unique `wx_qaiso_*`, no prior Active Case).

| Item | Value |
|------|--------|
| QA revision | `fiqa-api-qa-00055-mxs (code) → scale bump fiqa-api-qa-00056-mwc` |
| New case | `case_d4fe3e5d3b7e` |
| Invite | `dinv_ea83aadda56244d6` |
| Expires PDT | 2026-08-03 10:30 PM PDT |
| First screen | `START_NEW_CLAIM` (proven) |
| Stage 1/2 | Untouched |

## Founder path

See local `artifacts/langgraph_final_phone_handoff/PHONE_HANDOFF.json` (dit not committed).

DevTools: compile mode **LangGraph Final Phone QA** → clear cache → Preview.
