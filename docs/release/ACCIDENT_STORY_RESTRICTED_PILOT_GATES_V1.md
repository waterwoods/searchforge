# Accident Story Assistant — Restricted Pilot Gates V1

**Scope:** Cloud QA / restricted office pilot only  
**Does not authorize:** Production deploy, waterwoods retarget, or “Production Ready”

## Classification vocabulary

| Label | Meaning |
|-------|---------|
| DEMO READY | Safe to show founders/demo; flags + fallback proven |
| PILOT READY WITH RESTRICTIONS | Restricted office pilot allowed under runbook |
| BLOCKED | Do not pilot |

Never use **Production Ready** from this document alone.

---

## Gates (pass/fail)

| # | Gate | Pass criteria | Status |
|---|------|---------------|--------|
| 1 | Golden evaluation | `20/20` on `accident_story_v1` | PASS |
| 2 | PII / redaction | Trace meta ⊆ allow-list; no raw story in telemetry | PASS (online marker check; LangGraph auto-trace suppressed) |
| 3 | Max questions | ≤3 follow-ups always | PASS |
| 4 | Unknown-injury safety | unknown never coerced to no | PASS |
| 5 | Conflict handling | Conflicts surfaced; injury stays unknown | PASS |
| 6 | Fallback success | Timeout / invalid / exception → manual intake usable | PASS |
| 7 | Timeout behavior | Bounded timeout + calm customer copy | PASS |
| 8 | Tracing independence | Tracing off / failure does not break intake | PASS |
| 9 | Feature disable | `ACCIDENT_STORY_ASSISTANT_ENABLED=0` → manual path | PASS |
| 10 | Regression | Stage1/2 Guided Intake + golden + pilot-safety tests green | PASS |
| 11 | Rollback readiness | Documented kill switch + QA scale restore | PASS |

---

## Resource limits (chosen)

| Limit | Value | Why |
|-------|-------|-----|
| Max story chars | 2000 (env override ≤8000) | Bound model/input cost; matches normalize clamp |
| Max follow-up questions | 3 | Product contract |
| LLM timeout | 8s (0.5–30) | Keep Start Claim responsive |
| LLM retries | 1 (0–2) | Avoid unbounded loops |
| Max payload | 32 KiB (≤128 KiB) | Reject oversized posts safely |
| Idempotency | command/idempotency key cache | Duplicate-safe |

---

## Emergency disable

```bash
# Cloud QA only — set env then update service (example)
gcloud run services update fiqa-api-qa --region us-west1 \
  --update-env-vars ACCIDENT_STORY_ASSISTANT_ENABLED=0
```

Confirm: propose returns `manual_intake_required=true`, normal Start Claim still works.  
Restore QA scale after ops: minScale=0 / maxScale=2.

---

## Final classification (this PR)

**PILOT READY WITH RESTRICTIONS** — when gates 1–11 PASS on QA with LLM default OFF, tracing optional, Guided Intake Founder PASS already frozen.
