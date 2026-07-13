# P20 Customer Task Contract v0

**Status:** Track B Phase 1 interface SSOT  
**Scope:** Claim Intake only; concrete descriptor, not a generic form engine.

## Customer-safe payload

```json
{
  "contract_version": "0",
  "task_id": "opaque-token-nonce",
  "task_type": "claim_intake",
  "task_status": "collecting",
  "title": "我的事故资料",
  "instruction": "继续填写",
  "progress": {"completed": 2, "total": 4},
  "sections": [{"key": "story", "label": "事故经过", "component_type": "long_text", "required": true, "status": "received"}],
  "fields": {"accident_description": "我停在红灯前，后车追尾。"},
  "missing_items": [{"key": "customer_damage_photo", "label": "车损照片"}],
  "evidence_requirements": [{"slot": "customer_damage_photo", "label": "车损照片", "min": 1, "received": 0}],
  "next_action": {"type": "go_to_section", "target": "time_location", "label": "继续填写资料"},
  "review_ready": false,
  "submit_ready": false,
  "revision": 2,
  "timestamps": {"updated_at": "2026-07-12T00:00:00Z"},
  "capabilities": {"voice": false, "scan": false},
  "branding": {"office_name": "陈总办公室", "safety_copy": "此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。"},
  "error": null
}
```

The payload MUST NOT contain internal `case_id`, tenant identity, raw claim phase,
provenance/confidence, workflow lanes, split/merge state, liability, or coverage
concepts.

## Semantics and ownership

| Field | Meaning | Authority |
|---|---|---|
| `task_id` | Opaque task handle derived from the verified task credential, never the case id | server |
| `task_status` | Customer-safe projection: `collecting`, `review_ready`, or `submitted` | derived |
| `progress`, `missing_items`, `next_action` | Current workflow projection | derived from persisted case + state machine |
| `sections`, `evidence_requirements` | Fixed Claim descriptor supported by the current client | server configuration |
| `fields` | Allowlisted Claim facts with customer-task confirmation provenance | persisted facts |
| `review_ready`, `submit_ready` | Existing H5 review/submit gates; submit is false after submission | server |
| `revision` | Monotonic task-state revision incremented by H5 field save and submit | persisted task state |
| `timestamps` | Safe update timestamp only | server |
| `error` | Null on success; failures use the safe envelope below | server |

`fields` is intentionally not an arbitrary case dictionary. It is an allowlist of
the Claim form's structured inputs. The existing legacy intake response remains
unchanged; this descriptor is emitted additively as `task_contract` by
`intake_info_for_token()`.

## Internal binding

The server binds task → internal case, tenant/configuration context, workflow
projection, facts → provenance, and actor/correlation context. This binding is
never serialized into the customer task contract. The current Claim implementation
can map one active task to one Case, but task and case remain different concepts;
no task table is created in this phase.

## Error envelope

The projection itself returns `error: null` on success. Customer-task endpoints
must map failures to a customer-safe envelope:

```json
{"error": {"code": "task_unavailable", "message": "暂时无法打开资料，请稍后重试或联系办公室。"}}
```

Internal diagnostic codes, token details, identifiers, and stack traces are never
included. The legacy H5 endpoint retains its existing error behavior for backward
compatibility.

## Versioning and compatibility

- `contract_version` is `"0"`.
- Additive optional fields are permitted without a version change.
- Removing/renaming fields or changing their meaning requires explicit version
  review.
- Reusing existing component types normally avoids a Mini Program release; a new
  component or interaction type may require one.
- This is Claim-specific and does not introduce a generic form/schema engine.

## Persistence allowlist

Cloud SQL `service_records.extra` persists only the bounded fields needed for
resume and trust: `h5_intake_state` (step, bounded field-dedup keys, bounded submit
intent ids, submission marker, task revision), `known_fact_provenance`, and bounded
`known_fact_conflicts`. Existing allowlisted evidence attachments/slots and
`claim_timeline` remain authoritative for evidence and audit history. Unknown
case-dictionary keys are not promoted into Postgres JSONB.

## Provenance precedence

Highest to lowest: `broker_confirmed` (only with explicit logged broker action),
`customer_confirmed`, `customer_task` / legacy `h5_form`,
`wecom_customer_message`, `ai_suggestion`, `system_default`.

The existing Workbench display name `wecom_customer_text` is retained as a
backward-compatible alias of `wecom_customer_message`.

Same-value writes may enrich missing provenance. A lower-authority conflicting
write preserves the existing fact, appends a bounded conflict diagnostic and a safe
timeline event, and does not expose provenance to the customer. Legacy facts with
no provenance are treated as `customer_task` for conflict protection.
