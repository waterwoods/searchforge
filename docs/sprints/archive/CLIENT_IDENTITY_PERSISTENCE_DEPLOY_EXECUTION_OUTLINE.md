# Execution Outline: Client Identity Persistence Deploy

| Step | Action | Exit condition |
|------|--------|----------------|
| 1 | Create control docs | Blueprint, Outline, Criteria, Checklist |
| 2 | Pre-deploy validation | Inspect code, run guardrail + tests + npm build |
| 3 | Backend deploy | `bash scripts/deploy_rag_demo.sh` → success |
| 4 | Frontend deploy | `cd ui && vercel --prod` → success |
| 5 | Post-deploy verification | Scenarios A, B, C on production |
| 6 | Optional second loop | One small fix only if needed |
| 7 | Final judgment | Report + founder block |

## Stop Conditions

- Any validation script fails → stop, explain blocker
- Deploy fails → stop, capture error
- Do NOT deploy if pre-deploy validation fails
