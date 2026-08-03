# Case Value Metrics Semantics (V1)

**Status:** Stage 2 measurement foundation  
**Branch:** `stage2/real-usage-timing-instrumentation`  
**Scope:** Trustworthy business timing for pilot evidence. No dashboard. No LangGraph.

Governing principles:

- Page-open time is **not** active working time.
- Missing data stays blank; never fabricate.
- Business workflow events (formal submit, Request More, supplement, review, office accept) remain authoritative and unchanged.
- New open / first-action / broker-first-open markers are **observational telemetry** with durable first-wins timestamps.

---

## Audit baseline (pre-instrumentation)

| Fact | Status before this slice |
|------|--------------------------|
| Invite redeemed / customer context resolved | Observable in demo-invite + context APIs; **no case-scoped first-open timestamp** |
| Customer first meaningful action | Partially implied by Timeline / Cap2 commands; **no durable first-action stamp** |
| Formal claim submission | **Authoritative** — `formal_submitted_at` |
| Policy-context confirmation | **Authoritative** — Timeline `customer_policy_context_confirmed` + `policy_context` |
| First Request More | **Authoritative** — `broker_request_more_created` / open_request.created_at |
| Customer supplement submission | **Authoritative** — `supplement_submitted` / item response |
| Broker supplement acknowledgement | **Authoritative** — `broker_supplement_reviewed` |
| Broker first case open | **Missing** — exporter already marked `unsupported:broker_first_open_not_recorded` |
| Office-material acceptance | **Authoritative** — `office_materials_accepted_at` |

Misleading prior proxy: `customer_started_at` ≈ `created_at`, and when formal submit equals create, pre-submit dwell is not separately recorded.

---

## Event store contract

**Store:** `case_activity_events` (dedicated; not customer Timeline)

Required properties per event:

| Property | Rule |
|----------|------|
| `case_id` | Required |
| `event_type` | See catalog below |
| `actor_role` | `customer` \| `broker` \| `system` |
| `created_at` | **Server** clock (UTC ISO-8601) |
| `source_surface` | e.g. `mini_program`, `h5_intake`, `broker_workbench` |
| `schema_version` | Integer; V1 = `1` |
| `idempotency_key` | Stable; first-wins types use `{case_id}:{event_type}` |
| `session_id_hash` | Optional SHA-256 prefix of opaque session id (non-PII) |

**Never stored:** accident text, customer messages, raw tokens, sensitive PII, browser fingerprints.

---

## Metric catalog

### 1. `customer_intake_opened_at`

| Item | Definition |
|------|------------|
| **Exact definition** | First successful customer intake render / context resolution **for an existing case_id**. Observed session open — **not** guaranteed active work. |
| **Source** | `case_activity_events.event_type = customer_intake_opened` (also denormalized on case extra) |
| **Server timestamp** | Insert time on first successful record |
| **Idempotency** | One row per case; key `{case_id}:customer_intake_opened`. Refresh / reopen / replay do not reset. |
| **Known limitations** | Cannot be stamped before a case exists (cold Start Claim form with no case yet). Not wall-clock of typing. |
| **Class** | Observational telemetry |

### 2. `customer_first_action_at`

| Item | Definition |
|------|------------|
| **Exact definition** | First durable meaningful customer command: policy confirmation, story/field save, attachment / request-item submit, formal intake submit, or Start Claim with non-empty intake mutation / policy choice. |
| **Source** | `case_activity_events.event_type = customer_first_action` |
| **Server timestamp** | Insert time on first qualifying command success |
| **Idempotency** | One row per case; key `{case_id}:customer_first_action` |
| **Known limitations** | Does not measure thinking time. Passive browsing never stamps. Same HTTP request may also stamp intake_opened (opened first, then action). |
| **Class** | Observational telemetry of a business mutation boundary |

### 3. `formal_submitted_at`

| Item | Definition |
|------|------------|
| **Exact definition** | Existing formal claim submission business stamp. |
| **Source** | Case field `formal_submitted_at` (unchanged) |
| **Server timestamp** | Existing Cap2 / case_store write path |
| **Idempotency** | Immutable once set (existing precedent) |
| **Known limitations** | Legacy backfill may equal `created_at` |
| **Class** | **Business fact** |

### 4. `policy_context_confirmed_at`

| Item | Definition |
|------|------------|
| **Exact definition** | First Timeline / confirm event `customer_policy_context_confirmed`. |
| **Source** | `claim_timeline` / confirm command |
| **Server timestamp** | Event `created_at` |
| **Idempotency** | Confirm command idempotency (existing) |
| **Known limitations** | Only for known-customer confirm path |
| **Class** | **Business fact** |

### 5. `broker_first_opened_at`

| Item | Definition |
|------|------------|
| **Exact definition** | First successful Broker Workbench case-detail / Brief **render**, stamped by dedicated `POST /api/inbox/cases/{case_id}/activity/broker-first-opened` after the UI loads detail successfully. |
| **Source** | `case_activity_events.event_type = broker_first_opened` |
| **Server timestamp** | Insert time on first successful activity POST |
| **Idempotency** | One row per case; key `{case_id}:broker_first_opened`. Refresh / reopen / replay do not reset. |
| **Known limitations** | List-only glance without detail render is not counted. Generic `GET /cases/{id}`, metrics export, and support scripts must **not** create this event. Not “time broker spent reading.” |
| **Class** | Observational telemetry |

### 6. `first_request_more_at` / `request_more_loops`

| Item | Definition |
|------|------------|
| **Exact definition** | First / count of `broker_request_more_created` (fallback: open_request.created_at) |
| **Source** | Slice1 events / projection (unchanged) |
| **Class** | **Business fact** |

### 7. `supplement_submitted_at`

| Item | Definition |
|------|------------|
| **Exact definition** | First `supplement_submitted` (fallback: item customer_response.submitted_at) |
| **Class** | **Business fact** |

### 8. `broker_supplement_reviewed_at`

| Item | Definition |
|------|------------|
| **Exact definition** | First `broker_supplement_reviewed` |
| **Class** | **Business fact** |

### 9. `office_materials_accepted_at`

| Item | Definition |
|------|------------|
| **Exact definition** | Case field stamped by office-materials accept command |
| **Class** | **Business fact** |

---

## Derived metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| `intake_open_to_submit_sec` | `formal_submitted_at − customer_intake_opened_at` | Blank if either missing. Not active work time. |
| `first_action_to_submit_sec` | `formal_submitted_at − customer_first_action_at` | Blank if either missing. |
| `submit_to_broker_first_open_sec` | `broker_first_opened_at − formal_submitted_at` | Blank if either missing. |
| `request_more_to_supplement_sec` | `supplement_submitted_at − first_request_more_at` | Existing turnaround. |
| `supplement_to_broker_review_sec` | `broker_supplement_reviewed_at − supplement_submitted_at` | |
| `first_action_to_office_accept_sec` | `office_materials_accepted_at − customer_first_action_at` | Prefer first_action; blank if missing. |
| `request_more_loops` | Count of distinct Request More create events | |

### Backward-compatible aliases (legacy export columns)

Still emitted for older consumers:

- `customer_started_at` → `created_at` (legacy; prefer `customer_intake_opened_at`)
- `time_to_formal_submit_sec` → `created_at` → formal (legacy proxy)
- `supplement_turnaround_sec` → alias of `request_more_to_supplement_sec`
- `time_to_office_accept_sec` → `created_at` → office accept (legacy proxy)

---

## Data quality notes vocabulary

| Note | Meaning |
|------|---------|
| `missing:<field>` | Field blank; not inferred |
| `unsupported:<reason>` | Metric not available in this product shape |
| `note:formal_submitted_at_equals_created_at` | Pre-submit dwell not separately recorded on that case |
| `note:observational_open_not_active_work` | Open timestamps are session observations |
| `qa_or_artificial_timing` | Case tagged test/demo/harness — not pilot traffic |

Never claim statistical significance for small QA samples.
