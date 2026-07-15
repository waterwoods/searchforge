# P20 Slice 1 QA Claim Enablement Evidence

**Date:** 2026-07-15  
**Case:** `case_874d750b5d5f`  
**Environment:** founder/QA shared pilot (`caseiq` on `caseiq-pilot-pg`)

## Original values

```json
{
  "claim_phase": "intake_ready_for_broker",
  "slice1_capability_version": null,
  "extra_keys": [
    "broker_confirmed_at",
    "case_attachments",
    "case_notes",
    "claim_attachment_slots",
    "claim_timeline",
    "conflict_state",
    "evidence_events",
    "formal_submitted_at",
    "guided_workflow_state",
    "h5_intake_state",
    "known_fact_provenance",
    "merge_review_required",
    "wecom_external_userid",
    "wecom_open_kf_id",
    "workbench_archived",
    "workbench_test"
  ],
  "payload_keys": [
    "additional_vehicle_count_hint",
    "additional_vehicle_mentioned",
    "broker_next_step",
    "case_creation_suggested",
    "claim_phase",
    "client_prep",
    "client_reply_draft",
    "collected_fields",
    "conversation_summary",
    "handoff_ready",
    "human_confirmation_fields",
    "human_confirmation_required",
    "identity_binding_state",
    "issue_category",
    "known_facts",
    "lifecycle_status",
    "manual_followup_needed",
    "person_link_confidence",
    "person_link_key",
    "person_link_source",
    "primary_vehicle_summary",
    "quote_ready_status",
    "service_lane",
    "service_type",
    "triage_mode",
    "urgency",
    "vehicle_key"
  ]
}
```

## Pre-check snapshot

```json
{
  "record_id": "case_874d750b5d5f",
  "service_lane": "claim",
  "claim_phase": "intake_ready_for_broker",
  "guided_workflow_state": "ready_for_broker_review",
  "workbench_test": "true",
  "workbench_archived": "false",
  "slice1_capability_version": null,
  "broker_done": "",
  "case_status": "new",
  "lifecycle_status": "handed_off"
}
```

## Enabled state

- `extra.slice1_capability_version = 1`
- `structured_payload.claim_phase = broker_review`
- Affected rows: service_records=1, structured_record_data=1

## Rollback SQL

```sql
BEGIN;

UPDATE service_records
SET extra = COALESCE(extra, '{}'::jsonb) - 'slice1_capability_version',
    updated_at = NOW()
WHERE record_id = 'case_874d750b5d5f';

UPDATE structured_record_data
SET structured_payload = jsonb_set(
      COALESCE(structured_payload, '{}'::jsonb),
      '{claim_phase}',
      '"intake_ready_for_broker"'::jsonb,
      true
    ),
    updated_at = NOW()
WHERE record_id = 'case_874d750b5d5f';

COMMIT;

```

## Notes

- Do not DROP Slice 1 companion tables after accepted commands.
- Open Request More already created during automated smoke; customer continue starts at manual step B unless rolled back via product path.
