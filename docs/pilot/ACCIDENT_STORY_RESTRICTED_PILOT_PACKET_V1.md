# Accident Story — Restricted Pilot Packet V1

**Status:** QA CANARY PASS — PILOT READY WITH RESTRICTIONS  
**Date:** 2026-08-04T19:52:16Z  
**Support owner:** Founder / operator on Cloud QA (`fiqa-api-qa`)

## Eligible office / scenario

- **Office allowlist:** `qa_canary_synth` only (expand only by explicit Founder decision)
- **Environment:** Cloud QA (`fiqa-api-qa`) — never Production / waterwoods
- **Initial case limit:** **5** synthetic or Founder-approved pilot cases, then pause for metrics review

## Feature flags (server-side)

| Flag | Pilot value |
|------|-------------|
| `ACCIDENT_STORY_ASSISTANT_ENABLED` | `1` |
| `ACCIDENT_STORY_LLM` | `1` (allowlisted office only) |
| `ACCIDENT_STORY_OFFICE_ALLOWLIST` | `qa_canary_synth` |
| `ACCIDENT_STORY_LANGSMITH_TRACING` | `0` on QA unless keys approved |
| Deterministic fallback | always on |

## Kill-switch procedure

```bash
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars ACCIDENT_STORY_ASSISTANT_ENABLED=0 \
  --min-instances 0 --max-instances 2
```

Confirm propose returns `manual_intake_required=true` for allowlisted office; normal Start Claim still works.

## Metrics reviewed after each case

```bash
# Support manifest (non-sensitive)
curl -H "X-Unified-Intake-Support-Key: $UNIFIED_INTAKE_SUPPORT_API_KEY" \
  "$QA_URL/api/inbox/support/deployment-manifest"
# Local exporter against durable store when DB URL available
PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py --since <ISO> --until <ISO> --json
```

Review: created / accepted / edited / rejected / fallbacks / timeouts / invalid / latency / question count / unknown-injury violations.

## Customer-consent language (suggested)

“我们会用辅助整理帮助确认事故时间、地点和是否受伤。整理结果需您确认后才生效。您也可以直接手动填写。描述内容仅用于办理本次理赔协助。”

## Prohibited in support tickets / traces

Raw accident stories, phones, OpenIDs, invite `dit` tokens, photo URLs, customer names, stack traces with request bodies.

## Stop conditions

- Any unknown-injury → no  
- Any raw PII in new traces  
- Fallback path unusable  
- >3 follow-up questions  
- Unexpected Claim lifecycle mutation by assistant  
- p95 latency consistently >15s on propose

## Rollback procedure

1. Kill switch `ACCIDENT_STORY_ASSISTANT_ENABLED=0` **or** redeploy prior QA revision  
2. Restore scale minScale=0 / maxScale=2  
3. Do not touch Production or waterwoods  

## Second-office readiness checklist

- [ ] Founder approves office id addition to allowlist  
- [ ] Five-case review PASS on first office  
- [ ] Durable metrics reviewed  
- [ ] Kill switch drill completed  
- [ ] No open P0 from stop conditions  
- [ ] Support runbook owner confirmed (`docs/runbooks/ACCIDENT_STORY_PILOT_SUPPORT_RUNBOOK.md`)
