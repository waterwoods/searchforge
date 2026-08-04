# Accident Story Pilot — Support Runbook

**Audience:** Founder / operator on Cloud QA  
**Product:** Bounded Accident Story Assistant (guided intake)  
**Never:** copy raw stories, phones, OpenIDs, dit tokens, photo URLs into tickets or traces

---

## 1. Detect a failure

Symptoms:

- Customer sees calm copy: “AI暂时无法整理…” / “请继续填写…”
- Support metrics: `fallbacks`, `provider_timeouts`, `invalid_output_failures` rising
- Manifest: `GET /api/inbox/support/deployment-manifest` → `accident_story_assistant`

Commands:

```bash
PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py
curl -sS -H "X-Unified-Intake-Support-Key: $UNIFIED_INTAKE_SUPPORT_API_KEY" \
  "$QA_URL/api/inbox/support/deployment-manifest" | jq '.accident_story_assistant'
```

---

## 2. Classify

| Category | Meaning |
|----------|---------|
| `timeout` | Provider slow/unavailable |
| `invalid_json` / `hallucinated_fields` | Bad model output |
| `disabled` | Kill switch or office allowlist |
| `missing_credentials` | LLM key absent (expected when LLM off) |
| `tracing_failure` | LangSmith issue — intake must continue |
| `internal_exception` | Unexpected server error → manual fallback |

---

## 3. Disable AI safely (kill switch)

```bash
# QA only
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars ACCIDENT_STORY_ASSISTANT_ENABLED=0
```

Optional finer switches:

- `ACCIDENT_STORY_LLM=0` — disable LLM merge (default)
- `ACCIDENT_STORY_LANGSMITH_TRACING=0` — disable tracing
- `ACCIDENT_STORY_OFFICE_ALLOWLIST=office_a,office_b` — restrict offices

**Disabling AI must not disable normal Start Claim / Cap2 intake.**

---

## 4. Confirm fallback works

1. Propose with assistant disabled → `manual_intake_required=true`, original `raw_story` preserved  
2. Complete Start Claim with time/location/injury manually  
3. Lifecycle unchanged (no auto-submit/close)

---

## 5. Inspect non-sensitive metrics

```bash
PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py --json
```

Fields: created/accepted/edited/rejected/fallbacks/timeouts/latency/question counts.  
No raw stories.

---

## 6. Roll back QA

1. Re-deploy last known good QA revision **or** set kill switch  
2. Restore scale: **minScale=0 / maxScale=2**  
3. Do **not** touch Production or waterwoods

---

## 7. When to contact the Founder

- Product-policy change (e.g. enable LLM in pilot)
- Credential provisioning for online LangSmith UI review
- Suspected PII leak in telemetry
- Need to expand office allowlist beyond approved pilots

---

## 8. Never copy into tickets/traces

- Raw accident descriptions
- Customer names / phones
- OpenIDs / session secrets
- Invite `dit` tokens
- Photo paths / signed URLs
- Stack traces with request bodies
