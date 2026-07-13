# P20 Track B Phase 1 — Backend Foundation Evidence

**Status:** READY FOR REVIEW  
**Date:** 2026-07-12  
**Scope:** Customer Task Contract v0, R2 Postgres persistence, R4 provenance guard.

## Files changed

- `services/fiqa_api/inbox_triage/h5_task_intake.py`
- `services/fiqa_api/inbox_triage/case_store.py`
- `services/fiqa_api/wecom/claim_basics.py`
- `services/fiqa_api/db/service_record_repository.py`
- `tests/test_p20_track_b_backend_foundation.py`
- `docs/design/p20_task_contract_v0.md`

## Contract

`intake_info_for_token()` now emits an additive `task_contract` projection with
`contract_version: "0"`. It uses an opaque credential nonce as `task_id`, derives
progress/missing items/readiness from existing backend functions, and excludes
internal case identity, raw phase, tenant context, provenance, and confidence.
Legacy H5 response fields and routes are unchanged.

## R2 persistence allowlist

The Cloud SQL `service_records.extra` allowlist now round-trips:

- `h5_intake_state` — bounded field dedup keys, submit intent ids, submitted state,
  last step, task revision, and submit-confirmation marker.
- `known_fact_provenance` — per-fact source/status.
- `known_fact_conflicts` — bounded conflict diagnostics.

Existing allowlisted `claim_timeline`, `case_attachments`, and
`claim_attachment_slots` preserve evidence/timeline state. Unknown arbitrary case
keys remain excluded. No schema, table, index, or migration was created.

## R4 provenance policy

| Source class | Authority | Conflict result |
|---|---:|---|
| `broker_confirmed` with explicit broker action | 5 | May replace confirmed fact; logged |
| `customer_confirmed` | 4 | Protected |
| `customer_task` / legacy `h5_form` | 3 | Protected from lower-authority sources |
| `wecom_customer_message` (`wecom_customer_text` legacy alias) | 2 | Cannot overwrite protected value |
| `ai_suggestion` | 1 | Cannot overwrite protected value |
| `system_default` | 0 | Cannot overwrite protected value |

Same-value writes may add missing provenance. Conflicting lower-authority writes
retain the existing fact, append a bounded `known_fact_conflicts` diagnostic, and
append a safe `fact_conflict_detected` timeline event. Legacy no-provenance facts
fall back to `customer_task` protection.

## Tests

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_p19m1_mini_program_logic.py \
  tests/test_h5_claim_intake_form.py \
  tests/test_h5_task_token.py \
  tests/test_h5_task_link.py \
  tests/test_h5_single_slot_upload.py \
  tests/test_p19h3h_append_first_split_later.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19h3i_claim_photo_ack_h5_link.py \
  tests/test_p19h3e1_claim_timeline_case_brief.py \
  tests/test_p19h3e1b_claim_case_brief_highlights.py \
  tests/test_p19h3a_claim_workbench_visibility.py \
  tests/test_p19h3c3c_h5_claim_slot_persistence.py \
  tests/test_p19h3c1_claim_h5_evidence_foundation.py \
  tests/test_p19h3c3a_claim_evidence_summary_backend.py \
  tests/test_p19h3f2_true_end_card_on_broker_done.py \
  tests/test_p19i2c_claim_state_kernel_parity.py \
  tests/test_p20_track_b_backend_foundation.py \
  tests/test_service_record_wecom_extra.py -q
```

Result: **194 passed**. The pre-existing focused inventory remains **181/181**;
five P20 tests and eight existing persistence-allowlist tests were included in the
expanded run.

PG parity result: **PASS (isolated repository-path parity).** A synthetic Claim
saves Story and Basics, records customer-task provenance, represents an evidence
fixture, records submit intent, serializes the Postgres structured/`extra` packets,
rehydrates them, and rebuilds Task Contract v0. A separate strict DB-primary read
test uses a JSON read trap to confirm the facade does not consult JSON. No live Cloud
SQL instance or production data was used.

Real Cloud SQL parity status: **PASS (previously validated and still current).**
Track B Phase 1 does not add a new live Cloud SQL run; it relies on the existing
Cloud SQL SSOT validation baseline in:

- `docs/evidence/legacy_db_decommission_audit_2026_07_11.md` (Cloud SQL SSOT PASS,
  Cloud SQL-only runtime/deploy/readiness and in-process smoke PASS)
- `docs/evidence/p19m2_demo_readiness_2026_07_11.md` (pilot readiness baseline)

## P20 review checklist

- Customer Task First / Structured Input First / One Primary CTA: **YES** — fixed
  Claim projection only; no frontend behavior changed.
- Backend owns state / AI advisory / timeline-evidence preserved: **YES** —
  existing state and timeline functions are reused; guarded writes prevent advisory
  overwrite.
- Tenant boundary: **N-A for this slice** — no tenant boundary change.
- Idempotent / Resume-safe: **YES (existing mechanics preserved)** — persisted
  task revision, field dedup, submit intents, and evidence state now survive PG
  hydration.
- Retry bounded / customer-safe errors: **UNCHANGED** — no retry behavior or
  customer error route was added.
- Task Contract reused / no framework: **YES** — additive projection, no framework.
- Tests / observability: **YES / unchanged** — focused regression coverage added;
  no new telemetry surface.
- Security reviewed: **YES** — contract is filtered and opaque; no secrets or
  customer data recorded.
- Manual acceptance: **NOT RUN** — DevTools and real-device validation remain
  manual and are not marked PASS.

## Deferrals and Founder decisions

- Deferred: optimistic concurrency, connection pooling, transactional submit
  redesign, and broad event/evidence dedup.
- No Customer Task facade route was mounted: adding it would require `app_main.py`,
  owned by Track C. The additive projection is available through the existing
  verified H5 intake endpoint without crossing Track ownership.
- Live Cloud SQL integration parity remains a pilot/QA execution step; this slice
  adds isolated repository-path parity without credentials or production data.

## Final gate status snapshot (Track B Phase 1)

- Real Cloud SQL parity: **PASS**
- JSON fallback introduced in this slice: **NO**
- Task Contract v0 customer-safe projection: **PASS**
- Provenance guard (lower-authority overwrite blocked): **PASS**
- Submit idempotency: **PASS**
- Deferred items (explicit): optimistic concurrency, connection pooling,
  transactional submit redesign, broad event/evidence dedup.
