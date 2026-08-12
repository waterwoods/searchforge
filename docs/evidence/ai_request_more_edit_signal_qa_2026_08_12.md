# AI Request More pilot signal — Cloud QA evidence (2026-08-12)

**Scope:** QA only. Production untouched.
**Question this capability answers:** when a broker sends an AI-drafted Request
More, did they send the model's wording or rewrite it first?

---

## Posture

| Item | Value |
|------|-------|
| Branch | `strategy/founder-review-2026-08-05` |
| Deployed commit | `e8eb445` |
| QA service / revision | `fiqa-api-qa` / `fiqa-api-qa-00081-mpd` (100% traffic) |
| Approved pilot office | `chen_kui` (single office) |
| `REQUEST_MORE_ASSISTANT_ENABLED` | `1` |
| `REQUEST_MORE_ASSISTANT_LLM` | `1` |
| `REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST` | `chen_kui` |
| Model actually used | `openai` / `gpt-4o-mini` |
| Production revision | `fiqa-api-00233-scz` (2026-07-19, commit `2eacd9e3c`) — unchanged, no assistant env vars |

---

## Signal definition

`draft_edited_before_send` compares two SHA-256 digests of the **normalized
customer-facing fields** (`label`, `instructions`, keyed by `field_key`,
order-independent):

- the digest issued with the AI draft (`ai_draft_receipt.draft_signature`)
- the digest of the draft the broker actually sent

Normalization folds NFKC width, zero-width characters, and whitespace runs, so
reflowing a textarea is not an edit while any wording change is.

`draft_edited_before_send` is only claimed when the model produced the wording.
A broker-chosen template or a fallback template reports `ai_used=false` and
leaves the field `null`, so a deterministic send can never inflate AI adoption.

Durable storage: the existing send events (`broker_request_more_created` in
`claim_slice1_events`, `request_sent` in `claim_intake_events`) carry the
signal in their `evidence` payload, plus `claim_request_drafts.ai_provenance`.
No new analytics platform. Digests and model metadata only — no draft text.

Read-back: `GET /api/inbox/support/request-more-ai-signal/{case_id}` (support-key gated).

---

## Synthetic pilot result — `scripts/qa_pilot_request_more_edit_signal.py`

**53 / 53 checks PASS** against the deployed service with the real LLM.

| Case | Missing set | Path | `ai_used` | `used_fallback` | `draft_edited_before_send` |
|------|-------------|------|-----------|-----------------|-----------------------------|
| A | `vin` | real AI draft, sent unchanged | `true` | `false` | **`false`** |
| B | `vin` | real AI draft, one sentence rewritten | `true` | `false` | **`true`** |
| C | `vin`, `policy_or_insurance_card` | office template chosen | `false` | `false` | `null` (`ai_not_adopted`) |

Every case also proved: assist did not bump the case version, exactly one
stored send signal, stored signal matches the send response, request/command
linkage present, `pilot_office_id = chen_kui`, and no draft wording in storage.

### Allowlist gating (live)

| Office | `draft_used_ai` | `authority` | `fallback_reason` |
|--------|-----------------|-------------|-------------------|
| `chen_kui` | `true` | `ai_draft` | — |
| `office_not_in_pilot` | `false` | `office_template` | `assistant_disabled` |

### SYNTHETIC QA summary — not a real broker metric

```
AI drafts attempted   : 2
AI drafts successful  : 2
fallback sends        : 0
sent unchanged        : 1
sent edited           : 1
synthetic edit rate   : 0.5
```

This is three scripted cases, one of which was rewritten on purpose. It proves
the measurement works; it says nothing about whether real brokers like the
wording.

---

## Regression

- `tests/test_request_more_edit_signal.py` — 26 focused tests, all pass
- `scripts/qa_validate_request_more_ai_drafting.py` — 71 / 71 pass on QA
- `bash scripts/run_deployment_qa_gate.sh` — `READY FOR FOUNDER QA`
- Full local suite: no new failures versus HEAD in an isolated worktree

---

## Defects found and fixed during this work

1. **Allowlist would have disabled drafting for everyone.** The allowlist
   matched the `X-Org-Id` header, which the Workbench never sends. Office is
   now resolved from persisted case ownership, falling back to the
   deployment's client pack.
2. **Column added inside a read-only transaction was rolled back** while the
   process-local READY flag stayed true, so every draft write failed with
   `column "ai_provenance" does not exist`. Fixed with the repo's existing
   `case_ref` pattern: information_schema truth check plus a dedicated
   autocommit connection.
3. **That DDL connection then deadlocked the service.** Running `ALTER TABLE`
   after the caller's transaction had locked the table made both wait on each
   other; `/readyz` and all claim writes hung. Fixed by verifying before the
   enclosing transaction touches the table, skipping the ALTER on fresh
   databases, and capping lock waits at 4s.

---

## Limitations

- The receipt is issued by the server and replayed by the client. A broker
  client could in principle replay a stale receipt; every field is validated
  and bounded server-side, and the sent-side digest is always recomputed from
  persisted draft rows, but the *claim* "this wording came from the model"
  rests on the client echo. Acceptable for a QA pilot; sign the receipt before
  treating it as a billing-grade metric.
- Only the per-item `label` and `instructions` are compared — those are what
  the customer reads. The `draft_text` preview is not persisted and not part
  of the signal.
- One office. One model. Three synthetic cases. No real broker behaviour yet.
