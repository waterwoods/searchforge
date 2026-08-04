# Accident Story — Stop & Rollback Card V1

## Stop immediately if
- unknown injury becomes **no**
- unconfirmed AI shown as customer fact
- raw PII in new traces
- >3 follow-up questions
- Claim lifecycle mutated by assistant
- fallback / manual intake unusable

## Kill switch (Cloud QA only)
```bash
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars ACCIDENT_STORY_ASSISTANT_ENABLED=0 \
  --min-instances 0 --max-instances 2
```

## Confirm
Propose returns manual intake; Start Claim still works.

## Do not
Touch Production or waterwoods.
