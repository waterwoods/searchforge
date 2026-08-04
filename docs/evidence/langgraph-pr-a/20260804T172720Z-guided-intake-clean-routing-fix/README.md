# Guided Intake Clean Phone QA — Routing Fix (20260804T172720Z)

## Root cause

Morning DIT reused scenario `langgraph_final_phone_qa`. Founder phone isolated identity
`hash(wx_openid | langgraph_final_phone_qa)` already had Active Case `case_f31c3604bb70`
(CLM-0042) with Santa Ana / 昨天下午1点 / Case Status — created `2026-08-04T03:53:02Z`.

Dit redeem succeeded; Customer Context correctly resumed that isolated Active Case.
Not Stage 1/2 mutation. Warm page-stack can compound the confusion.

## Fix

1. New isolated scenario `guided_intake_clean_phone_qa` (unique `wx_qaiso_*`).
2. App.onShow warm Preview `dit=` reLaunch so Case Status stack cannot ignore a new QR.
3. QA deploy `fiqa-api-qa-00059-g8x` only. Production / waterwoods untouched.

| Item | Value |
|------|--------|
| QA revision | `fiqa-api-qa-00059-g8x` |
| Invite | `dinv_c8b845a45f4f48da` |
| Expires PDT | 2026-08-04 02:27 PM PDT |
| First screen | `START_NEW_CLAIM` (proven) |
| Prior CLM-0042 | Preserved |
| Stage 1/2 | Untouched |

## Founder path

1. Fully close/remove the Mini Program from WeChat recent apps.
2. DevTools compile **Guided Intake Clean Phone QA** → clear cache → Preview.
3. Scan the new QR only.

## Founder result

**PASS** (2026-08-04). Closeout: `docs/evidence/langgraph-pr-a/GUIDED_INTAKE_FOUNDER_PASS_CLOSEOUT.md`.
