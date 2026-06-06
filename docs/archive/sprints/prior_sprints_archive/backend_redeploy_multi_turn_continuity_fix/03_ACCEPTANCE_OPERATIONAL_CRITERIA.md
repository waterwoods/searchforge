# Backend Redeploy for Multi-Turn Continuity Fix — Acceptance / Operational Criteria

## Successful Redeploy

- `deploy_rag_demo.sh` completes without error
- Cloud Run service returns 200 for `/healthz`
- Cloud Run service returns 200 for `/readyz` (or acceptable not_ready if Qdrant cold)
- Backend URL is reachable from public internet

## Successful Production Continuity Verification

- **Quote/add-car first turn:** "我才买了一个2026年的丰田花冠，大约半年的保费是多少？" → `handoff_ready=false`, asks for zip or next missing field
- **Payment first turn:** "付款失败了" → `handoff_ready=false`, payment-specific reply, asks for notice/screenshot
- **Missing-doc first turn:** "我上周已经发过了，怎么还在追材料？" → acknowledge first, `handoff_ready=false` when more info needed (or True only when truly appropriate)

## Acceptable Risk

- `/readyz` may be not_ready if Qdrant cold (DEMO_MODE can make intake path ready without Qdrant)
- LLM path may differ slightly from rule-based; continuity logic must hold for both
- Frontend may need separate verification; this sprint is backend-only

## Blockers for Founder Inspection

- Deployment failure
- `/healthz` returns non-200
- First-turn continuity examples still return `handoff_ready=true` when more info needed
- Production behavior still matches one-shot intake model
