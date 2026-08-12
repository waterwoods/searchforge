# AI Request More Drafting V1 — Cloud QA validation with the real LLM

**Date:** 2026-08-12 (UTC) · **Verdict:** PASS · **Production touched:** NO

| Item | Value |
|------|-------|
| Branch | `strategy/founder-review-2026-08-05` |
| Baseline commit under test | `54a47a1`; validated revision runs `af14786` |
| QA service | `fiqa-api-qa` (`us-west1`, project `optimal-disk-472305-e2`) |
| QA revision | `fiqa-api-qa-00078-vjq` @ 100% traffic |
| QA base URL | `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| Posture | product-only, `STRICT_PG_ONLY` on `caseiq-qa`, `intake_path_ready=true` |
| Flags (QA only) | `REQUEST_MORE_ASSISTANT_ENABLED=1`, `REQUEST_MORE_ASSISTANT_LLM=1`, `REQUEST_MORE_ASSISTANT_TIMEOUT_SECONDS=20` |
| Model actually used | `openai / gpt-4o-mini`, 1.2–2.4 s per draft |

Reproduce:

```bash
set -a && source .env.cloudrun.qa && set +a
PYTHONPATH=. python3 scripts/qa_validate_request_more_ai_drafting.py       # 71 checks
PYTHONPATH=. python3 scripts/qa_validate_request_more_ai_failure_modes.py  # 16 checks
```

Synthetic cases only (`is_test=true`, no real customer PII), built through the
existing `POST /api/inbox/claims` + `fact-status` broker commands.

## Results

| Scenario | Deterministic missing set | Result |
|----------|---------------------------|--------|
| A — everything confirmed except VIN | `["vin"]` | real AI draft, `used_fallback=false`, guardrail `passed` |
| B — VIN + insurance card missing | `["vin","policy_or_insurance_card"]` | real AI draft, both represented, nothing extra |
| C — nothing missing | `[]` | `drafting_available=false`, `无需补充`, no model call (289 ms) |
| Broker chose office template | `["vin"]` | deterministic template, not counted as an AI failure |

Real Case A draft (sanitized synthetic case):

```text
您好！为了继续处理您的索赔，我们还需要您提供以下信息：
1. 车辆 VIN
请您方便时补充上传，谢谢！
```

Real Case B draft:

```text
您好！为了继续处理您的索赔，我们还需要您提供以下信息：
1. 车辆 VIN
2. 保险卡照片
请您方便时补充上传，谢谢！
```

Neither draft re-asks for anything already authoritative (insurance card, policy,
accident time, accident location, injury status, vehicle), invents facts, or
mentions coverage, liability, fault, payment, or approval.

## Failure modes proven on the live QA service

Kill switches were flipped on `fiqa-api-qa` only, then restored.

| Injected failure | Observed |
|------------------|----------|
| Unresolvable model name | `used_fallback=true`, `provider_error:NotFoundError`, office template returned, broker not blocked |
| `REQUEST_MORE_ASSISTANT_ENABLED=0` | `assistant_disabled`, deterministic template, Request More still usable |
| `REQUEST_MORE_ASSISTANT_LLM=0` | `llm_disabled`, deterministic template |
| Restore | real AI path healthy again |

Adds-item / omits-item / malformed JSON / timeout / forbidden language /
unsupported detail are covered by `tests/test_request_more_ai_drafting.py`.

## Read-only and authority proof

Requesting a draft left `aggregate_version`, lifecycle, known facts, and the
checklist byte-identical, created no request draft, no Request More, and no
customer access. Sending afterwards used the normal broker commands: one
Request More with one item carrying the broker's edit, retry replayed the same
`request_id`, and drafting is refused while a Request More is open
(`active_request_more_exists`).

## Logs

Zero ERROR/exception lines in the test window. Telemetry line
`request_more_ai_draft {...}` carries item count, AI/fallback, guardrail
outcome, model, and latency — and no case facts, draft text, or customer text.
Token/cost metadata is not captured; drafts are a few hundred tokens on
`gpt-4o-mini`, so cost is negligible at pilot volume.

**Pre-existing observation (not fixed here):** startup logs
`OPENAI_API_KEY loaded: sk-pro**** (length=164)` in `app_main`. Masked, but it
discloses the key prefix and exact length; consider trimming in shared startup
logging.

## Defects found and fixed during this validation

1. **Assistant flags could not reach any Cloud Run service.** `deploy_cloud_run_core.sh`
   passes an explicit env allowlist, so `REQUEST_MORE_ASSISTANT_*` was silently
   dropped and QA came up with the LLM off. Added the passthrough block plus
   `configs/cloud_qa.env.example` entries.
2. **Two-item drafts always fell back.** The model returned a lead-in only
   ("请您提供以下缺失的信息：") and left the list to the `items` array, so the guardrail
   correctly rejected a message that named nothing. Fixed the contract, not the
   guardrail: the office template now travels to the model as the baseline to
   improve, and the prompt requires `draft_text` to be the complete message.
3. **AI drafts dropped the customer-facing "how to find it" hint.** Blank
   instructions are now backfilled from the office template.
4. **Flag tests inherited the operator's shell.** Assistant env vars are cleared
   per test.
5. **Draft telemetry was invisible in Cloud Logging.** The app formatter drops
   `extra=`; bounded metadata is now rendered into the message.

`GET /api/inbox/support/deployment-manifest` now reports `request_more_assistant`
flag posture so QA/Production drift is visible without reading logs.
