# Accident Story — Founder Five-Case Go/No-Go (1 page)

**Date:** 2026-08-04T22:05:35Z  
**Ask:** Authorize up to **five** restricted pilot cases — or hold/disable.  
**Not Production Ready.**

## Finished
- Guided Intake Founder PASS (frozen)
- LangSmith golden evals 20/20 + pilot safety + QA canary 20/20 live synthetic
- Five-case office rehearsal PASS (local + Cloud QA)
- Broker Brief shows 客户原始描述 / AI整理草稿 / 客户已确认事实 + AI回退 visibility
- Kill switch, durable Postgres metrics, clean LangSmith project ready

## Validated
- Synthetic QA only: ≤3 questions, unknown≠no, fallback usable, lifecycle untouched
- New traces redacted; clean project `accident-story-restricted-pilot-v1` starts clean

## Not proven
- Real-customer accuracy
- Multi-office scale
- Production deploy

## Pilot box
- **Max cases:** 5 then pause for metrics review  
- **Eligible:** Founder-approved Chen office allowlist on **Cloud QA only** (prep docs; not auto-activated)  
- **Consent:** use `docs/pilot/ACCIDENT_STORY_CUSTOMER_CONSENT_COPY_V1.md`  
- **AI does not:** coverage, liability, claim submit/close, payment  
- **Broker must:** treat only **客户已确认事实** as office truth  

## Success thresholds
0 unknown→no · 0 unconfirmed-as-fact · 0 new PII traces · ≤3 questions · ≥4/5 complete without tech support · next action clear every case

## Stop conditions
Any threshold fail, fallback broken, or lifecycle mutation → kill switch + stop

## Kill switch / rollback (QA only)
```bash
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars ACCIDENT_STORY_ASSISTANT_ENABLED=0 \
  --min-instances 0 --max-instances 2
```
Redeploy prior QA revision if needed. **Do not touch Production / waterwoods.**

## Support owner
Founder / operator on Cloud QA. Tickets: support ref only — never raw story/phone/OpenID/dit/photo.

## Metrics after each case
`proposals_created`, fallbacks, timeouts, invalid, question count, unknown-injury violations, latency/p95, completion-after-fallback — via support deployment-manifest or  
`PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py --since <ISO> --until <ISO> --json`

## Decision (pick one)
- **GO** — authorize up to five real cases under the activation sheet (QA-only)
- **HOLD** — demo only; do not activate allowlist/LLM for Chen
- **NO-GO** — keep/disable AI (`ACCIDENT_STORY_ASSISTANT_ENABLED=0`) and stop
