# Stuck Case — 2 Minute Playbook V1

**When:** a customer or broker says「这个案件卡住了」.
**Goal:** answer *where it is stuck* and *what to do next* in under two minutes, without reading logs.

---

## The one call

```bash
curl -s "$BASE_URL/api/inbox/support/case-head/$CASE_ID" \
  -H "X-Unified-Intake-Support-Key: $UNIFIED_INTAKE_SUPPORT_API_KEY" \
  -H "X-Org-Id: $OFFICE_ID" | jq .support_diagnosis
```

- `X-Unified-Intake-Support-Key` — only needed when the deployment configures one.
- `X-Org-Id` — only needed when office ownership enforcement is on. Send the office that owns the case.
- Read-only. Calling it never changes the case, never sends the customer anything.

---

## The four lines to read

| Read this | It tells you |
|-----------|--------------|
| `status` | Where the case is stuck |
| `next_support_action_zh` | What to do next, in one sentence |
| `last_success` | The last thing that actually worked |
| `blocker` | The specific open item, when there is one |

---

## What each status means

| `status` | Meaning | Your next move |
|----------|---------|----------------|
| `start_claim_degraded` | Claim saved, but a follow-up write failed and is still unrepaired | Redo the missing step with the customer (policy context or accident story), then re-run this call |
| `blocked_by_open_request_more` | An open Request More is waiting on the customer | Chase the items in `blocker.open_request.unresolved_labels` |
| `waiting_office` | The ball is with the broker/office | Open the broker workbench; often it just needs「已核对补充资料」or「确认资料已齐」 |
| `story_confirmation_incomplete` | Claim exists but the customer never confirmed the accident story | Ask the customer to finish story confirmation |
| `ready_for_office_accept` | Nothing missing | Tell the broker to click「确认资料已齐」 |
| `waiting_customer` | Waiting on the customer | Confirm what was last asked of them |
| `closed_no_action` | Case is closed History | Nothing to unstick; open a new case if needed |
| `unknown` | No deterministic blocker found | **Only now** open the broker workbench, then logs |

---

## Two useful extras

- `signals.accident_story.used_fallback: true` — the AI draft came from the fallback path. The story may read poorly even when the case is not stuck. Worth a human read.
- `signals.start_claim.degraded_signal_seen: true` with `degraded: false` — a Start Claim write once failed but has since been repaired. Historical, not actionable.

---

## Order of evidence

1. `support_diagnosis` — deterministic business state. **First-line truth.**
2. Broker workbench — what the broker actually sees.
3. Logs / LangSmith — **second-line evidence only**, for *why* something failed, never for *what* the state is.

---

*Endpoint:* `GET /api/inbox/support/case-head/{case_id}`
*Logic:* `services/fiqa_api/inbox_triage/support_case_diagnosis.py` (deterministic, no LLM)
*Tests:* `tests/test_pilot_reliability_support_case_head.py`
