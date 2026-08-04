# Chen Office — Restricted Pilot Activation Prep (UNEXECUTED)

**Status:** Prepared only — **do not execute** until Founder marks **GO**.  
**Generated:** 2026-08-04T22:05:35Z  
**Target:** Cloud QA `fiqa-api-qa` only. Production / waterwoods forbidden.

## 1. Preconditions
- [ ] Founder decision = GO on `docs/founder/ACCIDENT_STORY_FIVE_CASE_GO_NO_GO_V1.md`
- [ ] Consent copy ready for customers
- [ ] Support owner assigned
- [ ] Clean LangSmith project exists: `accident-story-restricted-pilot-v1`

## 2. Exact QA-only env activation (do not run until GO)
```bash
# Cloud QA ONLY — replace OFFICE_ID with Founder-approved Chen office id
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars \
ACCIDENT_STORY_ASSISTANT_ENABLED=1,\
ACCIDENT_STORY_LLM=1,\
ACCIDENT_STORY_OFFICE_ALLOWLIST=<CHEN_OFFICE_ID>,\
ACCIDENT_STORY_LANGSMITH_TRACING=1,\
ACCIDENT_STORY_LANGSMITH_PROJECT=accident-story-restricted-pilot-v1,\
ACCIDENT_STORY_LLM_TIMEOUT_SECONDS=20 \
  --min-instances 0 --max-instances 2
```

If LangSmith keys are not on QA, either:
- bind approved secrets to QA and set tracing=1, **or**
- leave `ACCIDENT_STORY_LANGSMITH_TRACING=0` (intake remains safe; traces no-op)

## 3. Five-case control
- Hard process limit: **5 cases**, then pause and review scorecard/metrics
- Log each case in Issue Log / Daily Review checklist (no raw PII)

## 4. Consent
Use `docs/pilot/ACCIDENT_STORY_CUSTOMER_CONSENT_COPY_V1.md` before AI-assisted intake.

## 5. Daily metrics command
```bash
curl -sS -H "X-Unified-Intake-Support-Key: $UNIFIED_INTAKE_SUPPORT_API_KEY" \
  "$QA_URL/api/inbox/support/deployment-manifest" | jq '.accident_story_assistant, .accident_story_pilot_metrics_window'
```

## 6. Emergency kill switch
```bash
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars ACCIDENT_STORY_ASSISTANT_ENABLED=0 \
  --min-instances 0 --max-instances 2
```

## 7. Rollback
Redeploy last known-good QA revision **or** kill switch. Restore minScale=0 / maxScale=2. Never Production/waterwoods.

## 8. Verify manual intake still available
With assistant disabled **or** non-allowlisted office: propose returns manual path; Start Claim still completes without AI.

## 9. Historical LangSmith debt (non-blocking for GO if synthetic)
Optional cleanup: delete 8 immutable synthetic bare-node runs in the **old** lab project (id prefixes in `docs/evidence/pilot-freeze-final/langsmith-immutable-8/IMMUTABLE_8_CLASSIFICATION.json`). New pilot traces use the clean project only.
