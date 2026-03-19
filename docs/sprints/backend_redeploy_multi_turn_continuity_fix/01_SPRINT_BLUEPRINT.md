# Backend Redeploy for Multi-Turn Continuity Fix — Sprint Blueprint

## Why This Redeploy Is Needed Now

The latest audit found a critical continuity bug: Customer Entry behaved as one-shot intake + immediate handoff, not true multi-turn. The code repair has been implemented locally:

- First message now uses `triage_conversation(text, [])` (not `triage_message` + forced `handoff_ready`)
- First message no longer forces `handoff_ready=true`
- Persistence only when `handoff_ready=true`
- Guardrails and tests added

**Production backend has not yet been updated.** Until redeployed, production still behaves like single-turn intake.

## What Must Be Live

1. **First message path:** `triage_conversation` for all messages (including first turn with `turns=[]`)
2. **No forced handoff:** `handoff_ready` derived from `_should_handoff()` / collection thresholds
3. **First-turn continuity:** Quote/add-car, payment, missing-doc stay in thread when more info needed
4. **Persistence timing:** Case persisted only when `handoff_ready=true`, not prematurely

## What Counts as Success

- Backend redeploy completes successfully
- `/healthz` and `/readyz` return OK in production
- First-turn quote/add-car example returns `handoff_ready=false` and asks for next info
- First-turn payment example returns `handoff_ready=false` when more info needed
- First-turn missing-doc example stays in thread when item/sent status unclear
- Founder can demonstrate continuous intake on Vercel frontend

## Scope Guardrail

- **In scope:** Redeploy backend with continuity fix; verify production truth
- **Out of scope:** New features, frontend polish, unrelated changes
